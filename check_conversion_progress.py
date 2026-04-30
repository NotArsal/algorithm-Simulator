"""
Check conversion progress of PBF to CSV
"""
import os
import time

PBF_FILE = "D:/navigation_india_osm/india-251108.osm.pbf"
OUTPUT_DIR = "D:/navigation_india_osm"
OUT_NODES = os.path.join(OUTPUT_DIR, "india_nodes.csv")
OUT_GRAPH = os.path.join(OUTPUT_DIR, "india_graph.csv")

def get_file_size_mb(filepath):
    """Get file size in MB"""
    if os.path.exists(filepath):
        return os.path.getsize(filepath) / (1024 * 1024)
    return 0

def count_lines(filepath):
    """Count lines in file"""
    if not os.path.exists(filepath):
        return 0
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f) - 1  # Subtract header
    except:
        return 0

def check_progress():
    print("="*70)
    print("Conversion Progress Check")
    print("="*70)
    
    # Check PBF file
    if os.path.exists(PBF_FILE):
        pbf_size = get_file_size_mb(PBF_FILE)
        print(f"\n[PBF FILE] {PBF_FILE}")
        print(f"  Size: {pbf_size:.2f} MB ({pbf_size/1024:.2f} GB)")
    else:
        print(f"\n[ERROR] PBF file not found: {PBF_FILE}")
        return
    
    print(f"\n[OUTPUT FILES]")
    
    # Check nodes file
    if os.path.exists(OUT_NODES):
        nodes_size = get_file_size_mb(OUT_NODES)
        nodes_count = count_lines(OUT_NODES)
        print(f"  [OK] Nodes CSV: {nodes_size:.2f} MB")
        print(f"       Nodes: {nodes_count:,}")
    else:
        print(f"  [WAIT] Nodes CSV: Not created yet")
    
    # Check graph file
    if os.path.exists(OUT_GRAPH):
        graph_size = get_file_size_mb(OUT_GRAPH)
        edges_count = count_lines(OUT_GRAPH)
        print(f"  [OK] Graph CSV: {graph_size:.2f} MB")
        print(f"       Edges: {edges_count:,}")
    else:
        print(f"  [WAIT] Graph CSV: Not created yet")
    
    # Status
    if os.path.exists(OUT_NODES) and os.path.exists(OUT_GRAPH):
        nodes_size = get_file_size_mb(OUT_NODES)
        graph_size = get_file_size_mb(OUT_GRAPH)
        if nodes_size > 10 and graph_size > 10:  # Reasonable minimum
            print("\n" + "="*70)
            print("[SUCCESS] Conversion appears complete!")
            print("="*70)
            print("\nThe server will automatically use these files.")
        else:
            print("\n[INFO] Files exist but may still be writing...")
            print("       Check again in a few minutes.")
    else:
        print("\n[INFO] Conversion in progress...")
        print("       This takes 25-50 minutes for a 1.5 GB file.")
        print("       Check again in a few minutes.")
    
    print("\n" + "="*70)

if __name__ == '__main__':
    check_progress()

