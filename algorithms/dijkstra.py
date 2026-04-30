"""
algorithms/dijkstra.py
Classic Dijkstra using a binary min-heap.
Returns explored_edges: list of (u, v) pairs in the order the algorithm
first discovers/updates a path — these form the search tree for animation.
"""
import heapq
import time


def run(graph, nodes, src_id, dst_id):
    t0 = time.perf_counter()

    dist = {node: float('inf') for node in graph}
    prev = {node: None for node in graph}
    dist[src_id] = 0
    heap = [(0.0, src_id)]
    visited = set()
    explored_edges = []   # (u, v) discovery order — forms the search tree

    while heap:
        d, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        if u == dst_id:
            break
        for v, w in graph.get(u, {}).items():
            if v in visited:
                continue
            if v not in dist:
                dist[v] = float('inf')
                prev[v] = None
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                explored_edges.append((u, v))   # u found a better path to v
                heapq.heappush(heap, (nd, v))

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
    cur = dst_id
    while cur is not None:
        path.append(cur)
        if cur == src_id:
            break
        cur = prev.get(cur)
    path.reverse()
    return path if path and path[0] == src_id else []
