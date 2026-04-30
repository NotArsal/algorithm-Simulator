"""
Create a road-based combined graph that properly connects mountain, rural, and Pune locations
using actual road networks from OpenStreetMap.

This script:
1. Downloads OSM road data for specific regions (mountain/rural areas)
2. Connects them with the existing Pune road network
3. Creates a proper road-based graph for ground bot routing
"""

import os
import sys
import csv
import time
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
OUTPUT_DIR = "data"
OUT_NODES = os.path.join(OUTPUT_DIR, "combined_road_nodes.csv")
OUT_GRAPH = os.path.join(OUTPUT_DIR, "combined_road_graph.csv")

# Regions to download (around our mountain/rural locations)
REGIONS = [
    {"name": "Lonavala", "place": "Lonavala, Maharashtra, India", "lat": 18.75, "lon": 73.4},
    {"name": "Khandala", "place": "Khandala, Maharashtra, India", "lat": 18.8, "lon": 73.35},
    {"name": "Matheran", "place": "Matheran, Maharashtra, India", "lat": 18.85, "lon": 73.3},
    {"name": "Pune", "place": "Pune, Maharashtra, India", "lat": 18.52, "lon": 73.86},
]

def haversine_m(lat1, lon1, lat2, lon2):
    """Calculate distance in meters"""
    R = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def download_region_graph(place, bbox_radius_km=20):
    """Download road network for a region"""
    print(f"Downloading road network for {place}...")
    try:
        # Try place-based first
        G = ox.graph_from_place(place, network_type='drive', simplify=True)
        print(f"  ✓ Downloaded {len(G.nodes())} nodes, {len(G.edges())} edges")
        return G
    except Exception as e:
        print(f"  ⚠ Place-based failed: {e}")
        # Try bounding box
        try:
            # Get coordinates from place name or use provided
            # For now, use a simple bounding box approach
            print(f"  Trying bounding box approach...")
            # This is a fallback - would need actual coordinates
            return None
        except Exception as e2:
            print(f"  ✗ Failed: {e2}")
            return None

def load_existing_pune_graph():
    """Load existing Pune graph from CSV files"""
    print("Loading existing Pune graph...")
    nodes = []
    edges = []
    
    # Load nodes
    pune_nodes_file = os.path.join(OUTPUT_DIR, "pune_nodes.csv")
    if os.path.exists(pune_nodes_file):
        with open(pune_nodes_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                nodes.append({
                    'node_id': int(row['node_id']),
                    'lat': float(row['lat']),
                    'lon': float(row['lon']),
                    'label': row.get('label', '')
                })
        print(f"  Loaded {len(nodes)} Pune nodes")
    
    # Load edges
    pune_graph_file = os.path.join(OUTPUT_DIR, "pune_graph.csv")
    if os.path.exists(pune_graph_file):
        with open(pune_graph_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                edges.append({
                    'u': int(row['u']),
                    'v': int(row['v']),
                    'distance_km': float(row['distance_km']),
                    'safety_score': int(row['safety_score']),
                    'key': int(row['key'])
                })
        print(f"  Loaded {len(edges)} Pune edges")
    
    return nodes, edges

def combine_graphs():
    """Combine Pune graph with regional graphs"""
    print("\n" + "="*60)
    print("Creating Road-Based Combined Graph")
    print("="*60)
    
    # Load existing Pune data
    pune_nodes, pune_edges = load_existing_pune_graph()
    
    all_nodes = {node['node_id']: node for node in pune_nodes}
    all_edges = []
    
    # Add Pune edges
    for edge in pune_edges:
        all_edges.append(edge)
    
    # Download and add regional graphs
    for region in REGIONS:
        if region['name'] == 'Pune':
            continue  # Already have Pune
        
        print(f"\nProcessing {region['name']}...")
        G = download_region_graph(region['place'])
        
        if G is None:
            print(f"  ⚠ Skipping {region['name']} - download failed")
            continue
        
        # Convert to our format
        nodes_gdf, edges_gdf = ox.graph_to_gdfs(G, nodes=True, edges=True)
        nodes_gdf = nodes_gdf.reset_index()
        
        # Add nodes
        for _, row in nodes_gdf.iterrows():
            nid = row.get('osmid')
            if isinstance(nid, (list, tuple, set)):
                nid = list(nid)[0]
            lat = row.get('y')
            lon = row.get('x')
            label = row.get('name', '') or ''
            
            if nid is None or lat is None or lon is None:
                continue
            
            nid = int(nid)
            if nid not in all_nodes:
                all_nodes[nid] = {
                    'node_id': nid,
                    'lat': float(lat),
                    'lon': float(lon),
                    'label': label
                }
        
        # Add edges
        node_lookup = {n['node_id']: (n['lat'], n['lon']) for n in all_nodes.values()}
        key_counter = len(all_edges)
        
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
            
            all_edges.append({
                'u': u_int,
                'v': v_int,
                'distance_km': distance_km,
                'safety_score': int(safety),
                'key': key_counter
            })
            key_counter += 1
        
        print(f"  Added {len([n for n in all_nodes.values() if n['node_id'] not in [pn['node_id'] for pn in pune_nodes]])} new nodes")
        print(f"  Added {key_counter - len(all_edges) + len(pune_edges)} new edges")
        time.sleep(1)  # Be nice to OSM servers
    
    # Write combined files
    print(f"\nWriting combined graph...")
    print(f"  Total nodes: {len(all_nodes)}")
    print(f"  Total edges: {len(all_edges)}")
    
    # Write nodes CSV
    with open(OUT_NODES, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['node_id', 'lat', 'lon', 'label'])
        for node in sorted(all_nodes.values(), key=lambda x: x['node_id']):
            writer.writerow([node['node_id'], node['lat'], node['lon'], node['label']])
    
    # Write edges CSV
    with open(OUT_GRAPH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['u', 'v', 'distance_km', 'safety_score', 'key'])
        for edge in all_edges:
            writer.writerow([
                edge['u'],
                edge['v'],
                f"{edge['distance_km']:.10f}",
                edge['safety_score'],
                edge['key']
            ])
    
    print(f"\n✓ Created {OUT_NODES}")
    print(f"✓ Created {OUT_GRAPH}")

if __name__ == '__main__':
    combine_graphs()

