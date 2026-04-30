"""
add_safety.py

Adds reproducible synthetic safety scores to edges CSV.
Expects 'pune_edges_raw.csv' (u,v,distance_km,key) in current directory.

Writes 'pune_graph.csv' with columns: u,v,distance_km,safety_score,key

Usage:
    python add_safety.py
"""
import os, sys, random
try:
    import pandas as pd
except Exception as e:
    print("ERROR: pandas missing. Run: python -m pip install pandas")
    raise

INPUT = "pune_edges_raw.csv"
OUTPUT = "pune_graph.csv"
SEED = 1337

def main():
    if not os.path.exists(INPUT):
        print(f"ERROR: Input file not found: {INPUT}")
        print("Run extract_pune_edges.py first (it creates pune_edges_raw.csv).")
        sys.exit(1)
    try:
        df = pd.read_csv(INPUT)
    except Exception as e:
        print("ERROR: Could not read CSV:", e)
        sys.exit(1)
    random.seed(SEED)
    # safety 30..95 reproducible
    df['safety_score'] = df.apply(lambda r: random.randint(30,95), axis=1)
    # write with expected columns
    cols = ['u','v','distance_km','safety_score']
    # if 'key' exists, include it
    if 'key' in df.columns:
        cols.append('key')
    df.to_csv(OUTPUT, index=False, columns=cols)
    print(f"[add_safety] Wrote {OUTPUT} ({len(df)} rows). Seed={SEED}")

if __name__ == "__main__":
    main()
