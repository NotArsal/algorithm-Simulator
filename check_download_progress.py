"""
Check India OSM download progress with percentage
"""

import os
import time

OUTPUT_DIR_D = "D:/navigation_india_osm"
OUTPUT_DIR_LOCAL = "data/india_osm"

# Total cities being downloaded
TOTAL_CITIES = 30

def get_file_size_mb(filepath):
    """Get file size in MB"""
    if os.path.exists(filepath):
        return os.path.getsize(filepath) / (1024 * 1024)
    return 0

def count_lines(filepath):
    """Count lines in file (excluding header)"""
    if not os.path.exists(filepath):
        return 0
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f) - 1  # Subtract header
    except:
        return 0

def estimate_progress():
    """Estimate download progress based on file sizes"""
    # Typical sizes (approximate)
    # Each major city: ~50-200 MB for graph, ~10-50 MB for nodes
    # Total expected: ~1-2 GB for graph, ~300-500 MB for nodes
    
    expected_graph_size_mb = 1500  # 1.5 GB
    expected_nodes_size_mb = 400   # 400 MB
    
    if os.path.exists(OUTPUT_DIR_D):
        output_dir = OUTPUT_DIR_D
    elif os.path.exists(OUTPUT_DIR_LOCAL):
        output_dir = OUTPUT_DIR_LOCAL
    else:
        return 0, "Download not started"
    
    graph_file = os.path.join(output_dir, "india_graph.csv")
    nodes_file = os.path.join(output_dir, "india_nodes.csv")
    
    graph_size = get_file_size_mb(graph_file)
    nodes_size = get_file_size_mb(nodes_file)
    
    # Estimate based on file sizes
    graph_progress = min(100, (graph_size / expected_graph_size_mb) * 100)
    nodes_progress = min(100, (nodes_size / expected_nodes_size_mb) * 100)
    
    # Average progress
    overall_progress = (graph_progress + nodes_progress) / 2
    
    # Count actual nodes/edges if files exist
    nodes_count = count_lines(nodes_file)
    edges_count = count_lines(graph_file)
    
    status = "Downloading"
    if nodes_count > 0 and edges_count > 0:
        status = f"Processing ({nodes_count:,} nodes, {edges_count:,} edges)"
    elif graph_size > 0 or nodes_size > 0:
        status = "Downloading..."
    
    return overall_progress, status, graph_size, nodes_size, nodes_count, edges_count

def check_progress():
    print("="*70)
    print("India OSM Download Progress")
    print("="*70)
    
    # Check which location
    if os.path.exists(OUTPUT_DIR_D):
        output_dir = OUTPUT_DIR_D
        print(f"\n[LOCATION] D: drive: {output_dir}")
    elif os.path.exists(OUTPUT_DIR_LOCAL):
        output_dir = OUTPUT_DIR_LOCAL
        print(f"\n[LOCATION] Local: {output_dir}")
    else:
        print("\n[STATUS] Download directory not found.")
        print("         Download may not have started yet.")
        return
    
    # Get progress
    progress, status, graph_size, nodes_size, nodes_count, edges_count = estimate_progress()
    
    print(f"\n[PROGRESS] {progress:.1f}%")
    print(f"[STATUS]  {status}")
    
    # Progress bar (ASCII-safe)
    bar_length = 50
    filled = int(bar_length * progress / 100)
    bar = "#" * filled + "-" * (bar_length - filled)
    print(f"\n[{bar}] {progress:.1f}%")
    
    # File details
    print(f"\n[FILES]")
    graph_file = os.path.join(output_dir, "india_graph.csv")
    nodes_file = os.path.join(output_dir, "india_nodes.csv")
    
    if os.path.exists(nodes_file):
        print(f"  [OK] Nodes: {nodes_size:.2f} MB ({nodes_count:,} nodes)")
    else:
        print(f"  [WAIT] Nodes: Not created yet")
    
    if os.path.exists(graph_file):
        print(f"  [OK] Graph: {graph_size:.2f} MB ({edges_count:,} edges)")
    else:
        print(f"  [WAIT] Graph: Not created yet")
    
    # Time estimate
    if progress > 0 and progress < 100:
        # Rough estimate: assume linear progress
        # This is very approximate
        print(f"\n[ESTIMATE] Approximately {100-progress:.0f}% remaining")
        print(f"          Estimated time: 20-40 minutes (varies by connection)")
    
    if progress >= 100:
        print("\n" + "="*70)
        print("[SUCCESS] Download Complete!")
        print("="*70)
        print("\nThe server will automatically use this data.")
        print("You may need to restart the server to pick up the new data.")
    
    print("\n" + "="*70)

if __name__ == '__main__':
    check_progress()

