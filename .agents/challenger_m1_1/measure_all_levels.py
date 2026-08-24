#!/usr/bin/env python3
import sys
import os

# Add the tools directory to path
sys.path.append("/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools")

import verify_compression

def main():
    levels = verify_compression.load_raw_levels(verify_compression.levels_js_path)
    print(f"Loaded {len(levels)} levels.")
    
    total_raw = 0
    total_comp = 0
    
    print(f"{'Level':<6} | {'Raw (Bytes)':<12} | {'RLE (Bytes)':<12} | {'Savings (%)':<12}")
    print("-" * 50)
    
    for idx, raw in enumerate(levels):
        comp = verify_compression.compress_pipeline(raw)
        raw_size = len(raw)
        comp_size = len(comp)
        total_raw += raw_size
        total_comp += comp_size
        savings = (1.0 - (comp_size / raw_size)) * 100
        print(f"{idx:<6d} | {raw_size:<12d} | {comp_size:<12d} | {savings:<11.1f}%")
        
    print("-" * 50)
    print(f"TOTAL  | {total_raw:<12d} | {total_comp:<12d} | {(1.0 - (total_comp / total_raw)) * 100:<11.1f}%")
    
    # Let's calculate running sum to see where 16KB (16384 bytes) bank limit is breached
    running_sum = 0
    limit_breached = False
    for idx, raw in enumerate(levels):
        comp = verify_compression.compress_pipeline(raw)
        running_sum += len(comp)
        print(f"Cumulative size up to Level {idx}: {running_sum} bytes")
        if running_sum > 16384 and not limit_breached:
            print(f"==> BREACHES 16KB BANK LIMIT AT LEVEL {idx}! <==")
            limit_breached = True

if __name__ == "__main__":
    main()
