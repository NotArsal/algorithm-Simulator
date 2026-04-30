# India OSM Download Status

## Current Status: ⏳ IN PROGRESS

The download script is running in the background, downloading road networks for 30 major Indian cities.

### What's Being Downloaded

- **30 Major Indian Cities/Regions:**
  - Mumbai, Delhi, Bangalore, Hyderabad, Chennai, Kolkata
  - Pune, Ahmedabad, Jaipur, Surat, Lucknow, Kanpur
  - Nagpur, Indore, Thane, Bhopal, Visakhapatnam, Patna
  - Vadodara, Ghaziabad, Ludhiana, Agra, Nashik, Faridabad
  - Meerut, Rajkot, Varanasi, Srinagar, Amritsar, Chandigarh

### Expected Output

When complete, you'll have:
- `data/india_osm/india_nodes.csv` - All road network nodes
- `data/india_osm/india_graph.csv` - All road network edges
- `data/india_osm/edges_geom.json` - Edge geometries (optional)

### Estimated Time

- **Download time:** 30-60 minutes (depending on connection speed)
- **Processing time:** 10-20 minutes (converting to CSV format)
- **Total:** ~1-1.5 hours

### File Sizes (Estimated)

- Nodes: 500,000 - 2,000,000 nodes
- Edges: 1,000,000 - 5,000,000 edges
- Disk space: 500 MB - 2 GB

### How to Check Progress

1. Check if files are being created:
   ```bash
   dir data\india_osm
   ```

2. Check Python process:
   - The script will print progress as it downloads each city
   - Look for output showing "[X/30] Downloading..."

3. When complete, you'll see:
   - "DOWNLOAD COMPLETE!" message
   - Files in `data/india_osm/` directory

### Automatic Integration

Once the download completes, the server will **automatically** use the India OSM data:
- Ground bots will use India road network for routing
- Drones can also use it for better coverage
- No configuration changes needed!

### If Download Fails

If the download fails or times out:
1. Check internet connection
2. Re-run: `python download_india_cities.py`
3. The script will resume from where it left off (already downloaded cities won't be re-downloaded)

### Alternative: Manual Download

If automatic download doesn't work:
1. Go to: https://download.geofabrik.de/asia/india.html
2. Download: `india-latest.osm.pbf`
3. Use OSMnx to process it (see `download_india_osm.py` for code)

---

**Last Updated:** Download started - check back in 30-60 minutes!

