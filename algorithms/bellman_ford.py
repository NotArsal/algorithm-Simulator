"""
algorithms/bellman_ford.py
Bellman-Ford: relaxes all edges (V-1) times.
explored_edges records every relaxation where a shorter path is found —
this produces a wave-like pattern across the graph (characteristic of BF).
"""
import time


def run(graph, nodes, src_id, dst_id):
    t0 = time.perf_counter()

    all_nodes = list(graph.keys())
    if dst_id not in graph:
        all_nodes.append(dst_id)

    dist = {n: float('inf') for n in all_nodes}
    prev = {n: None for n in all_nodes}
    dist[src_id] = 0.0

    edges = []
    for u, neighbors in graph.items():
        for v, w in neighbors.items():
            edges.append((u, v, w))

    V = len(all_nodes)
    explored_edges = []   # (u, v) whenever a relaxation improves the path to v

    for iteration in range(V - 1):
        updated = False
        for u, v, w in edges:
            if dist.get(u, float('inf')) + w < dist.get(v, float('inf')):
                dist[v] = dist[u] + w
                prev[v] = u
                updated = True
                explored_edges.append((u, v))   # relaxation: u improves path to v
        if not updated:
            break

    t1 = time.perf_counter()
    path = _reconstruct(prev, src_id, dst_id)
    distance = dist.get(dst_id, float('inf'))
    return {
        'path': path,
        'distance_km': round(distance, 4) if distance != float('inf') else -1,
        'time_ms': round((t1 - t0) * 1000, 4),
        'explored_edges': explored_edges,
    }


def _reconstruct(prev, src_id, dst_id):
    path = []
    cur  = dst_id
    seen = set()
    while cur is not None:
        if cur in seen:
            return []
        seen.add(cur)
        path.append(cur)
        if cur == src_id:
            break
        cur = prev.get(cur)
    path.reverse()
    return path if path and path[0] == src_id else []
