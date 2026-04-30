# Manual India OSM Download Guide

## Option 1: Download from Geofabrik (Recommended - Easiest)

### Step 1: Download India OSM PBF File

1. **Go to Geofabrik Downloads:**
   - Visit: https://download.geofabrik.de/asia/india.html
   - Click on **"india-latest.osm.pbf"**
   - File size: ~2-3 GB (compressed)
   - Download time: 10-30 minutes (depending on connection)

2. **Save the file:**
   - Save to: `D:\navigation_india_osm\india-latest.osm.pbf`
   - Or any location you prefer

### Step 2: Convert PBF to CSV Format

After downloading, run this script to convert it:

```bash
python convert_osm_pbf_to_csv.py
```

This will create:
- `D:\navigation_india_osm\india_nodes.csv`
- `D:\navigation_india_osm\india_graph.csv`

---

## Option 2: Download by Region (Smaller Files)

If you want smaller, more manageable files:

1. **Go to:** https://download.geofabrik.de/asia/india.html
2. **Download individual states/regions:**
   - Maharashtra: `maharashtra-latest.osm.pbf`
   - Delhi: `delhi-latest.osm.pbf`
   - Karnataka: `karnataka-latest.osm.pbf`
   - etc.

3. **Convert each file** using the conversion script

---

## Option 3: Use OSMnx to Download Specific Cities

If you want to download specific cities only:

1. **Create a script** with cities you want:
```python
import osmnx as ox
import pandas as pd

cities = [
    "Mumbai, India",
    "Delhi, India",
    "Bangalore, India",
    # Add more cities
]

# Download and combine
graphs = []
for city in cities:
    print(f"Downloading {city}...")
    G = ox.graph_from_place(city, network_type='drive')
    graphs.append(G)

# Combine and save
# (use the conversion code from download_india_cities.py)
```

---

## Conversion Script

Create this file: `convert_osm_pbf_to_csv.py`

```python
"""
Convert OSM PBF file to CSV format for navigation system
"""
import os
import sys
import json
import math

try:
    import osmnx as ox
    import pandas as pd
    import networkx as nx
except ImportError:
    print("ERROR: Install required packages:")
    print("  pip install osmnx pandas networkx geopandas")
    sys.exit(1)

# Configuration
PBF_FILE = "D:/navigation_india_osm/india-latest.osm.pbf"  # Change this to your PBF file location
OUTPUT_DIR = "D:/navigation_india_osm"
OUT_NODES = os.path.join(OUTPUT_DIR, "india_nodes.csv")
OUT_GRAPH = os.path.join(OUTPUT_DIR, "india_graph.csv")

def haversine_m(lat1, lon1, lat2, lon2):
    """Calculate distance in meters"""
    R = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def main():
    print("="*70)
    print("OSM PBF to CSV Converter")
    print("="*70)
    
    if not os.path.exists(PBF_FILE):
        print(f"\nERROR: PBF file not found: {PBF_FILE}")
        print("\nPlease:")
        print("1. Download india-latest.osm.pbf from:")
        print("   https://download.geofabrik.de/asia/india.html")
        print(f"2. Save it to: {PBF_FILE}")
        print("3. Run this script again")
        return
    
    print(f"\nLoading PBF file: {PBF_FILE}")
    print("This may take 10-30 minutes depending on file size...")
    
    try:
        # Load PBF file
        G = ox.graph_from_xml(PBF_FILE, simplify=True)
        print(f"Loaded graph: {len(G.nodes()):,} nodes, {len(G.edges()):,} edges")
    except Exception as e:
        print(f"ERROR loading PBF: {e}")
        print("\nTrying alternative method...")
        try:
            # Alternative: use graph_from_file
            G = ox.graph_from_file(PBF_FILE, simplify=True)
            print(f"Loaded graph: {len(G.nodes()):,} nodes, {len(G.edges()):,} edges")
        except Exception as e2:
            print(f"ERROR: {e2}")
            return
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("\n[1/3] Converting nodes...")
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
        
        key_counter += 1
        if key_counter % 100000 == 0:
            print(f"  Processed {key_counter:,} edges...")
    
    print("\n[3/3] Writing graph file...")
    df_edges = pd.DataFrame(edge_rows)
    df_edges.to_csv(OUT_GRAPH, index=False)
    print(f"  [OK] Wrote {OUT_GRAPH} ({len(df_edges):,} rows)")
    
    print("\n" + "="*70)
    print("CONVERSION COMPLETE!")
    print("="*70)
    print(f"  Nodes: {len(df_nodes):,}")
    print(f"  Edges: {len(df_edges):,}")
    print(f"  Output: {OUTPUT_DIR}")
    print("\nThe server will automatically use this data!")

if __name__ == '__main__':
    main()
```

---

## Quick Steps Summary

1. **Download PBF file:**
   - Go to: https://download.geofabrik.de/asia/india.html
   - Download: `india-latest.osm.pbf`
   - Save to: `D:\navigation_india_osm\india-latest.osm.pbf`

2. **Create conversion script:**
   - Copy the code above to `convert_osm_pbf_to_csv.py`
   - Update `PBF_FILE` path if needed

3. **Run conversion:**
   ```bash
   python convert_osm_pbf_to_csv.py
   ```

4. **Wait for conversion:**
   - Takes 10-30 minutes depending on file size
   - Creates CSV files automatically

5. **Done!**
   - Server will automatically detect and use the files
   - No restart needed (server checks on each request)

---

## Alternative: Download Smaller Regions

If full India is too large, download specific states:

- **Maharashtra:** https://download.geofabrik.de/asia/india/maharashtra.html
- **Delhi:** https://download.geofabrik.de/asia/india/delhi.html
- **Karnataka:** https://download.geofabrik.de/asia/india/karnataka.html

Then convert each one separately.

---

## File Sizes (Approximate)

- **Full India PBF:** 2-3 GB (compressed)
- **Full India CSV:** 1-2 GB (uncompressed)
- **Maharashtra PBF:** 100-200 MB
- **Delhi PBF:** 50-100 MB

---

**That's it!** Download manually and convert. Much more reliable than automated download! 📥

