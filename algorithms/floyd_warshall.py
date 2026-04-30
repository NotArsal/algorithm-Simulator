"""
algorithms/floyd_warshall.py
Floyd-Warshall all-pairs shortest path — precomputed at startup.
explored_edges = the final path edges (FW has no frontier; animation
traces the reconstructed path segment by segment).
"""
import time

_fw_state = None


def precompute(graph, nodes):
    global _fw_state
    node_list = sorted(graph.keys())
    n   = len(node_list)
    idx = {nid: i for i, nid in enumerate(node_list)}

    INF  = float('inf')
    dist = [[INF] * n for _ in range(n)]
    nxt  = [[None] * n for _ in range(n)]

    for i in range(n):
        dist[i][i] = 0.0

    for u, neighbors in graph.items():
        if u not in idx:
            continue
        i = idx[u]
        for v, w in neighbors.items():
            if v not in idx:
                continue
            j = idx[v]
            if w < dist[i][j]:
                dist[i][j] = w
                nxt[i][j]  = j

    t0 = time.perf_counter()
    for k in range(n):
        dk = dist[k]
        for i in range(n):
            di = dist[i]
            if di[k] == INF:
                continue
            ni = nxt[i]
            for j in range(n):
                nd = di[k] + dk[j]
                if nd < di[j]:
                    di[j] = nd
                    ni[j] = nxt[i][k]
    t1 = time.perf_counter()

    _fw_state = {
        'dist': dist, 'nxt': nxt, 'idx': idx,
        'node_list': node_list,
        'precompute_ms': round((t1 - t0) * 1000, 2),
        'n': n,
    }
    return _fw_state['precompute_ms']


def query(src_id, dst_id):
    global _fw_state
    if _fw_state is None:
        return {'path': [], 'distance_km': -1, 'time_ms': 0,
                'precompute_ms': 0, 'explored_edges': []}

    t0            = time.perf_counter()
    idx           = _fw_state['idx']
    dist          = _fw_state['dist']
    nxt           = _fw_state['nxt']
    node_list     = _fw_state['node_list']
    precompute_ms = _fw_state['precompute_ms']

    if src_id not in idx or dst_id not in idx:
        return {'path': [], 'distance_km': -1, 'time_ms': 0,
                'precompute_ms': precompute_ms, 'explored_edges': []}

    i, j = idx[src_id], idx[dst_id]
    if dist[i][j] == float('inf'):
        t1 = time.perf_counter()
        return {'path': [], 'distance_km': -1,
                'time_ms': round((t1 - t0) * 1000, 4),
                'precompute_ms': precompute_ms, 'explored_edges': []}

    # Reconstruct path and collect consecutive node pairs as edges
    path = [node_list[i]]
    explored_edges = []
    ci = i
    steps = 0
    while ci != j:
        ni = nxt[ci][j]
        if ni is None:
            path = []
            explored_edges = []
            break
        explored_edges.append((node_list[ci], node_list[ni]))   # path edges for animation
        ci = ni
        path.append(node_list[ci])
        steps += 1
        if steps > _fw_state['n'] + 5:
            path = []
            explored_edges = []
            break

    t1 = time.perf_counter()
    return {
        'path': path,
        'distance_km': round(dist[i][j], 4),
        'time_ms': round((t1 - t0) * 1000, 4),
        'precompute_ms': precompute_ms,
        'explored_edges': explored_edges,
    }
