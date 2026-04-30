"""
Download full India OpenStreetMap road network data.
This script downloads the complete road network for India using OSMnx.

Note: This will download a very large dataset (millions of nodes).
It may take several hours and require significant disk space (10+ GB).

Usage:
    python download_india_osm.py
"""

import os
import sys
import time
import json
from math import radians, sin, cos, sqrt, atan2

try:
    import osmnx as ox
    import pandas as pd
    import networkx as nx
except ImportError:
    print("ERROR: Required packages missing. Install with:")
    print("  pip install osmnx pandas networkx")
    sys.exit(1)

# Configuration
OUTPUT_DIR = "data/india_osm"
OUT_NODES = os.path.join(OUTPUT_DIR, "india_nodes.csv")
OUT_GRAPH = os.path.join(OUTPUT_DIR, "india_graph.csv")
OUT_GEOM = os.path.join(OUTPUT_DIR, "edges_geom.json")
MAX_RETRIES = 5
BASE_DELAY = 3.0
BATCH_SIZE = 10000  # Process edges in batches to avoid memory issues

# India bounding box (approximate)
INDIA_BBOX = {
    'north': 37.0,  # Northernmost point
    'south': 6.0,   # Southernmost point
    'east': 97.0,   # Easternmost point
    'west': 68.0    # Westernmost point
}

def haversine_m(lat1, lon1, lat2, lon2):
    """Calculate distance in meters using Haversine formula"""
    R = 6371000.0
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    dphi = radians(lat2 - lat1)
    dl = radians(lon2 - lon1)
    a = sin(dphi/2.0)**2 + cos(phi1)*cos(phi2)*(sin(dl/2.0)**2)
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def download_india_graph():
    """
    Download India road network using bounding box.
    This is a large download and may take hours.
    """
    print("=" * 60)
    print("Downloading India OpenStreetMap Road Network")
    print("=" * 60)
    print(f"Bounding Box: {INDIA_BBOX}")
    print("This will download a VERY LARGE dataset (millions of nodes).")
    print("Estimated time: 2-6 hours depending on connection speed.")
    print("Estimated size: 10-50 GB")
    print("=" * 60)
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Aborted.")
        return None
    
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            print(f"\n[Attempt {attempt+1}/{MAX_RETRIES}] Downloading India road network...")
            print("This may take several hours. Please be patient...")
            
            # Download using bounding box
            # Note: This downloads ALL roads in India - very large!
            G = ox.graph_from_bbox(
                north=INDIA_BBOX['north'],
                south=INDIA_BBOX['south'],
                east=INDIA_BBOX['east'],
                west=INDIA_BBOX['west'],
                network_type='drive',  # Road network for ground vehicles
                simplify=True
            )
            
            print(f"Downloaded graph with {len(G.nodes())} nodes and {len(G.edges())} edges")
            return G
            
        except Exception as e:
            attempt += 1
            wait = BASE_DELAY * (2 ** (attempt - 1))
            print(f"[ERROR] Attempt {attempt} failed: {type(e).__name__}: {e}")
            if attempt < MAX_RETRIES:
                print(f"Retrying in {wait:.0f} seconds...")
                time.sleep(wait)
            else:
                print("\nFailed to download after all retries.")
                print("\nAlternative: Download India OSM PBF file manually:")
                print("1. Go to https://download.geofabrik.de/asia/india.html")
                print("2. Download india-latest.osm.pbf")
                print("3. Use osmnx.graph_from_xml() to load it")
                return None
    
    return None

