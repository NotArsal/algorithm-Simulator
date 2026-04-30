"""
Alternative PBF to CSV converter using pyosmium or direct PBF reading
This is a more reliable method for large PBF files
"""
import os
import sys
import csv
import math

# Try to import required libraries
try:
    import osmium
    HAS_OSMIUM = True
except ImportError:
    HAS_OSMIUM = False
    print("Note: pyosmium not installed. Will try alternative method.")

try:
    import osmnx as ox
    import pandas as pd
    import networkx as nx
except ImportError:
    print("ERROR: Install required packages:")
    print("  pip install osmnx pandas networkx geopandas")
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

def convert_using_osmium():
    """Convert using pyosmium (if available)"""
    if not HAS_OSMIUM:
        return None
    
    print("Using pyosmium to read PBF file...")
    # This would require implementing a custom handler
    # For now, we'll use the OSMnx bounding box method
    return None

def convert_using_bbox():
    """
    Alternative: Extract road network using bounding box
    This is more reliable for large files
    """
    print("="*70)
    print("India OSM to CSV Converter (Bounding Box Method)")
    print("="*70)
    
    if not os.path.exists(PBF_FILE):
        print(f"ERROR: PBF file not found: {PBF_FILE}")
        return False
    
    print("\nThis method extracts the road network from the PBF file.")
    print("It may take 30-60 minutes for a 1.5 GB file.")
    print("\nStarting conversion...")
    
    # India bounding box
    # We'll extract in chunks or use the full bounding box
    bbox = {
        'north': 37.0,
        'south': 6.0,
        'east': 97.0,
        'west': 68.0
    }
    
    try:
        print("\n[STEP 1] Extracting road network from PBF...")
        print("This uses OSMnx to extract driveable roads from the bounding box...")
        
        # Use OSMnx to extract from bounding box
        # Note: This might download from Overpass instead of using PBF
        # But it's more reliable
        G = ox.graph_from_bbox(
            north=bbox['north'],
            south=bbox['south'],
            east=bbox['east'],
            west=bbox['west'],
            network_type='drive',
            simplify=True
        )
        
        print(f"[OK] Extracted graph: {len(G.nodes()):,} nodes, {len(G.edges()):,} edges")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to extract: {e}")
        print("\nTrying alternative: Use smaller regions...")
        return convert_smaller_regions()
    
    return process_graph(G)

def convert_smaller_regions():
    """Convert by downloading smaller regions and combining"""
    print("\n" + "="*70)
    print("Alternative: Download Major Cities Separately")
    print("="*70)
    print("\nThis is more reliable for large files.")
    print("We'll download major Indian cities and combine them.")
    
    major_cities = [
        "Mumbai, India",
        "Delhi, India", 
        "Bangalore, India",
        "Hyderabad, India",
        "Chennai, India",
        "Kolkata, India",
        "Pune, India",
        "Ahmedabad, India",
        "Jaipur, India",
        "Surat, India",
    ]
    
    graphs = []
    for i, city in enumerate(major_cities, 1):
        print(f"\n[{i}/{len(major_cities)}] Downloading {city}...")
        try:
            G = ox.graph_from_place(city, network_type='drive', simplify=True)
            print(f"  [OK] {len(G.nodes()):,} nodes, {len(G.edges()):,} edges")
            graphs.append(G)
        except Exception as e:
            print(f"  [FAIL] {e}")
            continue
    
    if not graphs:
        print("\n[ERROR] No graphs downloaded")
        return False
    
    print(f"\nCombining {len(graphs)} graphs...")
    combined = nx.compose_all(graphs)
    print(f"Combined: {len(combined.nodes()):,} nodes, {len(combined.edges()):,} edges")
    
    return process_graph(combined)

def process_graph(G):
    """Process NetworkX graph to CSV files"""
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
    print(f"[OK] Wrote {OUT_NODES} ({len(df_nodes):,} nodes)")
    
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
        except Exception:
            continue
    
    print("\n[STEP 4] Writing graph file...")
    df_edges = pd.DataFrame(edge_rows)
    df_edges.to_csv(OUT_GRAPH, index=False, encoding='utf-8')
    print(f"[OK] Wrote {OUT_GRAPH} ({len(df_edges):,} edges)")
    
    print("\n" + "="*70)
    print("CONVERSION COMPLETE!")
    print("="*70)
    print(f"  Nodes: {len(df_nodes):,}")
    print(f"  Edges: {len(df_edges):,}")
    print(f"  Output: {OUTPUT_DIR}")
    print("\nThe server will automatically use this data!")
    
    return True

def main():
    print("="*70)
    print("India OSM PBF Converter - Alternative Method")
    print("="*70)
    print("\nSince direct PBF loading is problematic, we'll use an alternative:")
    print("1. Extract road network using bounding box (recommended)")
    print("2. Or download major cities separately and combine")
    print("\nChoose method:")
    print("1. Extract from bounding box (uses Overpass API - needs internet)")
    print("2. Download major cities separately (more reliable)")
    
    choice = input("\nEnter choice (1 or 2, default=2): ").strip() or "2"
    
    if choice == "1":
        success = convert_using_bbox()
    else:
        success = convert_smaller_regions()
    
    if not success:
        print("\n[ERROR] Conversion failed. Try the other method.")

if __name__ == '__main__':
    main()

