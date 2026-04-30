# diagnose_route_geom.py
import json, os, sys

NAV_DIR = r"C:\Users\rauna\navigation"
DATA_DIR = os.path.join(NAV_DIR, "data")
LAST_ROUTE = os.path.join(NAV_DIR, "last_route.json")
EDGES_GEOM = os.path.join(DATA_DIR, "edges_geom.json")
NODES_CSV = os.path.join(DATA_DIR, "pune_nodes.csv")

def load_json(p):
    try:
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR reading {p}: {e}")
        return None

route = load_json(LAST_ROUTE)
if route is None:
    print("No last_route.json found or failed to parse. Aborting.")
    sys.exit(2)

eg = load_json(EDGES_GEOM)
if eg is None:
    print("edges_geom.json not found or failed to parse. That's likely why polylines are not available.")
    eg = {}

# quick prints
print("===== last_route.json quick summary =====")
print("nodes count:", len(route.get("nodes",[])))
if route.get("nodes"):
    print("first node sample:", route["nodes"][0])
print("edges count:", len(route.get("edges",[])))
if route.get("edges"):
    print("first edge sample:", route["edges"][0])

# find first edge and test lookup
if not route.get("edges"):
    print("No edges in last_route.json — routing may have failed.")
    sys.exit(0)

first_edge = route["edges"][0]
f = first_edge.get("from")
t = first_edge.get("to")
print("\nChecking geometry lookup for first edge:")
print("edge from:", f, "type:", type(f))
print("edge to  :", t, "type:", type(t))

# Build possible keys
keys_to_try = []
# ensure we try both string and int forms
keys_to_try.append(f"{f}|{t}")
keys_to_try.append(f"{int(f)}|{int(t)}" if isinstance(f, (int,float)) or (isinstance(f,str) and f.isdigit()) else None)
keys_to_try = [k for k in keys_to_try if k]

print("Keys to try in edges_geom.json:", keys_to_try[:5])

found = False
for k in keys_to_try:
    if k in eg and eg[k]:
        print(f"Found geometry for key {k} : length {len(eg[k])} points")
        found = True
        break

if not found:
    # try flipped order
    kflip = f"{t}|{f}"
    print("Not found. Trying flipped key:", kflip)
    if kflip in eg and eg[kflip]:
        print(f"Found geometry for flipped key {kflip} : length {len(eg[kflip])} points")
        found = True

if not found:
    print("\nRESULT: No matching edge geometry found for the first route edge.")
    print("Possible causes:")
    print(" - last_route.json 'from'/'to' are *internal indices* (0..N-1), but edges_geom.json keys are OSM node IDs.")
    print(" - last_route.json 'from'/'to' are OSM IDs but formatting differs (strings vs ints).")
    print(" - edges_geom.json uses different node id space (e.g., you used a different graph extract).")
    # show some example keys from edges_geom.json to compare
    print("\nExample keys present in edges_geom.json (first 10):")
    cnt = 0
    for k in list(eg.keys())[:10]:
        print(" ", k)
        cnt += 1
    if cnt == 0:
        print(" (edges_geom.json appears empty)")
    print("\nNext suggestions:")
    print(" - Inspect last_route.json nodes[].node_id values and compare to keys in edges_geom.json.")
    print(" - If last_route.json edges 'from'/'to' are small sequential integers, we need to map them to OSM IDs.")
    sys.exit(0)

# ALSO check that nodes[] in last_route.json have lat/lon
print("\nChecking node coordinates in last_route.json:")
missing_coords = 0
for n in route.get("nodes",[]):
    lat = n.get("lat")
    lon = n.get("lon")
    nid = n.get("node_id")
    if lat is None or lon is None or (lat==0 and lon==0):
        print(" node missing coords:", nid, n)
        missing_coords += 1
print("Total nodes missing coords:", missing_coords)
if missing_coords > 0:
    print("If nodes have no coords, the frontend cannot draw polylines from nodes. Make sure your navigation program wrote lat/lon into last_route.json (nodes[].lat /.lon).")
else:
    print("Nodes have coordinates — good.")

print("\nDIAGNOSTIC COMPLETE.")
