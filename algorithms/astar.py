"""
algorithms/astar.py
A* Search with Haversine heuristic.
explored_edges shows the guided search tree — far fewer branches than Dijkstra
because the heuristic steers the search toward the destination.
"""
import heapq
import math
import time


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(min(1.0, a)))


def run(graph, nodes, src_id, dst_id):
    t0 = time.perf_counter()

    dst_info = nodes.get(dst_id, {})
    dst_lat  = dst_info.get('lat', 0)
    dst_lon  = dst_info.get('lon', 0)

    def h(nid):
        n = nodes.get(nid, {})
        return haversine_km(n.get('lat', 0), n.get('lon', 0), dst_lat, dst_lon)

    g_cost = {src_id: 0.0}
    prev   = {}
    heap   = [(h(src_id), 0.0, src_id)]
    closed = set()
    explored_edges = []   # (u, v) discovery order

    while heap:
        f, g, u = heapq.heappop(heap)
        if u in closed:
            continue
        closed.add(u)
        if u == dst_id:
            break
        for v, w in graph.get(u, {}).items():
            if v in closed:
                continue
            ng = g + w
            if ng < g_cost.get(v, float('inf')):
                g_cost[v] = ng
                prev[v] = u
                explored_edges.append((u, v))   # u discovers v with lower cost
                heapq.heappush(heap, (ng + h(v), ng, v))

    t1 = time.perf_counter()
    path = _reconstruct(prev, src_id, dst_id)
    distance = g_cost.get(dst_id, float('inf'))
    return {
        'path': path,
        'distance_km': round(distance, 4) if distance != float('inf') else -1,
        'time_ms': round((t1 - t0) * 1000, 4),
        'explored_edges': explored_edges,
    }


def _reconstruct(prev, src_id, dst_id):
    path = []
    cur  = dst_id
    while cur is not None:
        path.append(cur)
        if cur == src_id:
            break
        cur = prev.get(cur)
    path.reverse()
    return path if path and path[0] == src_id else []
