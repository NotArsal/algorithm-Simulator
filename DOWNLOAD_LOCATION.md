# India OSM Download Location

## ✅ Updated to D: Drive

The India OSM download has been configured to save files to **D: drive** to save space on C: drive.

### Download Location
- **Directory:** `D:\navigation_india_osm\`
- **Files:**
  - `india_nodes.csv` - All road network nodes
  - `india_graph.csv` - All road network edges
  - `edges_geom.json` - Edge geometries (optional)

### Server Configuration
The server automatically checks for files in this order:
1. **D:\navigation_india_osm\** (preferred)
2. `data/india_osm/` (fallback if D: not available)

### Check Download Status
Run this command to check progress:
```bash
python check_download_status.py
```

### Benefits
- ✅ Saves space on C: drive
- ✅ Can store large files (500 MB - 2 GB)
- ✅ Server automatically detects and uses D: drive location
- ✅ No manual configuration needed

### Current Status
Download is running in the background. Check status with the command above.

