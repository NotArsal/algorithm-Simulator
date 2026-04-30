# server/app.py
# Flask server to run navigation.exe and return last_route.json
# Added: /nodes endpoint that returns a list of nodes from the CSV (label, node_id, lat, lon)
# Added: Energy-efficient route calculation with battery capacity checking
from flask import Flask, request, jsonify, send_from_directory
import subprocess, os, json, shutil, time, csv
import sys

app = Flask(__name__, static_folder='static', template_folder='templates')

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))   # project root
NAV_EXE = os.path.join(ROOT, 'navigation.exe')

# Support both combined and Pune-specific data
COMBINED_GRAPH_CSV = os.path.join(ROOT, 'data', 'combined_graph.csv')
COMBINED_NODES_CSV = os.path.join(ROOT, 'data', 'combined_nodes.csv')
GRAPH_CSV = os.path.join(ROOT, 'data', 'pune_graph.csv')
NODES_CSV = os.path.join(ROOT, 'data', 'pune_nodes.csv')
LAST_ROUTE = os.path.join(ROOT, 'last_route.json')

# Import energy calculator
sys.path.insert(0, ROOT)
try:
    from energy_calculator import calculate_route_energy
except ImportError:
    calculate_route_energy = None

# simple cache for nodes CSV (load on first request)
_NODES_CACHE = None

def find_nav():
    if os.path.exists(NAV_EXE) and os.access(NAV_EXE, os.X_OK):
        return NAV_EXE
    exe = shutil.which('navigation.exe') or shutil.which('navigation')
    return exe

