"""
Download India road network by major cities/regions.
This is a more manageable approach than downloading all of India at once.
"""

import os
import sys
import time
import json
import math

try:
    import osmnx as ox
    import pandas as pd
    import networkx as nx
except ImportError:
    print("ERROR: Required packages missing. Install with:")
    print("  pip install osmnx pandas networkx")
    sys.exit(1)

# Configuration
# Save to D: drive to save space on C: drive
OUTPUT_DIR = "D:/navigation_india_osm"
OUT_NODES = os.path.join(OUTPUT_DIR, "india_nodes.csv")
OUT_GRAPH = os.path.join(OUTPUT_DIR, "india_graph.csv")
OUT_GEOM = os.path.join(OUTPUT_DIR, "edges_geom.json")
MAX_RETRIES = 5
BASE_DELAY = 3.0

def haversine_m(lat1, lon1, lat2, lon2):
    """Calculate distance in meters"""
    R = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# Major Indian cities/regions for comprehensive coverage
REGIONS = [
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
    "Lucknow, India",
    "Kanpur, India",
    "Nagpur, India",
    "Indore, India",
    "Thane, India",
    "Bhopal, India",
    "Visakhapatnam, India",
    "Patna, India",
    "Vadodara, India",
    "Ghaziabad, India",
    "Ludhiana, India",
    "Agra, India",
    "Nashik, India",
    "Faridabad, India",
    "Meerut, India",
    "Rajkot, India",
    "Varanasi, India",
    "Srinagar, India",
    "Amritsar, India",
    "Chandigarh, India",
]

def download_region(region_name, attempt=0):
    """Download road network for a single region"""
    if attempt >= MAX_RETRIES:
        return None
    
    try:
        print(f"  Downloading {region_name}...", end=" ", flush=True)
        G = ox.graph_from_place(region_name, network_type='drive', simplify=True)
        nodes_count = len(G.nodes())
        edges_count = len(G.edges())
        print(f"[OK] {nodes_count:,} nodes, {edges_count:,} edges")
        return G
    except Exception as e:
        attempt += 1
        if attempt < MAX_RETRIES:
            wait = BASE_DELAY * (2 ** (attempt - 1))
            print(f"[FAIL] Attempt {attempt}/{MAX_RETRIES}, retrying in {wait:.0f}s...")
            time.sleep(wait)
            return download_region(region_name, attempt)
        else:
            print(f"[FAIL] After {MAX_RETRIES} attempts: {e}")
            return None

def combine_graphs(graphs):
    """Combine multiple graphs into one"""
    if not graphs:
        return None
    
    print(f"\nCombining {len(graphs)} regional graphs...")
    combined = nx.compose_all(graphs)
    print(f"Combined graph: {len(combined.nodes()):,} nodes, {len(combined.edges()):,} edges")
    return combined

def build_assets(G):
    """Convert NetworkX graph to CSV files"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("\n[1/3] Converting nodes to CSV...")
    nodes_gdf, edges_gdf = ox.graph_to_gdfs(G, nodes=True, edges=True)
    nodes_gdf = nodes_gdf.reset_index()
    
    node_rows = []
    for _, row in nodes_gdf.iterrows():
        nid = row.get('osmid')
        if isinstance(nid, (list, tuple, set)):
            nid = list(nid)[0]
        lat = row.get('y')
        lon = row.get('x')
        label = row.get('name', '') or ''
        
        if nid is None or lat is None or lon is None:
            continue
        
        node_rows.append({
            'node_id': int(nid),
            'lat': float(lat),
            'lon': float(lon),
            'label': label
        })
    
    df_nodes = pd.DataFrame(node_rows)
    df_nodes.to_csv(OUT_NODES, index=False)
    print(f"  [OK] Wrote {OUT_NODES} ({len(df_nodes):,} rows)")
    
    node_lookup = {r['node_id']: (r['lat'], r['lon']) for r in node_rows}
    
    print("\n[2/3] Processing edges...")
    geom_map = {}
    edge_rows = []
    key_counter = 0
    
    for u, v, key, data in G.edges(keys=True, data=True):
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
        
        if 'geometry' in data:
            geom = data['geometry']
            if hasattr(geom, 'coords'):
                coords = list(geom.coords)
                geom_map[f"{u_int}_{v_int}_{key_counter}"] = [[lat, lon] for lon, lat in coords]
        
        key_counter += 1
        if key_counter % 50000 == 0:
            print(f"  Processed {key_counter:,} edges...")
    
    print("\n[3/3] Writing files...")
    df_edges = pd.DataFrame(edge_rows)
    df_edges.to_csv(OUT_GRAPH, index=False)
    print(f"  [OK] Wrote {OUT_GRAPH} ({len(df_edges):,} rows)")
    
    if geom_map:
        with open(OUT_GEOM, 'w') as f:
            json.dump(geom_map, f)
        print(f"  [OK] Wrote {OUT_GEOM}")
    
    print("\n" + "="*60)
    print("DOWNLOAD COMPLETE!")
    print("="*60)
    print(f"  Nodes: {len(df_nodes):,}")
    print(f"  Edges: {len(df_edges):,}")
    print(f"  Output: {OUTPUT_DIR}")
    print("\nThe server will automatically use this data for ground bot routing.")

def main():
    print("="*60)
    print("India Road Network Downloader - Major Cities")
    print("="*60)
    print(f"Downloading road networks for {len(REGIONS)} major Indian cities/regions")
    print("This will take approximately 30-60 minutes depending on connection speed.")
    print("="*60)
    print("\nStarting download...\n")
    
    graphs = []
    successful = 0
    failed = 0
    
    for i, region in enumerate(REGIONS, 1):
        print(f"[{i}/{len(REGIONS)}] ", end="")
        G = download_region(region)
        if G:
            graphs.append(G)
            successful += 1
        else:
            failed += 1
        
        # Combine periodically to save memory
        if len(graphs) >= 5:
            print("  Combining graphs to save memory...")
            combined = combine_graphs(graphs)
            graphs = [combined] if combined else []
        
        time.sleep(2)  # Be nice to OSM servers
    
    print(f"\nDownload Summary:")
    print(f"  Successful: {successful}/{len(REGIONS)}")
    print(f"  Failed: {failed}/{len(REGIONS)}")
    
    if not graphs:
        print("\nERROR: No graphs downloaded successfully.")
        return
    
    # Final combination
    final_graph = combine_graphs(graphs)
    if final_graph:
        build_assets(final_graph)
    else:
        print("\nERROR: Failed to combine graphs.")

if __name__ == '__main__':
    main()