def download_india_by_states():
    """
    Alternative: Download India by major states/cities to reduce load.
    This is more manageable but may miss some rural areas.
    """
    print("=" * 60)
    print("Downloading India Road Network by Major Regions")
    print("=" * 60)
    print("This approach downloads major cities/states separately.")
    print("More manageable but may miss some rural connections.")
    print("=" * 60)
    
    # Major Indian cities/regions
    regions = [
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
    
    all_graphs = []
    
    for i, region in enumerate(regions, 1):
        print(f"\n[{i}/{len(regions)}] Downloading {region}...")
        attempt = 0
        while attempt < MAX_RETRIES:
            try:
                G = ox.graph_from_place(region, network_type='drive', simplify=True)
                print(f"  ✓ Downloaded {len(G.nodes())} nodes, {len(G.edges())} edges")
                all_graphs.append(G)
                time.sleep(2)  # Be nice to OSM servers
                break
            except Exception as e:
                attempt += 1
                if attempt < MAX_RETRIES:
                    print(f"  ⚠ Retry {attempt}/{MAX_RETRIES}...")
                    time.sleep(BASE_DELAY)
                else:
                    print(f"  ✗ Failed: {e}")
        
        # Combine graphs periodically to save memory
        if len(all_graphs) >= 5:
            print("  Combining graphs...")
            combined = nx.compose_all(all_graphs)
            all_graphs = [combined]
    
    if all_graphs:
        print("\nCombining all regional graphs...")
        final_graph = nx.compose_all(all_graphs)
        print(f"Final graph: {len(final_graph.nodes())} nodes, {len(final_graph.edges())} edges")
        return final_graph
    
    return None

def build_assets(G):
    """Convert NetworkX graph to CSV files"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("\n[build] Converting nodes...")
    nodes_gdf, edges_gdf = ox.graph_to_gdfs(G, nodes=True, edges=True)
    nodes_gdf = nodes_gdf.reset_index()
    
    # Create nodes CSV
    node_rows = []
    for _, row in nodes_gdf.iterrows():
        nid = row.get('osmid')
        if isinstance(nid, (list, tuple, set)):
            nid = list(nid)[0]
        lat = row.get('y') if 'y' in row else row.get('lat', None)
        lon = row.get('x') if 'x' in row else row.get('lon', None)
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
    print(f"[build] Wrote {OUT_NODES} ({len(df_nodes)} rows)")
    
    # Create node lookup for distance calculation
    node_lookup = {r['node_id']: (r['lat'], r['lon']) for r in node_rows}
    
    # Process edges
    print("[build] Processing edges...")
    geom_map = {}
    edge_rows = []
    key_counter = 0
    
    for u, v, key, data in G.edges(keys=True, data=True):
        if u not in node_lookup or v not in node_lookup:
            continue
        
        lat1, lon1 = node_lookup[u]
        lat2, lon2 = node_lookup[v]
        distance_km = haversine_m(lat1, lon1, lat2, lon2) / 1000.0
        
        # Safety score (placeholder - can be enhanced with road type data)
        safety = 70.0  # Default
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
            elif 'residential' in hw_type or 'unclassified' in hw_type:
                safety = 60.0
        
        edge_rows.append({
            'u': int(u),
            'v': int(v),
            'distance_km': distance_km,
            'safety_score': int(safety),
            'key': key_counter
        })
        
        # Store geometry if available
        if 'geometry' in data:
            geom = data['geometry']
            if hasattr(geom, 'coords'):
                coords = list(geom.coords)
                geom_map[f"{u}_{v}_{key_counter}"] = [[lat, lon] for lon, lat in coords]
        
        key_counter += 1
        
        # Progress indicator
        if key_counter % 10000 == 0:
            print(f"  Processed {key_counter} edges...")
    
    # Write edges CSV
    df_edges = pd.DataFrame(edge_rows)
    df_edges.to_csv(OUT_GRAPH, index=False)
    print(f"[build] Wrote {OUT_GRAPH} ({len(df_edges)} rows)")
    
    # Write geometry JSON
    if geom_map:
        with open(OUT_GEOM, 'w') as f:
            json.dump(geom_map, f)
        print(f"[build] Wrote {OUT_GEOM}")
    
    print("\n[build] Complete!")
    print(f"  Nodes: {len(df_nodes)}")
    print(f"  Edges: {len(df_edges)}")
    print(f"  Output directory: {OUTPUT_DIR}")

def main():
    print("India OSM Road Network Downloader")
    print("=" * 60)
    print("\nChoose download method:")
    print("1. Full India (VERY LARGE - 10-50 GB, 2-6 hours)")
    print("2. Major Cities/Regions (More manageable, faster)")
    print("3. Exit")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == '1':
        G = download_india_graph()
    elif choice == '2':
        G = download_india_by_states()
    else:
        print("Exiting.")
        return
    
    if G is None:
        print("\nFailed to download graph.")
        return
    
    print(f"\nGraph downloaded successfully!")
    print(f"  Nodes: {len(G.nodes())}")
    print(f"  Edges: {len(G.edges())}")
    
    build_assets(G)

if __name__ == '__main__':
    main()

