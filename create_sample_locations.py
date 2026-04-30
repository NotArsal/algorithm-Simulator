"""
Create sample location data for mountain and rural areas, plus Pune.
This creates CSV files compatible with the navigation system.
"""

import csv
import random
import math

# Sample mountain locations (Himalayan region, Western Ghats, etc.)
MOUNTAIN_LOCATIONS = [
    # Western Ghats near Pune
    {"node_id": 9000001, "lat": 18.7500, "lon": 73.4000, "label": "Lonavala Mountain"},
    {"node_id": 9000002, "lat": 18.8000, "lon": 73.3500, "label": "Khandala Peak"},
    {"node_id": 9000003, "lat": 18.8500, "lon": 73.3000, "label": "Matheran Hill Station"},
    {"node_id": 9000004, "lat": 18.9000, "lon": 73.2500, "label": "Prabalgad Fort"},
    {"node_id": 9000005, "lat": 18.9500, "lon": 73.2000, "label": "Raigad Fort"},
    
    # Himalayan region (sample)
    {"node_id": 9000010, "lat": 30.7333, "lon": 79.0667, "label": "Badrinath Mountain"},
    {"node_id": 9000011, "lat": 30.7500, "lon": 79.1000, "label": "Kedarnath Peak"},
    {"node_id": 9000012, "lat": 30.8000, "lon": 79.1500, "label": "Gangotri Ridge"},
    
    # More Western Ghats
    {"node_id": 9000020, "lat": 19.0000, "lon": 73.1500, "label": "Sinhagad Fort"},
    {"node_id": 9000021, "lat": 19.0500, "lon": 73.1000, "label": "Torna Fort"},
    {"node_id": 9000022, "lat": 19.1000, "lon": 73.0500, "label": "Rajgad Fort"},
]

# Sample rural locations
RURAL_LOCATIONS = [
    # Rural areas around Pune
    {"node_id": 8000001, "lat": 18.6000, "lon": 73.7000, "label": "Mulshi Village"},
    {"node_id": 8000002, "lat": 18.6500, "lon": 73.6500, "label": "Lavasa Rural Area"},
    {"node_id": 8000003, "lat": 18.7000, "lon": 73.6000, "label": "Panshet Village"},
    {"node_id": 8000004, "lat": 18.5500, "lon": 73.7500, "label": "Khadakwasla Rural"},
    {"node_id": 8000005, "lat": 18.5000, "lon": 73.8000, "label": "Saswad Village"},
    
    # More rural locations
    {"node_id": 8000010, "lat": 18.4500, "lon": 73.8500, "label": "Purandar Village"},
    {"node_id": 8000011, "lat": 18.4000, "lon": 73.9000, "label": "Baramati Rural"},
    {"node_id": 8000012, "lat": 18.3500, "lon": 73.9500, "label": "Indapur Village"},
    
    # Distant rural
    {"node_id": 8000020, "lat": 19.2000, "lon": 74.0000, "label": "Ahmednagar Rural"},
    {"node_id": 8000021, "lat": 19.2500, "lon": 74.0500, "label": "Shirdi Village"},
    {"node_id": 8000022, "lat": 19.3000, "lon": 74.1000, "label": "Kopargaon Rural"},
]

