"""
extract_pune_nodes.py

Safer extraction of node coordinate table for Pune using OSMnx.
- Retries on transient network failures.
- Writes: pune_nodes.csv with columns: node_id,lat,lon

Usage:
    python extract_pune_nodes.py
"""

import time
import sys
import os

try:
    import osmnx as ox
    import pandas as pd
except Exception as e:
    print("ERROR: required Python packages missing. Run:")
    print("  python -m pip install osmnx pandas")
    raise

PLACE = "Pune, India"
OUT_NODES = "pune_nodes.csv"
MAX_RETRIES = 3
BASE_DELAY = 2.0

def try_get_graph(retries=MAX_RETRIES):
    attempt = 0
    while attempt < retries:
        try:
            print(f"[extract_pune_nodes] Attempt {attempt+1} to download graph for '{PLACE}'...")
            G = ox.graph_from_place(PLACE, network_type='drive')
            print("[extract_pune_nodes] Graph downloaded.")
            return G
        except Exception as e:
            attempt += 1
            wait = BASE_DELAY * (2 ** (attempt-1))
            print(f"[extract_pune_nodes] Attempt {attempt} failed: {type(e).__name__}: {e}")
            if attempt < retries:
                print(f"[extract_pune_nodes] Retrying in {wait:.0f}s...")
                time.sleep(wait)
            else:
                print("[extract_pune_nodes] All attempts failed.")
                return None

def main():
    G = try_get_graph()
    if G is None:
        print("\nCould not fetch OSM data. See extract_pune_edges.py for offline fallback instructions.")
        sys.exit(1)
    try:
        print("[extract_pune_nodes] Converting graph to nodes GeoDataFrame...")
        nodes_gdf, edges_gdf = ox.graph_to_gdfs(G, nodes=True, edges=True)
        nodes_gdf = nodes_gdf.reset_index()
        nodes_df = nodes_gdf[['osmid','y','x']].rename(columns={'osmid':'node_id','y':'lat','x':'lon'})
        nodes_df.to_csv(OUT_NODES, index=False)
        print(f"[extract_pune_nodes] Wrote {OUT_NODES} ({len(nodes_df)} rows).")
    except Exception as e:
        print("[extract_pune_nodes] Failed to export nodes:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
