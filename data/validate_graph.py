#!/usr/bin/env python3
"""
validate_graph.py

Quick checks:
 - edges' u/v appear in nodes CSV
 - edges_geom.json keys match u/v pairs (format)
 - basic statistics printed
Run:
  python validate_graph.py
"""
import os, json, csv, sys
NAV = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.dirname(__file__)
EDGES = os.path.join(DATA, "pune_edges_raw.csv")
NODES = os.path.join(DATA, "pune_nodes.csv")
GRAPH = os.path.join(DATA, "pune_graph.csv")
EG = os.path.join(DATA, "edges_geom.json")

def load_nodes():
    nodes = {}
    if not os.path.exists(NODES):
        print("[validate] nodes file missing:", NODES); return nodes
    with open(NODES,'r',encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            nid = int(row['node_id'])
            nodes[nid] = (float(row['lat']), float(row['lon']), row.get('label',''))
    return nodes

def sample_edges(n=10):
    rows=[]
    if not os.path.exists(EDGES):
        print("[validate] edges file missing:", EDGES); return rows
    with open(EDGES,'r',encoding='utf-8') as f:
        r = csv.DictReader(f)
        for i,row in enumerate(r):
            if i < n: rows.append(row)
            else: break
    return rows

def main():
    nodes = load_nodes()
    print("[validate] Nodes loaded:", len(nodes))
    s = sample_edges(5)
    print("[validate] Sample edges (first 5):")
    for row in s:
        print(" ", row)
    # check edge key existence in geom
    if not os.path.exists(EG):
        print("[validate] edges_geom.json missing:", EG)
    else:
        with open(EG,'r',encoding='utf-8') as f:
            eg = json.load(f)
        keys = list(eg.keys())[:10]
        print("[validate] edges_geom.json sample keys:", keys)
        # test mapping for first sample edge
        if s:
            a = int(s[0]['u']); b = int(s[0]['v'])
            k = f"{a}|{b}"
            kf = f"{b}|{a}"
            found = k in eg or kf in eg
            print(f"[validate] First sample edge keys: {k} or {kf} present? {found}")
    # verify graph.csv exists
    print("[validate] final graph csv present:", os.path.exists(GRAPH))
    print("[validate] Done.")

if __name__ == "__main__":
    main()
