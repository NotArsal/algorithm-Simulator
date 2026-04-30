"""
Convert OSM PBF file to CSV format for navigation system
"""
import os
import sys
import json
import math

try:
    import osmnx as ox
    import pandas as pd
    import networkx as nx
except ImportError:
    print("ERROR: Install required packages:")
    print("  pip install osmnx pandas networkx geopandas")
    sys.exit(1)

# Configuration - Your downloaded PBF file
PBF_FILE = "D:/navigation_india_osm/india-251108.osm.pbf"
OUTPUT_DIR = "D:/navigation_india_osm"
OUT_NODES = os.path.join(OUTPUT_DIR, "india_nodes.csv")
OUT_GRAPH = os.path.join(OUTPUT_DIR, "india_graph.csv")

def haversine_m(lat1, lon1, lat2, lon2):
    """Calculate distance in meters"""
    R = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def main():
    print("="*70)
    print("OSM PBF to CSV Converter")
    print("="*70)
    
    if not os.path.exists(PBF_FILE):
        print(f"\nERROR: PBF file not found: {PBF_FILE}")
        print("\nPlease:")
        print("1. Download india-latest.osm.pbf from:")
        print("   https://download.geofabrik.de/asia/india.html")
        print(f"2. Save it to: {PBF_FILE}")
        print("   OR edit this script and change PBF_FILE variable")
        print("3. Run this script again")
        return
    
    file_size_mb = os.path.getsize(PBF_FILE) / (1024 * 1024)
    print(f"\nPBF file found: {PBF_FILE}")
    print(f"File size: {file_size_mb:.2f} MB")
    print("\nLoading PBF file...")
    print("This may take 10-30 minutes depending on file size...")
    print("Please be patient...")
    
    try:
        # Load PBF file using OSMnx - use graph_from_file for PBF files
        print("\n[STEP 1] Loading OSM data from PBF...")
        print("This will take 10-30 minutes for a 1.5 GB file...")
        print("Please be patient - the file is being processed...")
        
        # OSMnx uses graph_from_file for PBF files, not graph_from_xml
        G = ox.graph_from_file(PBF_FILE, network_type='drive', simplify=True)
        print(f"[OK] Loaded graph: {len(G.nodes()):,} nodes, {len(G.edges()):,} edges")
    except Exception as e:
        print(f"\n[ERROR] Failed to load PBF: {e}")
        print(f"Error type: {type(e).__name__}")
        print("\nTroubleshooting:")
        print("1. Make sure osmnx is installed: pip install osmnx geopandas")
        print("2. The file might be too large - try a smaller region first")
        print("3. Check if the PBF file is corrupted or incomplete")
        print("4. You might need more RAM (1.5 GB file needs 4-8 GB RAM)")
        print("\nAlternative: Download a smaller region like Maharashtra")
        return
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("\n[STEP 2] Converting nodes to CSV...")
    nodes_gdf, edges_gdf = ox.graph_to_gdfs(G, nodes=True, edges=True)
    nodes_gdf = nodes_gdf.reset_index()
    
    node_rows = []
    for idx, row in nodes_gdf.iterrows():
        nid = row.get('osmid')
        if isinstance(nid, (list, tuple, set)):
            nid = list(nid)[0]
        lat = row.get('y')
        lon = row.get('x')
        label = row.get('name', '') or ''
        
        if nid is None or lat is None or lon is None:
            continue
        
        try:
            node_rows.append({
                'node_id': int(nid),
                'lat': float(lat),
                'lon': float(lon),
                'label': str(label) if label else ''
            })
        except (ValueError, TypeError):
            continue
        
        if len(node_rows) % 50000 == 0:
            print(f"  Processed {len(node_rows):,} nodes...")
    
    df_nodes = pd.DataFrame(node_rows)
    df_nodes.to_csv(OUT_NODES, index=False, encoding='utf-8')
    print(f"[OK] Wrote {OUT_NODES}")
    print(f"     Nodes: {len(df_nodes):,}")
    
    node_lookup = {r['node_id']: (r['lat'], r['lon']) for r in node_rows}
    
    print("\n[STEP 3] Processing edges...")
    edge_rows = []
    key_counter = 0
    
    for u, v, key, data in G.edges(keys=True, data=True):
        try:
            u_int = int(u) if not isinstance(u, (list, tuple)) else int(list(u)[0])
            v_int = int(v) if not isinstance(v, (list, tuple)) else int(list(v)[0])
            
            if u_int not in node_lookup or v_int not in node_lookup:
                continue
            
            lat1, lon1 = node_lookup[u_int]
            lat2, lon2 = node_lookup[v_int]
            distance_km = haversine_m(lat1, lon1, lat2, lon2) / 1000.0
            
            # Safety score based on road type
            safety = 70.0
            if 'highway' in data:
                hw_type = str(data['highway']).lower()
                if 'motorway' in hw_type or 'trunk' in hw_type:
                    safety = 85.0
                elif 'primary' in hw_type:
                    safety = 80.0
                elif 'secondary' in hw_type:
                    safety = 75.0
                elif 'tertiary' in hw_type:
                    safety = 70.0
                else:
                    safety = 60.0
            
            edge_rows.append({
                'u': u_int,
                'v': v_int,
                'distance_km': distance_km,
                'safety_score': int(safety),
                'key': key_counter
            })
            
            key_counter += 1
            if key_counter % 100000 == 0:
                print(f"  Processed {key_counter:,} edges...")
        except Exception as e:
            continue
    
    print("\n[STEP 4] Writing graph file...")
    df_edges = pd.DataFrame(edge_rows)
    df_edges.to_csv(OUT_GRAPH, index=False, encoding='utf-8')
    print(f"[OK] Wrote {OUT_GRAPH}")
    print(f"     Edges: {len(df_edges):,}")
    
    print("\n" + "="*70)
    print("CONVERSION COMPLETE!")
    print("="*70)
    print(f"  Nodes: {len(df_nodes):,}")
    print(f"  Edges: {len(df_edges):,}")
    print(f"  Output directory: {OUTPUT_DIR}")
    print("\nThe server will automatically use this data!")
    print("No restart needed - it checks on each request.")

if __name__ == '__main__':
    main()

