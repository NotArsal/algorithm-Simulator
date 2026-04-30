"""
Energy consumption calculator for drone/ground bot navigation.
Calculates energy based on distance, terrain type, elevation, and vehicle type.
"""

import math

# Energy consumption rates (Wh per km) for different terrains
# Base consumption for flat urban terrain
ENERGY_RATES = {
    'drone': {
        'urban': 50.0,      # Wh/km - flat urban areas
        'rural': 60.0,      # Wh/km - rural areas (more wind resistance)
        'mountain': 120.0,   # Wh/km - mountains (elevation changes, wind)
        'forest': 80.0,      # Wh/km - forest areas
        'desert': 70.0,     # Wh/km - desert areas
    },
    'ground_bot': {
        'urban': 30.0,      # Wh/km - paved roads
        'rural': 45.0,      # Wh/km - unpaved roads
        'mountain': 100.0,  # Wh/km - steep terrain
        'forest': 60.0,     # Wh/km - rough terrain
        'desert': 50.0,     # Wh/km - sandy terrain
    }
}

# Speed in km/h for different terrains
SPEED_RATES = {
    'drone': {
        'urban': 40.0,      # km/h
        'rural': 35.0,
        'mountain': 20.0,
        'forest': 25.0,
        'desert': 30.0,
    },
    'ground_bot': {
        'urban': 25.0,      # km/h
        'rural': 15.0,
        'mountain': 8.0,
        'forest': 10.0,
        'desert': 12.0,
    }
}

# Elevation penalty multiplier (per 100m elevation gain)
ELEVATION_PENALTY = {
    'drone': 0.15,      # 15% more energy per 100m elevation
    'ground_bot': 0.25  # 25% more energy per 100m elevation
}


def get_terrain_type(lat, lon, label=""):
    """
    Determine terrain type based on location.
    For now, uses simple heuristics. Can be enhanced with elevation data.
    """
    label_lower = label.lower() if label else ""
    
    # Mountain keywords
    if any(kw in label_lower for kw in ['mountain', 'hill', 'peak', 'ridge', 'summit', 'alp', 'mont']):
        return 'mountain'
    
    # Rural keywords
    if any(kw in label_lower for kw in ['village', 'rural', 'countryside', 'farm', 'agricultural']):
        return 'rural'
    
    # Forest keywords
    if any(kw in label_lower for kw in ['forest', 'wood', 'jungle', 'park']):
        return 'forest'
    
    # Default based on coordinates (simple heuristic)
    # This is a placeholder - in production, use elevation/terrain APIs
    # For now, assume urban for Pune region, rural for others
    if 18.0 <= lat <= 19.0 and 73.0 <= lon <= 74.0:
        return 'urban'  # Pune region
    elif lat > 30.0 or lat < 10.0:  # Rough heuristic for mountain regions
        return 'mountain'
    else:
        return 'rural'


def calculate_energy_consumption(distance_km, terrain_type, vehicle_type='drone', 
                                 elevation_gain_m=0, elevation_loss_m=0):
    """
    Calculate energy consumption for a route segment.
    
    Args:
        distance_km: Distance in kilometers
        terrain_type: 'urban', 'rural', 'mountain', 'forest', 'desert'
        vehicle_type: 'drone' or 'ground_bot'
        elevation_gain_m: Elevation gain in meters
        elevation_loss_m: Elevation loss in meters (negative gain)
    
    Returns:
        Energy consumption in Wh (Watt-hours)
    """
    if vehicle_type not in ENERGY_RATES:
        vehicle_type = 'drone'  # default
    
    if terrain_type not in ENERGY_RATES[vehicle_type]:
        terrain_type = 'urban'  # default
    
    base_rate = ENERGY_RATES[vehicle_type][terrain_type]
    
    # Base energy for distance
    base_energy = base_rate * distance_km
    
    # Elevation penalty (only for gain, loss is minimal benefit)
    if elevation_gain_m > 0:
        elevation_multiplier = 1.0 + (ELEVATION_PENALTY[vehicle_type] * (elevation_gain_m / 100.0))
        base_energy *= elevation_multiplier
    
    return base_energy


def calculate_travel_time(distance_km, terrain_type, vehicle_type='drone'):
    """
    Calculate travel time for a route segment.
    
    Args:
        distance_km: Distance in kilometers
        terrain_type: Terrain type
        vehicle_type: 'drone' or 'ground_bot'
    
    Returns:
        Time in hours
    """
    if vehicle_type not in SPEED_RATES:
        vehicle_type = 'drone'
    
    if terrain_type not in SPEED_RATES[vehicle_type]:
        terrain_type = 'urban'
    
    speed_kmh = SPEED_RATES[vehicle_type][terrain_type]
    time_hours = distance_km / speed_kmh if speed_kmh > 0 else 0
    
    return time_hours


def calculate_route_energy(route_data, vehicle_type='drone', battery_capacity_wh=None):
    """
    Calculate total energy consumption for a route.
    
    Args:
        route_data: Route data from last_route.json format
        vehicle_type: 'drone' or 'ground_bot'
        battery_capacity_wh: Battery capacity in Wh (optional, for feasibility check)
    
    Returns:
        Dictionary with energy metrics
    """
    total_energy_wh = 0.0
    total_time_hours = 0.0
    segments = []
    
    nodes = route_data.get('nodes', [])
    edges = route_data.get('edges', [])
    
    # Calculate for each edge
    for i, edge in enumerate(edges):
        distance_km = edge.get('distance_km', 0)
        if distance_km is None or distance_km <= 0:
            continue
        
        # Get terrain type from nodes
        from_node = next((n for n in nodes if n.get('node_id') == edge.get('from')), None)
        to_node = next((n for n in nodes if n.get('node_id') == edge.get('to')), None)
        
        # Determine terrain (use from_node label or default)
        terrain = 'urban'  # default
        if from_node:
            terrain = get_terrain_type(
                from_node.get('lat', 0),
                from_node.get('lon', 0),
                from_node.get('label', '')
            )
        
        # Calculate elevation (placeholder - would need elevation data)
        elevation_gain = 0  # TODO: Get from elevation data
        
        # Calculate energy and time for this segment
        segment_energy = calculate_energy_consumption(
            distance_km, terrain, vehicle_type, elevation_gain, 0
        )
        segment_time = calculate_travel_time(distance_km, terrain, vehicle_type)
        
        total_energy_wh += segment_energy
        total_time_hours += segment_time
        
        segments.append({
            'distance_km': distance_km,
            'terrain': terrain,
            'energy_wh': segment_energy,
            'time_hours': segment_time
        })
    
    # Round trip energy (double the one-way)
    round_trip_energy = total_energy_wh * 2
    
    # Feasibility check
    is_feasible = True
    battery_remaining = None
    battery_percent_remaining = None
    min_battery_required_wh = round_trip_energy  # Minimum battery needed for round trip
    
    if battery_capacity_wh:
        battery_remaining = battery_capacity_wh - round_trip_energy
        is_feasible = battery_remaining >= 0
        battery_percent_remaining = (battery_remaining / battery_capacity_wh * 100) if battery_capacity_wh > 0 else None
    
    return {
        'one_way_energy_wh': total_energy_wh,
        'round_trip_energy_wh': round_trip_energy,
        'total_time_hours': total_time_hours,
        'round_trip_time_hours': total_time_hours * 2,
        'is_feasible': is_feasible,
        'battery_remaining_wh': battery_remaining,
        'battery_percent_remaining': battery_percent_remaining,
        'min_battery_required_wh': min_battery_required_wh,  # Minimum battery needed
        'segments': segments
    }