# Pune city locations (key landmarks)
PUNE_LOCATIONS = [
    {"node_id": 7000001, "lat": 18.5204, "lon": 73.8567, "label": "Pune City Center"},
    {"node_id": 7000002, "lat": 18.4986, "lon": 73.8638, "label": "Swargate"},
    {"node_id": 7000003, "lat": 18.5310, "lon": 73.8567, "label": "Shivaji Nagar"},
    {"node_id": 7000004, "lat": 18.5165, "lon": 73.8397, "label": "FC Road"},
    {"node_id": 7000005, "lat": 18.5205, "lon": 73.8550, "label": "Deccan"},
    {"node_id": 7000006, "lat": 18.5390, "lon": 73.9016, "label": "Koregaon Park"},
    {"node_id": 7000007, "lat": 18.5596, "lon": 73.7938, "label": "Baner"},
    {"node_id": 7000008, "lat": 18.5630, "lon": 73.8203, "label": "Aundh"},
    {"node_id": 7000009, "lat": 18.5933, "lon": 73.7388, "label": "Hinjewadi"},
    {"node_id": 7000010, "lat": 18.4988, "lon": 73.8107, "label": "Kothrud"},
    {"node_id": 7000011, "lat": 18.5537, "lon": 73.9006, "label": "Yerawada"},
    {"node_id": 7000012, "lat": 18.5980, "lon": 73.7814, "label": "Pimple Saudagar"},
    {"node_id": 7000013, "lat": 18.5167, "lon": 73.8562, "label": "Camp"},
    {"node_id": 7000014, "lat": 18.5065, "lon": 73.9143, "label": "Magarpatta"},
    {"node_id": 7000015, "lat": 18.5286, "lon": 73.8768, "label": "Pune Railway Station"},
    {"node_id": 7000016, "lat": 18.4300, "lon": 73.8676, "label": "Katraj"},
    {"node_id": 7000017, "lat": 18.4900, "lon": 73.9249, "label": "Hadapsar"},
]


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km"""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def create_nodes_csv(filename='data/combined_nodes.csv'):
    """Create a combined nodes CSV with all locations"""
    all_locations = MOUNTAIN_LOCATIONS + RURAL_LOCATIONS + PUNE_LOCATIONS
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['node_id', 'lat', 'lon', 'label'])
        for loc in all_locations:
            writer.writerow([loc['node_id'], loc['lat'], loc['lon'], loc['label']])
    
    print(f"Created {filename} with {len(all_locations)} nodes")
    return all_locations


def create_edges_csv(nodes, filename='data/combined_graph.csv', max_distance_km=50.0):
    """Create edges between nearby nodes"""
    edges = []
    edge_id = 0
    
    for i, node1 in enumerate(nodes):
        for j, node2 in enumerate(nodes[i+1:], start=i+1):
            distance = haversine_distance(
                node1['lat'], node1['lon'],
                node2['lat'], node2['lon']
            )
            
            # Only create edges for nearby nodes
            if distance <= max_distance_km:
                # Safety score: higher for shorter distances, lower for mountains
                base_safety = 80.0
                if 'mountain' in node1['label'].lower() or 'mountain' in node2['label'].lower():
                    base_safety = 50.0
                elif 'rural' in node1['label'].lower() or 'rural' in node2['label'].lower():
                    base_safety = 65.0
                
                # Add some randomness
                safety = max(30, min(95, base_safety + random.uniform(-10, 10)))
                
                edges.append({
                    'u': node1['node_id'],
                    'v': node2['node_id'],
                    'distance_km': distance,
                    'safety_score': int(safety),
                    'key': edge_id
                })
                edge_id += 1
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['u', 'v', 'distance_km', 'safety_score', 'key'])
        for edge in edges:
            writer.writerow([
                edge['u'], edge['v'], 
                f"{edge['distance_km']:.10f}",
                edge['safety_score'],
                edge['key']
            ])
    
    print(f"Created {filename} with {len(edges)} edges")
    return edges


if __name__ == '__main__':
    import os
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Create nodes
    nodes = create_nodes_csv()
    
    # Create edges (connect nodes within 50km)
    edges = create_edges_csv(nodes, max_distance_km=50.0)
    
    print(f"\nSummary:")
    print(f"  Mountain locations: {len(MOUNTAIN_LOCATIONS)}")
    print(f"  Rural locations: {len(RURAL_LOCATIONS)}")
    print(f"  Pune locations: {len(PUNE_LOCATIONS)}")
    print(f"  Total nodes: {len(nodes)}")
    print(f"  Total edges: {len(edges)}")

