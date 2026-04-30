

import os, sys, time, json, random
from math import radians, sin, cos, sqrt, atan2

# defensive imports
try:
    import osmnx as ox
    import pandas as pd
except Exception as e:
    print("Missing packages. Install with conda/pip as described in the script header.")
    raise

# Config
PLACE = "Pune, India"
OUT_EDGES = "pune_edges_raw.csv"
OUT_NODES = "pune_nodes.csv"
OUT_GEOM = "edges_geom.json"
OUT_GRAPH = "pune_graph.csv"
LOCAL_PBF = "pune-latest.osm.pbf"   # put this in the same folder to use offline
MAX_RETRIES = 3
BASE_DELAY = 2.0
SAFETY_SEED = 1337

# haversine (meters)
def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1 = radians(lat1); phi2 = radians(lat2)
    dphi = radians(lat2 - lat1); dl = radians(lon2 - lon1)
    a = sin(dphi/2.0)**2 + cos(phi1)*cos(phi2)*(sin(dl/2.0)**2)
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def try_get_graph(place=PLACE):
    # 1) Prefer online via graph_from_place with retries
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            print(f"[build] Attempt {attempt+1} to download graph for '{place}'...")
            G = ox.graph_from_place(place, network_type='drive')
            print("[build] Graph downloaded via Overpass.")
            return G
        except Exception as e:
            attempt += 1
            wait = BASE_DELAY * (2 ** (attempt-1))
            print(f"[build] Attempt {attempt} failed: {type(e).__name__}: {e}")
            if attempt < MAX_RETRIES:
                print(f"[build] Retrying in {wait:.0f}s...")
                time.sleep(wait)
            else:
                print("[build] Online download failed after retries.")
                break

    # 2) Try local PBF fallback if present
    if os.path.exists(LOCAL_PBF):
        try:
            print("[build] Trying local PBF:", LOCAL_PBF)
            G = ox.graph_from_file(LOCAL_PBF, network_type='drive')
            print("[build] Graph loaded from local PBF.")
            return G
        except Exception as e:
            print("[build] Failed to load local PBF:", e)

    print("[build] No graph available. Please provide network access or place a PBF named 'pune-latest.osm.pbf' in this folder.")
    return None

def build_assets(G):
    # Nodes dataframe
    print("[build] Converting nodes...")
    nodes_gdf, edges_gdf = ox.graph_to_gdfs(G, nodes=True, edges=True)
    nodes_gdf = nodes_gdf.reset_index()
    # Ensure 'osmid' column exists (osmnx names it 'osmid' sometimes or 'osmid' can be list)
    if 'osmid' not in nodes_gdf.columns:
        # try 'index' fallback
        nodes_gdf = nodes_gdf.rename(columns={'index':'osmid'}) if 'index' in nodes_gdf.columns else nodes_gdf

    # create nodes CSV with single numeric id per row
    node_rows = []
    for _, row in nodes_gdf.iterrows():
        nid = row.get('osmid') if 'osmid' in row else row.get('node_id', None)
        # osmnx sometimes stores osmid as a list (multi-osmid). pick first if list
        if isinstance(nid, (list, tuple, set)):
            nid = list(nid)[0]
        lat = row.get('y') if 'y' in row else row.get('lat', None)
        lon = row.get('x') if 'x' in row else row.get('lon', None)
        label = row.get('name') if 'name' in row else ""
        if nid is None or lat is None or lon is None:
            # skip malformed
            continue
        node_rows.append({'node_id': int(nid), 'lat': float(lat), 'lon': float(lon), 'label': label or ""})

    df_nodes = pd.DataFrame(node_rows)
    df_nodes.to_csv(OUT_NODES, index=False)
    print(f"[build] Wrote {OUT_NODES} ({len(df_nodes)} rows).")

    # Edges: iterate G.edges(keys=True,data=True)
    print("[build] Processing edges and geometries...")
    geom_map = {}
    rows = []
    node_lookup = dict()  # just for quick node coords
    for r in node_rows:
        node_lookup[r['node_id']] = (r['lat'], r['lon'])

    count = 0
    for u, v, key, data in G.edges(keys=True, data=True):
        # normalize u/v to numeric osmid if needed (osmnx uses node ids directly)
        uid = int(u); vid = int(v)
        # length in meters prefer 'length'
        length_m = None
        if 'length' in data and data.get('length') is not None:
            try: length_m = float(data.get('length'))
            except: length_m = None
        # geometry polyline if available
        poly = None
        geom = data.get('geometry', None)
        if geom is not None and hasattr(geom, 'coords'):
            coords = list(geom.coords)
            # coords are (lon,lat) pairs
            poly = [[float(lat), float(lon)] for (lon, lat) in coords]
            if length_m is None and len(coords) >= 2:
                seg_sum = 0.0
                for i in range(len(coords)-1):
                    lon1, lat1 = coords[i]; lon2, lat2 = coords[i+1]
                    seg_sum += haversine_m(lat1, lon1, lat2, lon2)
                length_m = seg_sum
        # fallback: straight distance between node coords
        if length_m is None:
            n_u = node_lookup.get(uid)
            n_v = node_lookup.get(vid)
            if n_u and n_v:
                length_m = haversine_m(n_u[0], n_u[1], n_v[0], n_v[1])
                if poly is None:
                    poly = [[n_u[0], n_u[1]], [n_v[0], n_v[1]]]
            else:
                # last resort small length
                length_m = 1.0
        distance_km = float(length_m) / 1000.0

        rows.append((uid, vid, distance_km, key))
        # store both directions for easy lookup
        k1 = f"{uid}|{vid}"
        k2 = f"{vid}|{uid}"
        if poly is not None:
            geom_map[k1] = poly
            geom_map[k2] = list(reversed(poly))
        else:
            geom_map[k1] = None
            geom_map[k2] = None

        count += 1
        if count % 5000 == 0:
            print(f"[build] processed {count} edges...")

    df_edges = pd.DataFrame(rows, columns=['u','v','distance_km','key'])
    df_edges.to_csv(OUT_EDGES, index=False)
    with open(OUT_GEOM, 'w', encoding='utf-8') as f:
        json.dump(geom_map, f, ensure_ascii=False)
    print(f"[build] Wrote {OUT_EDGES} ({len(df_edges)} rows) and {OUT_GEOM} ({len(geom_map)} entries).")

    # Add reproducible safety column and write final graph CSV
    print("[build] Adding synthetic safety scores (stable seed)...")
    random.seed(SAFETY_SEED)
    df_edges['safety_score'] = df_edges.apply(lambda r: int(random.randint(30,95)), axis=1)
    cols = ['u','v','distance_km','safety_score','key']
    if 'key' not in df_edges.columns:
        df_edges['key'] = ''
    df_edges.to_csv(OUT_GRAPH, index=False, columns=cols)
    print(f"[build] Wrote {OUT_GRAPH} ({len(df_edges)} rows).")

def main():
    print("[build] Starting build process.")
    G = try_get_graph()
    if G is None:
        print("[build] Aborting: no graph.")
        sys.exit(1)
    build_assets(G)
    print("[build] Done. Files produced:")
    for fname in [OUT_EDGES, OUT_NODES, OUT_GEOM, OUT_GRAPH]:
        print("  -", fname, ":", os.path.exists(fname))

if __name__ == "__main__":
    main()
