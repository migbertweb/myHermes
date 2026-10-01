#!/usr/bin/env python3
import json, glob, os, sqlite3, datetime

# This script aggregates token usage from the internal state.db
def analyze_usage():
    home = os.path.expanduser("~")
    db_path = os.path.join(home, ".hermes", "state.db")
    if not os.path.exists(db_path):
        print("Error: state.db not found.")
        return

    db = sqlite3.connect(db_path)
    
    print("📊 --- REAL TOKEN USAGE ---")
    cur = db.execute("""
        SELECT 
            COUNT(*) as sessions,
            SUM(input_tokens), SUM(output_tokens), SUM(cache_read_tokens),
            SUM(estimated_cost_usd)
        FROM sessions
    """)
    r = cur.fetchone()
    print(f"Sessions: {r[0]}\nInput: {r[1]:,}\nOutput: {r[2]:,}\nCache Read: {r[3]:,}\nEst. Cost: ${r[4]:.4f}")

    print("\n📅 --- LAST 30 DAYS ---")
    cur = db.execute("""
        SELECT 
            COUNT(*), SUM(input_tokens), SUM(output_tokens), SUM(cache_read_tokens)
        FROM sessions 
        WHERE started_at > strftime('%s', 'now', '-30 days')
    """)
    r30 = cur.fetchone()
    print(f"Sessions: {r30[0]}\nInput: {r30[1]:,}\nOutput: {r30[2]:,}\nCache Read: {r30[3]:,}")
    
    db.close()

if __name__ == "__main__":
    analyze_usage()
