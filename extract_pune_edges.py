#!/usr/bin/env python3

import time, sys, os, json
from math import radians, sin, cos, sqrt, atan2

# defensive imports
try:
    import osmnx as ox
    import pandas as pd
except Exception as e:
    print("ERROR: required Python packages missing. Run:")
    print("  python -m pip install osmnx pandas")
    raise

PLACE = "Pune, India"
OUT_CSV = "pune_edges_raw.csv"
OUT_GEOM = "edges_geom.json"
MAX_RETRIES = 3
BASE_DELAY = 2.0  # seconds

def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1 = radians(lat1); phi2 = radians(lat2)
    dphi = radians(lat2 - lat1); dl = radians(lon2 - lon1)
    a = sin(dphi/2.0)**2 + cos(phi1)*cos(phi2)*(sin(dl/2.0)**2)
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def try_graph_from_place(retries=MAX_RETRIES):
    attempt = 0
    while attempt < retries:
        try:
            print(f"[extract] Attempt {attempt+1} to download graph for '{PLACE}'...")
            G = ox.graph_from_place(PLACE, network_type='drive')
            print("[extract] Graph downloaded.")
            return G
        except Exception as e:
            attempt += 1
            wait = BASE_DELAY * (2 ** (attempt-1))
            print(f"[extract] Attempt {attempt} failed: {type(e).__name__}: {e}")
            if attempt < retries:
                print(f"[extract] Retrying in {wait:.0f}s...")
                time.sleep(wait)
            else:
                print("[extract] All attempts failed.")
                return None

def main():
    G = try_graph_from_place()
    if G is None:
        print("Network failed. See earlier instructions for offline PBF fallback.")
        sys.exit(1)

    try:
        nodes = G.nodes
        rows = []
        geom_map = {}
        count = 0
        for u, v, key, data in G.edges(keys=True, data=True):
            # length (meters)
            length_m = None
            if 'length' in data and data['length'] is not None:
                try:
                    length_m = float(data['length'])
                except Exception:
                    length_m = None
            # geometry -> compute if length missing or to record polyline
            poly = None
            geom = data.get('geometry', None)
            if geom is not None and hasattr(geom, 'coords'):
                coords = list(geom.coords)
                # convert coords (lon,lat) pairs to list [lat,lon]
                poly = [[lat, lon] for (lon, lat) in coords]
                if length_m is None and len(coords) >= 2:
                    seg_sum = 0.0
                    for i in range(len(coords)-1):
                        lon1, lat1 = coords[i]
                        lon2, lat2 = coords[i+1]
                        seg_sum += haversine_m(lat1, lon1, lat2, lon2)
                    length_m = seg_sum
            # fallback: node-to-node straight distance
            if length_m is None:
                n_u = nodes[u]; n_v = nodes[v]
                lat1 = n_u.get('y') or n_u.get('lat')
                lon1 = n_u.get('x') or n_u.get('lon')
                lat2 = n_v.get('y') or n_v.get('lat')
                lon2 = n_v.get('x') or n_v.get('lon')
                if None not in (lat1, lon1, lat2, lon2):
                    length_m = haversine_m(lat1, lon1, lat2, lon2)
                    # create straight-line poly if geometry absent
                    if poly is None:
                        poly = [[lat1, lon1], [lat2, lon2]]
                else:
                    length_m = 1.0
            distance_km = float(length_m) / 1000.0
            rows.append((u, v, distance_km, key))
            # store geometry both directions for easy lookup later (if poly exists)
            key_uv = f"{u}|{v}"
            key_vu = f"{v}|{u}"
            if poly is not None:
                geom_map[key_uv] = poly
                geom_map[key_vu] = list(reversed(poly))
            else:
                geom_map[key_uv] = None
                geom_map[key_vu] = None
            count += 1
            if count % 5000 == 0:
                print(f"[extract] processed {count} edges...")

        df = pd.DataFrame(rows, columns=['u','v','distance_km','key'])
        df.to_csv(OUT_CSV, index=False)
        with open(OUT_GEOM, 'w', encoding='utf-8') as g:
            json.dump(geom_map, g, ensure_ascii=False)
        print(f"[extract] Wrote {OUT_CSV} ({len(df)} rows) and {OUT_GEOM} ({len(geom_map)} entries).")
    except Exception as e:
        print("[extract] Failed:", type(e).__name__, e)
        sys.exit(1)

if __name__ == "__main__":
    main()
