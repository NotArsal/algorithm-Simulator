"""
Quick script to check India OSM download status
"""

import os

# Check both D: drive and local directory
OUTPUT_DIR_D = "D:/navigation_india_osm"
OUTPUT_DIR_LOCAL = "data/india_osm"

# Prefer D: drive
if os.path.exists(OUTPUT_DIR_D):
    OUTPUT_DIR = OUTPUT_DIR_D
    print(f"[INFO] Using D: drive location: {OUTPUT_DIR}")
else:
    OUTPUT_DIR = OUTPUT_DIR_LOCAL
    print(f"[INFO] Using local location: {OUTPUT_DIR}")

OUT_NODES = os.path.join(OUTPUT_DIR, "india_nodes.csv")
OUT_GRAPH = os.path.join(OUTPUT_DIR, "india_graph.csv")

def check_status():
    print("="*60)
    print("India OSM Download Status Check")
    print("="*60)
    
    if not os.path.exists(OUTPUT_DIR):
        print("\n[STATUS] Download directory not created yet.")
        print("         Download is starting or in progress...")
        return
    
    print(f"\nDirectory: {OUTPUT_DIR}")
    
    if os.path.exists(OUT_NODES):
        size = os.path.getsize(OUT_NODES) / (1024 * 1024)  # MB
        print(f"[OK] Nodes file exists: {OUT_NODES}")
        print(f"     Size: {size:.2f} MB")
        
        # Count lines (approximate)
        try:
            with open(OUT_NODES, 'r', encoding='utf-8') as f:
                lines = sum(1 for _ in f) - 1  # Subtract header
            print(f"     Nodes: {lines:,}")
        except:
            print("     (Counting nodes...)")
    else:
        print(f"[WAIT] Nodes file not created yet: {OUT_NODES}")
    
    if os.path.exists(OUT_GRAPH):
        size = os.path.getsize(OUT_GRAPH) / (1024 * 1024)  # MB
        print(f"[OK] Graph file exists: {OUT_GRAPH}")
        print(f"     Size: {size:.2f} MB")
        
        # Count lines (approximate)
        try:
            with open(OUT_GRAPH, 'r', encoding='utf-8') as f:
                lines = sum(1 for _ in f) - 1  # Subtract header
            print(f"     Edges: {lines:,}")
        except:
            print("     (Counting edges...)")
    else:
        print(f"[WAIT] Graph file not created yet: {OUT_GRAPH}")
    
    if os.path.exists(OUT_NODES) and os.path.exists(OUT_GRAPH):
        print("\n" + "="*60)
        print("[SUCCESS] Download appears to be complete!")
        print("="*60)
        print("\nThe server will automatically use this data.")
        print("Restart the server to ensure it picks up the new data.")
    else:
        print("\n[INFO] Download is still in progress...")
        print("       This typically takes 30-60 minutes.")
        print("       Run this script again to check progress.")

if __name__ == '__main__':
    check_status()

