"""
app.py  —  Shortest Path Algorithm Simulator
Flask backend for the Advanced Data Structures course project.
"""
from flask import Flask, request, jsonify, render_template
import os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from graph_loader import get_subgraph
from algorithms import dijkstra, astar, bellman_ford, floyd_warshall

app = Flask(__name__,
            template_folder=os.path.join(ROOT, 'templates'),
            static_folder=os.path.join(ROOT, 'static'))

# ── Startup ────────────────────────────────────────────────────
print("=" * 55)
print("  Shortest Path Algorithm Simulator — Startup")
print("=" * 55)

sub_nodes, sub_graph, seed_id = get_subgraph()

# Assign human-readable sequential numbers to each node
# Sort by lat then lon so numbering is geographically ordered
_sorted_ids = sorted(sub_nodes.keys(),
                     key=lambda n: (sub_nodes[n]['lat'], sub_nodes[n]['lon']))
NODE_NUMBERS = {nid: i + 1 for i, nid in enumerate(_sorted_ids)}  # node_id → #

print(f"[app] Seed node: {seed_id} (Node #{NODE_NUMBERS.get(seed_id, '?')})")
print(f"[app] Precomputing Floyd-Warshall on {len(sub_nodes)} nodes...")
fw_precompute_ms = floyd_warshall.precompute(sub_graph, sub_nodes)
print(f"[app] Floyd-Warshall ready in {fw_precompute_ms} ms")
print("[app] Server ready.  Open http://localhost:5000")
print("=" * 55)


# ── Routes ─────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/graph')
def graph_endpoint():
    """Return all subgraph nodes with sequential node numbers."""
    nodes_list = [
        {
            'node_id':    nid,
            'node_num':   NODE_NUMBERS[nid],
            'lat':        info['lat'],
            'lon':        info['lon'],
        }
        for nid, info in sub_nodes.items()
    ]
    return jsonify({'nodes': nodes_list, 'seed_id': seed_id})


@app.route('/route', methods=['POST'])
def route_endpoint():
    """
    Run selected algorithms on src→dst.
    Body: { "src": node_id, "dst": node_id, "algorithms": ["dijkstra", "astar", ...] }
    Response: { ok, results: { <algo>: { path, distance_km, time_ms,
                explored_nodes, coordinates, explored_coordinates } } }
    """
    body = request.get_json(force=True, silent=True)
    if not body:
        return jsonify({'ok': False, 'error': 'Invalid JSON body'}), 400

    try:
        src = int(body['src'])
        dst = int(body['dst'])
    except (KeyError, TypeError, ValueError):
        return jsonify({'ok': False, 'error': 'src and dst must be integer node IDs'}), 400

    requested = body.get('algorithms', ['dijkstra', 'astar', 'bellman_ford', 'floyd_warshall'])
    valid_algos = {'dijkstra', 'astar', 'bellman_ford', 'floyd_warshall'}
    requested = [a for a in requested if a in valid_algos]

    if not requested:
        return jsonify({'ok': False, 'error': 'No valid algorithms specified'}), 400
    if src not in sub_nodes:
        return jsonify({'ok': False, 'error': f'src node {src} not in subgraph'}), 400
    if dst not in sub_nodes:
        return jsonify({'ok': False, 'error': f'dst node {dst} not in subgraph'}), 400
    if src == dst:
        return jsonify({'ok': False, 'error': 'Source and destination are the same node'}), 400

    runners = {
        'dijkstra':       lambda: dijkstra.run(sub_graph, sub_nodes, src, dst),
        'astar':          lambda: astar.run(sub_graph, sub_nodes, src, dst),
        'bellman_ford':   lambda: bellman_ford.run(sub_graph, sub_nodes, src, dst),
        'floyd_warshall': lambda: floyd_warshall.query(src, dst),
    }

    def node_coord(nid):
        n = sub_nodes.get(nid)
        return {'lat': n['lat'], 'lon': n['lon']} if n else None

    results = {}
    for algo in requested:
        r = runners[algo]()

        # Path coordinates for the final bright polyline
        r['coordinates'] = [
            node_coord(n) for n in r.get('path', [])
            if n in sub_nodes
        ]

        # Explored edges: list of {from_lat,from_lon,to_lat,to_lon}
        # Each entry is one edge drawn during animation (u discovers/relaxes v)
        edge_coords = []
        for (u, v) in r.get('explored_edges', []):
            un = sub_nodes.get(u)
            vn = sub_nodes.get(v)
            if un and vn:
                edge_coords.append({
                    'from_lat': un['lat'], 'from_lon': un['lon'],
                    'to_lat':   vn['lat'], 'to_lon':   vn['lon'],
                })
        r['explored_edge_coords'] = edge_coords
        r.pop('explored_edges', None)   # don't send raw IDs to client

        results[algo] = r


    return jsonify({'ok': True, 'results': results})


if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)
