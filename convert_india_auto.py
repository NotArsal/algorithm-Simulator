"""
Automatic India OSM converter - downloads major cities and combines them
This is the most reliable method
"""
import os
import sys
import time
import math

try:
    import osmnx as ox
    import pandas as pd
    import networkx as nx
except ImportError:
    print("ERROR: Install required packages:")
    print("  pip install osmnx pandas networkx geopandas")
    sys.exit(1)

OUTPUT_DIR = "D:/navigation_india_osm"
OUT_NODES = os.path.join(OUTPUT_DIR, "india_nodes.csv")
OUT_GRAPH = os.path.join(OUTPUT_DIR, "india_graph.csv")

# Major Indian cities for comprehensive coverage
CITIES = [
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
]

def haversine_m(lat1, lon1, lat2, lon2):
    """Calculate distance in meters"""
    R = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def download_city(city_name, attempt=0):
    """Download road network for a city"""
    max_retries = 3
    if attempt >= max_retries:
        return None
    
    try:
        print(f"  Downloading {city_name}...", end=" ", flush=True)
        G = ox.graph_from_place(city_name, network_type='drive', simplify=True)
        nodes_count = len(G.nodes())
        edges_count = len(G.edges())
        print(f"[OK] {nodes_count:,} nodes, {edges_count:,} edges")
        return G
    except Exception as e:
        attempt += 1
        if attempt < max_retries:
            wait = 2 * (2 ** (attempt - 1))
            print(f"[RETRY {attempt}/{max_retries}] Waiting {wait}s...")
            time.sleep(wait)
            return download_city(city_name, attempt)
        else:
            print(f"[FAIL] {e}")
            return None

def process_graph(G):
    """Convert NetworkX graph to CSV files"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("\n[1/3] Converting nodes...")
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
        except:
            continue
    
    df_nodes = pd.DataFrame(node_rows)
    df_nodes.to_csv(OUT_NODES, index=False, encoding='utf-8')
    print(f"  [OK] Wrote {OUT_NODES} ({len(df_nodes):,} nodes)")
    
    node_lookup = {r['node_id']: (r['lat'], r['lon']) for r in node_rows}
    
    print("\n[2/3] Processing edges...")
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
            if key_counter % 50000 == 0:
                print(f"  Processed {key_counter:,} edges...")
        except:
            continue
    
    print("\n[3/3] Writing graph file...")
    df_edges = pd.DataFrame(edge_rows)
    df_edges.to_csv(OUT_GRAPH, index=False, encoding='utf-8')
    print(f"  [OK] Wrote {OUT_GRAPH} ({len(df_edges):,} edges)")
    
    print("\n" + "="*70)
    print("CONVERSION COMPLETE!")
    print("="*70)
    print(f"  Nodes: {len(df_nodes):,}")
    print(f"  Edges: {len(df_edges):,}")
    print(f"  Output: {OUTPUT_DIR}")
    print("\nThe server will automatically use this data!")

def main():
    print("="*70)
    print("India Road Network Downloader - Major Cities")
    print("="*70)
    print(f"Downloading road networks for {len(CITIES)} major Indian cities")
    print("This will take approximately 30-60 minutes.")
    print("="*70)
    print("\nStarting download...\n")
    
    graphs = []
    successful = 0
    failed = 0
    
    for i, city in enumerate(CITIES, 1):
        print(f"[{i}/{len(CITIES)}] ", end="")
        G = download_city(city)
        if G:
            graphs.append(G)
            successful += 1
        else:
            failed += 1
        
        # Combine periodically to save memory
        if len(graphs) >= 5:
            print("  Combining graphs to save memory...")
            combined = nx.compose_all(graphs)
            graphs = [combined]
        
        time.sleep(2)  # Be nice to OSM servers
    
    print(f"\nDownload Summary:")
    print(f"  Successful: {successful}/{len(CITIES)}")
    print(f"  Failed: {failed}/{len(CITIES)}")
    
    if not graphs:
        print("\n[ERROR] No graphs downloaded successfully.")
        return
    
    # Final combination
    print(f"\nCombining {len(graphs)} graphs...")
    final_graph = nx.compose_all(graphs)
    print(f"Final graph: {len(final_graph.nodes()):,} nodes, {len(final_graph.edges()):,} edges")
    
    # Process to CSV
    process_graph(final_graph)

if __name__ == '__main__':
    main()