@app.route('/')
def index():
    # Try energy navigation UI first, fallback to original
    energy_nav_path = os.path.join(app.static_folder, 'energy_nav.html')
    if os.path.exists(energy_nav_path):
        return send_from_directory(app.static_folder, 'energy_nav.html')
    index_path = os.path.join(app.static_folder, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(app.static_folder, 'index.html')
    return "UI not present. Place index.html or energy_nav.html into server/static/ or templates/"

@app.route('/energy')
def energy_nav():
    """Direct route to energy-efficient navigation UI"""
    energy_nav_path = os.path.join(app.static_folder, 'energy_nav.html')
    if os.path.exists(energy_nav_path):
        return send_from_directory(app.static_folder, 'energy_nav.html')
    return jsonify({"ok": False, "error": "energy_nav.html not found"}), 404

@app.route('/nodes')
def nodes_endpoint():
    """
    Returns JSON array of nodes read from nodes CSV:
    [ { "label": "...", "node_id": 245645011, "lat": 18.44, "lon": 73.89 }, ... ]
    If a node has no label, we return a fallback label "node_<id> (lat,lon)" so the UI can show something.
    """
    global _NODES_CACHE
    
    # Check if user wants combined data
    use_combined = request.args.get('combined', 'true').lower() == 'true'
    nodes_file = COMBINED_NODES_CSV if (use_combined and os.path.exists(COMBINED_NODES_CSV)) else NODES_CSV
    
    if _NODES_CACHE is not None:
        return jsonify(_NODES_CACHE)

    nodes = []
    if not os.path.exists(nodes_file):
        return jsonify({"ok": False, "error": f"nodes CSV not found: {nodes_file}"}), 404

    try:
        with open(nodes_file, newline='', encoding='utf-8') as fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            # We'll try to find columns: node_id, lat, lon, label (case-insensitive)
            # If header exists, map indices; otherwise assume order node_id,lat,lon,label
            idx_id = idx_lat = idx_lon = idx_label = None
            if header:
                for i,h in enumerate(header):
                    hn = h.strip().lower()
                    if hn in ('node_id','nodeid','id','osmid','osm_id'): idx_id = i
                    elif hn in ('lat','latitude'): idx_lat = i
                    elif hn in ('lon','lng','longitude','long'): idx_lon = i
                    elif hn in ('label','name','place','placename'): idx_label = i
            # fallback defaults
            if idx_id is None: idx_id = 0
            if idx_lat is None: idx_lat = 1
            if idx_lon is None: idx_lon = 2

            for row in reader:
                if len(row) <= max(idx_id, idx_lat, idx_lon):
                    continue
                try:
                    nid = int(row[idx_id].strip())
                except:
                    # skip rows with invalid id
                    continue
                lat = float(row[idx_lat].strip()) if row[idx_lat].strip() else None
                lon = float(row[idx_lon].strip()) if row[idx_lon].strip() else None
                label = None
                if idx_label is not None and idx_label < len(row):
                    label = row[idx_label].strip()
                # fallback label if empty
                if not label or label == '':
                    if lat is not None and lon is not None:
                        label = f"node_{nid} ({lat:.6f},{lon:.6f})"
                    else:
                        label = f"node_{nid}"
                nodes.append({"label": label, "node_id": nid, "lat": lat, "lon": lon})
    except Exception as e:
        return jsonify({"ok": False, "error": f"failed to read nodes CSV: {str(e)}"}), 500

    # Optionally: sort alphabetically by label for nicer dropdowns
    nodes.sort(key=lambda x: x["label"].lower() if x.get("label") else "")

    # cache (memory) for subsequent calls
    _NODES_CACHE = nodes
    return jsonify(nodes)

@app.route('/route', methods=['POST'])
def compute_route():
    body = request.get_json(force=True, silent=True)
    if not body:
        return jsonify({"ok": False, "error": "invalid json"}), 400

    src = str(body.get('src', '')).strip()
    dst = str(body.get('dst', '')).strip()
    mode = int(body.get('mode', 1))
    
    # Energy calculation parameters
    vehicle_type = body.get('vehicle_type', 'drone')  # 'drone' or 'ground_bot'
    battery_capacity_wh = body.get('battery_capacity_wh', None)  # Optional battery capacity
    use_combined = body.get('use_combined', True)  # Use combined data (mountain, rural, Pune)

    if not src or not dst:
        return jsonify({"ok": False, "error": "missing src or dst"}), 400

    nav = find_nav()
    if not nav:
        return jsonify({"ok": False, "error": "navigation.exe not found"}), 500

    # Choose data files based on vehicle type
    # Priority: India OSM > Road-based combined > Combined > Pune only
    # Check both D: drive and local data directory
    INDIA_GRAPH_D = "D:/navigation_india_osm/india_graph.csv"
    INDIA_NODES_D = "D:/navigation_india_osm/india_nodes.csv"
    INDIA_GRAPH_LOCAL = os.path.join(ROOT, 'data', 'india_osm', 'india_graph.csv')
    INDIA_NODES_LOCAL = os.path.join(ROOT, 'data', 'india_osm', 'india_nodes.csv')
    
    # Prefer D: drive, fallback to local
    INDIA_GRAPH = INDIA_GRAPH_D if os.path.exists(INDIA_GRAPH_D) else INDIA_GRAPH_LOCAL
    INDIA_NODES = INDIA_NODES_D if os.path.exists(INDIA_NODES_D) else INDIA_NODES_LOCAL
    road_graph = os.path.join(ROOT, 'data', 'combined_road_graph.csv')
    road_nodes = os.path.join(ROOT, 'data', 'combined_road_nodes.csv')
    
    if vehicle_type == 'ground_bot':
        # For ground bots, MUST use road-based graphs (OSM data only)
        # DO NOT use combined_graph.csv as it has direct paths, not roads
        # Priority: India OSM > Road-based combined > Pune OSM (always road-based)
        if use_combined and os.path.exists(INDIA_GRAPH) and os.path.exists(INDIA_NODES):
            # Use full India OSM data if available (best option)
            graph_file = INDIA_GRAPH
            nodes_file = INDIA_NODES
        elif use_combined and os.path.exists(road_graph) and os.path.exists(road_nodes):
            # Use road-based combined graph
            graph_file = road_graph
            nodes_file = road_nodes
        else:
            # ALWAYS use Pune OSM for ground bots (it's road-based from OSM)
            # Pune graph is from OSM and represents actual roads
            graph_file = GRAPH_CSV  # Pune graph is OSM road-based
            nodes_file = NODES_CSV  # Pune nodes
    else:
        # For drones, can use any graph (prefer India OSM for coverage)
        if use_combined and os.path.exists(INDIA_GRAPH) and os.path.exists(INDIA_NODES):
            graph_file = INDIA_GRAPH
            nodes_file = INDIA_NODES
        elif use_combined and os.path.exists(COMBINED_GRAPH_CSV) and os.path.exists(COMBINED_NODES_CSV):
            graph_file = COMBINED_GRAPH_CSV
            nodes_file = COMBINED_NODES_CSV
        else:
            graph_file = GRAPH_CSV
            nodes_file = NODES_CSV

    cmd = [
        nav,
        "--graph", graph_file,
        "--nodes", nodes_file,
        "--src", src,
        "--dst", dst,
        "--mode", str(mode)
    ]

    try:
        t0 = time.time()
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=25)
        elapsed = time.time() - t0
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        retcode = proc.returncode
    except subprocess.TimeoutExpired as e:
        return jsonify({"ok": False, "error": "navigation timed out", "detail": str(e)}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": "failed to run navigation", "detail": str(e)}), 500

    route_json = None
    if os.path.exists(LAST_ROUTE):
        try:
            with open(LAST_ROUTE, 'r', encoding='utf-8') as fh:
                route_json = json.load(fh)
        except Exception as e:
            route_json = {"_error_reading_last_route": str(e)}

    # Calculate energy consumption if route is available
    energy_data = None
    if route_json and calculate_route_energy:
        try:
            energy_data = calculate_route_energy(
                route_json, 
                vehicle_type=vehicle_type,
                battery_capacity_wh=battery_capacity_wh
            )
        except Exception as e:
            energy_data = {"error": str(e)}

    result = {
        "ok": (retcode == 0),
        "exec": {
            "cmd": cmd,
            "returncode": retcode,
            "elapsed_s": elapsed,
            "stdout": stdout,
            "stderr": stderr
        },
        "route": route_json,
        "energy": energy_data
    }
    status = 200 if retcode == 0 else 500
    return jsonify(result), status

@app.route('/last_route.json')
def serve_last_route():
    if os.path.exists(LAST_ROUTE):
        return send_from_directory(ROOT, 'last_route.json')
    return jsonify({"ok": False, "error": "last_route.json not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
