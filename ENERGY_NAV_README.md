# Energy-Efficient Navigation System

## Overview

This is an enhanced navigation system designed for **drones and ground surveillance bots** that calculates the most energy-efficient routes while checking battery capacity and round-trip feasibility.

## Features

### ✅ Core Functionality
- **Energy-Efficient Route Calculation**: Computes routes optimized for energy consumption based on terrain type
- **Battery Capacity Checking**: Validates if a round trip is feasible with the given battery capacity
- **Travel Time Estimation**: Calculates estimated travel time based on vehicle type and terrain
- **Multi-Location Support**: Includes mountain, rural, and urban (Pune) locations

### 🗺️ Location Data
- **Mountain Locations**: 11 locations including Lonavala, Khandala, Matheran, and Himalayan regions
- **Rural Locations**: 11 locations including villages and rural areas around Pune
- **Pune Locations**: 17 key landmarks in Pune city

### 🚁 Vehicle Types
- **Drone**: Optimized for aerial navigation
  - Urban: 50 Wh/km, 40 km/h
  - Rural: 60 Wh/km, 35 km/h
  - Mountain: 120 Wh/km, 20 km/h
- **Ground Bot**: Optimized for ground navigation
  - Urban: 30 Wh/km, 25 km/h
  - Rural: 45 Wh/km, 15 km/h
  - Mountain: 100 Wh/km, 8 km/h

## Usage

### Starting the Server

```bash
cd server
python app.py
```

The server will start on `http://localhost:5000`

### Using the Web Interface

1. Open `http://localhost:5000` in your browser
2. Select **Start Location** and **End Location** from the dropdowns
3. Choose **Vehicle Type** (Drone or Ground Bot)
4. Enter **Battery Capacity** in Watt-hours (Wh)
5. Select **Route Mode** (Fastest or Safest)
6. Click **Compute Route**

### Route Information Display

The system displays:
- **Distance**: One-way and round-trip distance
- **Travel Time**: Estimated time for one-way and round-trip
- **Energy Consumption**: Energy required for one-way and round-trip
- **Battery Status**: 
  - ✅ Feasible: Round trip is possible with current battery
  - ❌ Not Feasible: Round trip requires more battery than available
- **Battery Remaining**: Shows remaining battery after round trip

## File Structure

```
navigation/
├── server/
│   ├── app.py                    # Flask server with energy calculation
│   └── static/
│       └── energy_nav.html       # Energy-efficient navigation UI
├── energy_calculator.py          # Energy consumption calculation module
├── create_sample_locations.py    # Script to generate location data
├── data/
│   ├── combined_nodes.csv        # All locations (mountain, rural, Pune)
│   ├── combined_graph.csv        # Route graph connecting locations
│   ├── pune_nodes.csv            # Original Pune nodes
│   └── pune_graph.csv            # Original Pune graph
└── navigation.exe                # C-based route computation engine
```

## API Endpoints

### `GET /nodes`
Returns list of all available nodes (locations)

**Query Parameters:**
- `combined` (default: `true`): Use combined data (mountain, rural, Pune)

### `POST /route`
Computes a route between two locations

**Request Body:**
```json
{
  "src": "7000001",                    // Start node ID
  "dst": "9000001",                    // End node ID
  "mode": 1,                           // 1=Fastest, 2=Safest
  "vehicle_type": "drone",             // "drone" or "ground_bot"
  "battery_capacity_wh": 500,          // Battery capacity in Wh
  "use_combined": true                  // Use combined location data
}
```

**Response:**
```json
{
  "ok": true,
  "route": {
    "total_distance_km": 25.5,
    "nodes": [...],
    "edges": [...]
  },
  "energy": {
    "one_way_energy_wh": 1250.5,
    "round_trip_energy_wh": 2501.0,
    "total_time_hours": 0.75,
    "round_trip_time_hours": 1.5,
    "is_feasible": true,
    "battery_remaining_wh": 2499.0,
    "battery_percent_remaining": 99.96
  }
}
```

## Energy Calculation Details

### Terrain Types
- **Urban**: Flat, paved areas (lowest energy consumption)
- **Rural**: Unpaved roads, countryside (moderate energy)
- **Mountain**: Steep terrain, elevation changes (highest energy)
- **Forest**: Dense vegetation areas
- **Desert**: Sandy, arid terrain

### Elevation Penalty
- **Drone**: +15% energy per 100m elevation gain
- **Ground Bot**: +25% energy per 100m elevation gain

### Round Trip Calculation
The system automatically doubles the one-way energy consumption to check round-trip feasibility.

## Adding New Locations

To add new locations, edit `create_sample_locations.py`:

1. Add locations to `MOUNTAIN_LOCATIONS`, `RURAL_LOCATIONS`, or `PUNE_LOCATIONS`
2. Run: `python create_sample_locations.py`
3. This will regenerate `data/combined_nodes.csv` and `data/combined_graph.csv`

## Requirements

- Python 3.6+
- Flask
- Leaflet.js (loaded from CDN)
- navigation.exe (C-based route engine)

## Notes

- The system uses terrain heuristics based on location labels. For production use, integrate with elevation APIs (e.g., Google Elevation API, OpenElevation) for accurate elevation data.
- Energy consumption rates are estimates and should be calibrated based on actual vehicle specifications.
- The route graph connects locations within 50km of each other by default.

