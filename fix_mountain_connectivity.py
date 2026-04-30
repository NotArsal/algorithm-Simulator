"""
Fix mountain and rural location connectivity by finding nearest road nodes
and connecting them to the road network.

This ensures ground bots can navigate to mountain/rural locations via roads.
"""

import os
import csv
import math

def haversine_m(lat1, lon1, lat2, lon2):
    """Calculate distance in meters"""
    R = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def find_nearest_road_nodes(target_nodes, road_nodes, max_distance_km=5.0):
    """
    Find nearest road nodes for each target node (mountain/rural locations).
    Creates connections between target nodes and their nearest road network nodes.
    """
    connections = []
    
    for target in target_nodes:
        target_id = target['node_id']
        target_lat = target['lat']
        target_lon = target['lon']
        
        nearest = None
        min_dist = float('inf')
        
        for road_node in road_nodes:
            road_id = road_node['node_id']
            road_lat = road_node['lat']
            road_lon = road_node['lon']
            
            dist_km = haversine_m(target_lat, target_lon, road_lat, road_lon) / 1000.0
            
            if dist_km < min_dist and dist_km <= max_distance_km:
                min_dist = dist_km
                nearest = {
                    'road_id': road_id,
                    'distance_km': dist_km,
                    'road_lat': road_lat,
                    'road_lon': road_lon
                }
        
        if nearest:
            connections.append({
                'target_id': target_id,
                'road_id': nearest['road_id'],
                'distance_km': nearest['distance_km']
            })
            print(f"  {target.get('label', target_id)} -> Road node {nearest['road_id']} ({nearest['distance_km']:.2f} km)")
    
    return connections

def main():
    print("=" * 60)
    print("Fixing Mountain/Rural Location Connectivity")
    print("=" * 60)
    
    # Load combined nodes
    combined_nodes_file = "data/combined_nodes.csv"
    if not os.path.exists(combined_nodes_file):
        print(f"ERROR: {combined_nodes_file} not found")
        return
    
    print("\n1. Loading nodes...")
    all_nodes = []
    mountain_nodes = []
    rural_nodes = []
    pune_nodes = []
    
    with open(combined_nodes_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            node = {
                'node_id': int(row['node_id']),
                'lat': float(row['lat']),
                'lon': float(row['lon']),
                'label': row.get('label', '')
            }
            all_nodes.append(node)
            
            label_lower = node['label'].lower()
            if 'mountain' in label_lower or 'peak' in label_lower or 'hill' in label_lower or 'fort' in label_lower:
                mountain_nodes.append(node)
            elif 'rural' in label_lower or 'village' in label_lower:
                rural_nodes.append(node)
            else:
                pune_nodes.append(node)
    
    print(f"  Total nodes: {len(all_nodes)}")
    print(f"  Mountain nodes: {len(mountain_nodes)}")
    print(f"  Rural nodes: {len(rural_nodes)}")
    print(f"  Pune/Other nodes: {len(pune_nodes)}")
    
    # Load Pune road nodes (these are actual road network nodes)
    pune_nodes_file = "data/pune_nodes.csv"
    road_nodes = []
    
    if os.path.exists(pune_nodes_file):
        print("\n2. Loading Pune road network nodes...")
        with open(pune_nodes_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                road_nodes.append({
                    'node_id': int(row['node_id']),
                    'lat': float(row['lat']),
                    'lon': float(row['lon'])
                })
        print(f"  Loaded {len(road_nodes)} road nodes")
    else:
        print(f"  WARNING: {pune_nodes_file} not found. Using all nodes as potential road nodes.")
        road_nodes = all_nodes
    
    # Find connections for mountain nodes
    print("\n3. Finding road connections for mountain locations...")
    mountain_connections = find_nearest_road_nodes(mountain_nodes, road_nodes, max_distance_km=10.0)
    
    # Find connections for rural nodes
    print("\n4. Finding road connections for rural locations...")
    rural_connections = find_nearest_road_nodes(rural_nodes, road_nodes, max_distance_km=5.0)
    
    # Load existing graph
    print("\n5. Loading existing graph...")
    combined_graph_file = "data/combined_graph.csv"
    existing_edges = []
    max_key = 0
    
    if os.path.exists(combined_graph_file):
        with open(combined_graph_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_edges.append({
                    'u': int(row['u']),
                    'v': int(row['v']),
                    'distance_km': float(row['distance_km']),
                    'safety_score': int(row['safety_score']),
                    'key': int(row['key'])
                })
                max_key = max(max_key, int(row['key']))
        print(f"  Loaded {len(existing_edges)} existing edges")
    
    # Add new connections
    print("\n6. Adding road connections...")
    new_edges = []
    key_counter = max_key + 1
    
    # Add mountain-to-road connections
    for conn in mountain_connections:
        # Connection from mountain to road (lower safety for mountain access roads)
        new_edges.append({
            'u': conn['target_id'],
            'v': conn['road_id'],
            'distance_km': conn['distance_km'],
            'safety_score': 50,  # Lower safety for mountain access
            'key': key_counter
        })
        key_counter += 1
        
        # Bidirectional: road to mountain
        new_edges.append({
            'u': conn['road_id'],
            'v': conn['target_id'],
            'distance_km': conn['distance_km'],
            'safety_score': 50,
            'key': key_counter
        })
        key_counter += 1
    
    # Add rural-to-road connections
    for conn in rural_connections:
        # Connection from rural to road
        new_edges.append({
            'u': conn['target_id'],
            'v': conn['road_id'],
            'distance_km': conn['distance_km'],
            'safety_score': 65,  # Moderate safety for rural roads
            'key': key_counter
        })
        key_counter += 1
        
        # Bidirectional
        new_edges.append({
            'u': conn['road_id'],
            'v': conn['target_id'],
            'distance_km': conn['distance_km'],
            'safety_score': 65,
            'key': key_counter
        })
        key_counter += 1
    
    print(f"  Added {len(new_edges)} new connection edges")
    
    # Combine all edges
    all_edges = existing_edges + new_edges
    
    # Write updated graph
    print("\n7. Writing updated graph...")
    with open(combined_graph_file, 'w', newline='', encoding='utf-8') as f:
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
    
    print(f"\n[SUCCESS] Updated {combined_graph_file}")
    print(f"  Total edges: {len(all_edges)}")
    print(f"  New connections: {len(new_edges)}")
    print("\nMountain and rural locations are now connected to the road network!")

if __name__ == '__main__':
    main()

