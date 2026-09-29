"""
graph_loader.py
Loads the real Pune OSM road network from CSV files and extracts a
dense connected subgraph of ~200 nodes via BFS from Pune city center.
All 4 algorithms operate on this same subgraph.
"""
import csv
import os
from collections import deque

ROOT = os.path.dirname(os.path.abspath(__file__))
NODES_CSV = os.path.join(ROOT, 'data', 'pune_nodes.csv')
GRAPH_CSV = os.path.join(ROOT, 'data', 'pune_graph.csv')

# Pune city center (Shivaji Nagar / FC Road area)
SEED_LAT = 18.5204
SEED_LON = 73.8567
SUBGRAPH_SIZE = 500  # Floyd-Warshall is O(N^3); ~1s startup at this size, ~5.5s at 800, ~19s at 1200

_subgraph_cache = None


def load_full_graph():
    """Read all nodes and edges from CSV files into memory."""
    nodes = {}
    with open(NODES_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                nid = int(row['node_id'])
                lat = float(row['lat'])
                lon = float(row['lon'])
                label = row.get('label', '').strip()
                nodes[nid] = {
                    'lat': lat,
                    'lon': lon,
                    'label': label if label else f'{lat:.5f}, {lon:.5f}'
                }
            except (ValueError, KeyError):
                continue

    graph = {}  # adjacency list: {u: {v: dist_km}}
    with open(GRAPH_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                u = int(row['u'])
                v = int(row['v'])
                dist = float(row['distance_km'])
                if dist <= 0:
                    continue
                if u not in graph:
                    graph[u] = {}
                # Keep shortest edge if duplicates exist
                if v not in graph[u] or dist < graph[u][v]:
                    graph[u][v] = dist
            except (ValueError, KeyError):
                continue

    return nodes, graph


def find_seed_node(nodes):
    """Return the node ID closest to Pune city center."""
    best_id = None
    best_dist = float('inf')
    for nid, info in nodes.items():
        d = (info['lat'] - SEED_LAT) ** 2 + (info['lon'] - SEED_LON) ** 2
        if d < best_dist:
            best_dist = d
            best_id = nid
    return best_id


def _dijkstra_reachable(sub_graph, src_id):
    """Return set of nodes reachable from src_id via directed edges."""
    import heapq
    dist = {src_id: 0.0}
    heap = [(0.0, src_id)]
    visited = set()
    while heap:
        d, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        for v, w in sub_graph.get(u, {}).items():
            nd = d + w
            if nd < dist.get(v, float('inf')):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return visited


def extract_subgraph(nodes, graph, seed_id, size=SUBGRAPH_SIZE):
    """
    BFS from seed_id to collect ~size nodes, then prune to those
    actually reachable FROM seed via directed edges so all algorithms
    can always find a valid path from seed.
    """
    visited = set()
    queue = deque([seed_id])
    visited.add(seed_id)

    while queue and len(visited) < size:
        node = queue.popleft()
        for neighbor in graph.get(node, {}):
            if neighbor not in visited and neighbor in nodes:
                visited.add(neighbor)
                queue.append(neighbor)
                if len(visited) >= size:
                    break

    sub_nodes = {nid: nodes[nid] for nid in visited if nid in nodes}
    sub_graph = {}
    for u in visited:
        neighbors = {v: w for v, w in graph.get(u, {}).items() if v in visited}
        if neighbors:
            sub_graph[u] = neighbors

    # Prune to nodes reachable from seed so there are no dead-ends in demos
    reachable = _dijkstra_reachable(sub_graph, seed_id)
    sub_nodes = {nid: info for nid, info in sub_nodes.items() if nid in reachable}
    sub_graph = {
        u: {v: w for v, w in nbrs.items() if v in reachable}
        for u, nbrs in sub_graph.items()
        if u in reachable
    }
    sub_graph = {u: nbrs for u, nbrs in sub_graph.items() if nbrs}

    return sub_nodes, sub_graph, seed_id


def get_subgraph():
    """Cached accessor — loads and extracts subgraph only once.
    Returns (sub_nodes, sub_graph, seed_id).
    """
    global _subgraph_cache
    if _subgraph_cache is None:
        print("[graph_loader] Reading CSV files...")
        nodes, graph = load_full_graph()
        seed = find_seed_node(nodes)
        print(f"[graph_loader] Seed node: {seed} at {nodes[seed]}")
        sub_nodes, sub_graph, seed_id = extract_subgraph(nodes, graph, seed)
        print(f"[graph_loader] Subgraph: {len(sub_nodes)} nodes, "
              f"{sum(len(v) for v in sub_graph.values())} edges "
              f"(all reachable from seed)")
        _subgraph_cache = (sub_nodes, sub_graph, seed_id)
    return _subgraph_cache
