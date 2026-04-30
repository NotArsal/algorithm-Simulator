"""
Convert OSM PBF file to CSV using pyrosm (the correct library for PBF files)
"""
import os
import sys
import math

try:
    from pyrosm import OSM
    import networkx as nx
    import pandas as pd
    HAS_PYROSM = True
except ImportError:
    HAS_PYROSM = False
    print("ERROR: pyrosm not installed!")
    print("\nInstall it with:")
    print("  pip install pyrosm geopandas networkx pandas")
    print("\nThis is the correct library for reading PBF files.")
    sys.exit(1)

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
    print("OSM PBF to CSV Converter (using pyrosm)")
    print("="*70)
    
    if not os.path.exists(PBF_FILE):
        print(f"\nERROR: PBF file not found: {PBF_FILE}")
        return
    
    file_size_mb = os.path.getsize(PBF_FILE) / (1024 * 1024)
    print(f"\nPBF file: {PBF_FILE}")
    print(f"File size: {file_size_mb:.2f} MB ({file_size_mb/1024:.2f} GB)")
    print("\nThis will take 20-40 minutes for a 1.5 GB file...")
    print("Please be patient...")
    
    try:
        print("\n[STEP 1] Initializing OSM object from PBF...")
        osm = OSM(PBF_FILE)
        print("[OK] OSM object created")
        
        print("\n[STEP 2] Extracting road network...")
        print("This may take 10-20 minutes...")
        nodes, edges = osm.get_network(nodes=True, network_type="driving")
        print(f"[OK] Extracted network")
        print(f"     Nodes: {len(nodes):,}")
        print(f"     Edges: {len(edges):,}")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to extract network: {e}")
        print(f"Error type: {type(e).__name__}")
        print("\nTroubleshooting:")
        print("1. Make sure pyrosm is installed: pip install pyrosm")
        print("2. Check if the PBF file is complete and not corrupted")
        print("3. You might need more RAM (recommended: 8GB+)")
        return
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("\n[STEP 3] Converting nodes to CSV...")
    node_rows = []
    for idx, row in nodes.iterrows():
        try:
            nid = row.get('id') or row.get('node_id') or row.get('osmid')
            lat = row.get('lat') or row.get('y')
            lon = row.get('lon') or row.get('x')
            label = row.get('name', '') or ''
            
            if nid is None or lat is None or lon is None:
                continue
            
            node_rows.append({
                'node_id': int(nid),
                'lat': float(lat),
                'lon': float(lon),
                'label': str(label) if label else ''
            })
        except:
            continue
        
        if len(node_rows) % 50000 == 0:
            print(f"  Processed {len(node_rows):,} nodes...")
    
    df_nodes = pd.DataFrame(node_rows)
    df_nodes.to_csv(OUT_NODES, index=False, encoding='utf-8')
    print(f"[OK] Wrote {OUT_NODES} ({len(df_nodes):,} nodes)")
    
    # Create node lookup
    node_lookup = {r['node_id']: (r['lat'], r['lon']) for r in node_rows}
    
    print("\n[STEP 4] Processing edges...")
    edge_rows = []
    key_counter = 0
    
    for idx, row in edges.iterrows():
        try:
            u = row.get('u') or row.get('from') or row.get('source')
            v = row.get('v') or row.get('to') or row.get('target')
            
            if u is None or v is None:
                continue
            
            u_int = int(u)
            v_int = int(v)
            
            if u_int not in node_lookup or v_int not in node_lookup:
                continue
            
            lat1, lon1 = node_lookup[u_int]
            lat2, lon2 = node_lookup[v_int]
            distance_km = haversine_m(lat1, lon1, lat2, lon2) / 1000.0
            
            # Safety score based on road type
            safety = 70.0
            highway = row.get('highway', '')
            if highway:
                hw_type = str(highway).lower()
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
    
    print("\n[STEP 5] Writing graph file...")
    df_edges = pd.DataFrame(edge_rows)
    df_edges.to_csv(OUT_GRAPH, index=False, encoding='utf-8')
    print(f"[OK] Wrote {OUT_GRAPH} ({len(df_edges):,} edges)")
    
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

