# India OSM Road Network Download Guide

## Overview

To get the complete India road network for ground bot navigation, you have several options:

## Option 1: Download Full India (Recommended for Complete Coverage)

**File:** `download_india_osm.py`

This script downloads the complete India road network from OpenStreetMap.

### Requirements
- Python 3.6+
- `pip install osmnx pandas networkx`
- **10-50 GB disk space**
- **2-6 hours download time** (depending on connection)
- Stable internet connection

### Usage
```bash
python download_india_osm.py
```

Choose option 1 for full India download.

### What You Get
- Complete road network for all of India
- Millions of nodes and edges
- All major highways, roads, and streets
- Suitable for ground bot navigation across India

### Alternative: Manual PBF Download

If the script fails or times out, you can download manually:

1. Go to: https://download.geofabrik.de/asia/india.html
2. Download: `india-latest.osm.pbf` (2-3 GB compressed)
3. Extract and process using OSMnx:
   ```python
   import osmnx as ox
   G = ox.graph_from_xml('india-latest.osm.pbf', simplify=True)
   ```

## Option 2: Download by Major Cities/Regions (Faster, More Manageable)

**File:** `download_india_osm.py`

Choose option 2 when running the script.

### What You Get
- Road networks for 20+ major Indian cities
- Faster download (30-60 minutes)
- Smaller file size (1-5 GB)
- May miss some rural connections between cities

### Cities Included
- Mumbai, Delhi, Bangalore, Hyderabad, Chennai, Kolkata
- Pune, Ahmedabad, Jaipur, Surat, Lucknow, Kanpur
- Nagpur, Indore, Thane, Bhopal, Visakhapatnam, Patna
- Vadodara, Ghaziabad, and more

## Option 3: Create Road-Based Combined Graph (Current Locations)

**File:** `create_road_based_graph.py`

This script creates a road-based graph for the current mountain/rural/Pune locations.

### Usage
```bash
python create_road_based_graph.py
```

### What It Does
- Downloads OSM road data for specific regions (Lonavala, Khandala, Matheran, Pune)
- Combines them with existing Pune road network
- Creates `data/combined_road_graph.csv` and `data/combined_road_nodes.csv`

### When to Use
- For testing with current locations
- When you only need specific regions
- Faster than full India download

## Current Status

### Fixed Issues
✅ Mountain/rural locations now connected to road network
✅ Ground bot routing uses road-based graphs
✅ Battery requirement display added
✅ System differentiates between drone (direct) and ground bot (road) routing

### Files Created
- `data/combined_graph.csv` - Updated with road connections
- `data/combined_nodes.csv` - All locations (mountain, rural, Pune)

### Next Steps for Full India Coverage

1. **Run full India download:**
   ```bash
   python download_india_osm.py
   # Choose option 1
   ```

2. **Update server configuration** to use India graph:
   - The server will automatically detect `data/india_osm/india_graph.csv`
   - Or manually specify in `server/app.py`

3. **Expected File Sizes:**
   - Nodes: 5-20 million nodes
   - Edges: 10-50 million edges
   - Disk space: 10-50 GB

## Notes

- **Ground Bots**: Always use road-based graphs (OSM road network)
- **Drones**: Can use direct paths or road graphs (prefer direct for efficiency)
- **Mountain Locations**: May require special handling if far from road network
- **Processing Time**: Full India graph processing may take 1-2 hours after download

## Troubleshooting

### Download Fails
- Check internet connection
- Try option 2 (cities) instead of full India
- Use manual PBF download method

### Out of Memory
- Process in batches (modify script)
- Use option 2 (cities) instead
- Increase system RAM

### Mountain Locations Not Found
- Run `fix_mountain_connectivity.py` to connect them to road network
- Increase `max_distance_km` parameter if locations are far from roads

## Support

For issues or questions:
1. Check that OSMnx is properly installed
2. Verify internet connection
3. Check available disk space
4. Review error messages for specific issues

