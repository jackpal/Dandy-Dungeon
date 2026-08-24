#!/usr/bin/env python3
"""
verify_compression.py - Automated ROM Build and Size Verification Pipeline
Milestone 1 Foundation

This script:
1. Automatically cleans and compiles the GameBoy ROM using lcc (make clean && make).
2. Asserts that the compiled ROM bin/dandy.gb exists and is exactly 32,768 bytes (32KB flat).
3. Parses the linker map file (dandy.map) to extract and sum up all active code
   and data segments, classifying them into ROM, WRAM, HRAM, or VRAM.
4. Asserts that the active ROM segment footprint is under 28KB (28,672 bytes).
5. Runs a round-trip compression/decompression fidelity check on all 26 levels.
"""

import os
import sys
import re
import subprocess

# Paths relative to the dandy-gb directory
current_dir = os.path.dirname(os.path.abspath(__file__))
dandy_gb_dir = os.path.normpath(os.path.join(current_dir, ".."))
rom_path = os.path.join(dandy_gb_dir, "bin", "dandy.gb")
map_path = os.path.join(dandy_gb_dir, "dandy.map")
levels_js_path = os.path.join(dandy_gb_dir, "../dandy-js/levels.js")

def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_success(message):
    print(f"\033[92m✔ SUCCESS: {message}\033[0m")

def print_failure(message):
    print(f"\033[91m✘ FAILURE: {message}\033[0m")

# ==============================================================================
# 1. Level Round-Trip Fidelity Check
# ==============================================================================
ENCODING = " *DudKF$i123mnop"

def char_to_tile_id(c):
    try:
        return ENCODING.index(c)
    except ValueError:
        return 0

def compress_level(tile_ids):
    compressed = []
    i = 0
    n = len(tile_ids)
    while i < n:
        tile = tile_ids[i]
        run_len = 1
        while i + run_len < n and tile_ids[i + run_len] == tile and run_len < 255:
            run_len += 1
        
        if run_len >= 4:
            compressed.extend([255, run_len, tile])
            i += run_len
        else:
            compressed.append(tile)
            i += 1
    return compressed

def decompress_level(compressed_tiles):
    decompressed = []
    i = 0
    n = len(compressed_tiles)
    while i < n:
        byte = compressed_tiles[i]
        if byte == 255:
            if i + 2 >= n:
                raise ValueError("Malformed RLE stream: truncated run-length encoding")
            run_len = compressed_tiles[i+1]
            tile = compressed_tiles[i+2]
            decompressed.extend([tile] * run_len)
            i += 3
        else:
            decompressed.append(byte)
            i += 1
    return decompressed

def run_round_trip_check():
    print_header("1. Level Compression Round-Trip Fidelity Check")
    
    if not os.path.exists(levels_js_path):
        print_failure(f"levels.js not found at {levels_js_path}")
        return False
        
    print(f"Reading levels from {levels_js_path}...")
    with open(levels_js_path, "r") as f:
        content = f.read()
    
    all_strings = re.findall(r'"([^"]*)"', content)
    level_rows = [s for s in all_strings if len(s) == 60]
    
    levels = []
    for i in range(0, len(level_rows), 30):
        levels.append(level_rows[i:i+30])
        
    print(f"Found {len(levels)} levels. Performing round-trip checks...")
    
    for l_idx, lvl in enumerate(levels):
        flat_tiles = []
        for row in lvl:
            flat_tiles.extend([char_to_tile_id(c) for c in row])
            while len(flat_tiles) % 60 != 0:
                flat_tiles.append(0)
                
        compressed = compress_level(flat_tiles)
        decompressed = decompress_level(compressed)
        
        if decompressed != flat_tiles:
            print_failure(f"Level {l_idx} failed round-trip compression fidelity check!")
            return False
            
    print_success(f"All {len(levels)} levels passed round-trip RLE compression/decompression with 100% fidelity.")
    return True

# ==============================================================================
# 2. Compile ROM
# ==============================================================================
def compile_rom():
    print_header("2. Compiling ROM (make clean && make)")
    
    # Run make clean
    print("Running 'make clean'...")
    clean_res = subprocess.run(["make", "clean"], cwd=dandy_gb_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if clean_res.returncode != 0:
        print_failure("make clean failed:")
        print(clean_res.stderr.decode())
        return False
        
    # Run make
    print("Running 'make'...")
    build_res = subprocess.run(["make"], cwd=dandy_gb_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if build_res.returncode != 0:
        print_failure("make build failed:")
        print(build_res.stderr.decode())
        return False
        
    print_success("ROM compiled successfully.")
    return True

# ==============================================================================
# 3. Assert ROM Size
# ==============================================================================
def verify_rom_size():
    print_header("3. Verifying ROM Size (bin/dandy.gb)")
    
    if not os.path.exists(rom_path):
        print_failure(f"Compiled ROM not found at {rom_path}")
        return False
        
    rom_size = os.path.getsize(rom_path)
    expected_size = 32768  # 32KB
    
    print(f"ROM Path: {rom_path}")
    print(f"ROM Size: {rom_size} bytes ({rom_size / 1024:.2f} KB)")
    
    if rom_size != expected_size:
        print_failure(f"ROM size is {rom_size} bytes, but MUST be exactly {expected_size} bytes (32KB flat).")
        return False
        
    print_success(f"ROM size is exactly {expected_size} bytes.")
    return True

# ==============================================================================
# 4. Parse Map File & Analyze Segments
# ==============================================================================
def analyze_segments():
    print_header("4. Linker Map File Segment Analysis (dandy.map)")
    
    if not os.path.exists(map_path):
        print_failure(f"Linker map file not found at {map_path}")
        return False
        
    print(f"Parsing {map_path}...")
    
    # Read map file contents
    with open(map_path, "r") as f:
        map_content = f.read()
        
    # Regex to match area entries:
    # E.g.: _CODE                              00000200   00001E4A =   7754 bytes (R/O  CODE)
    area_pattern = re.compile(
        r'^\s*([_A-Za-z0-9]+)\s+([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+=\s+(\d+)\s+bytes',
        re.MULTILINE
    )
    
    matches = area_pattern.findall(map_content)
    
    if not matches:
        print_failure("No active segments found in map file. Verify map file format.")
        return False
        
    rom_segments = []
    wram_segments = []
    hram_segments = []
    vram_segments = []
    other_segments = []
    
    print(f"{'Segment Name':<20} | {'Start Addr':<10} | {'Size (Hex)':<10} | {'Size (Bytes)':<12} | {'Memory Region':<12}")
    print("-" * 74)
    
    for name, addr_hex, size_hex, size_bytes_str in matches:
        addr = int(addr_hex, 16)
        size = int(size_bytes_str)
        if size == 0:
            continue
            
        region = "Unknown"
        if 0x0000 <= addr < 0x8000:
            region = "ROM"
            rom_segments.append((name, addr, size))
        elif 0x8000 <= addr < 0xA000:
            region = "VRAM"
            vram_segments.append((name, addr, size))
        elif 0xC000 <= addr < 0xE000:
            region = "WRAM"
            wram_segments.append((name, addr, size))
        elif 0xFF80 <= addr <= 0xFFFE:
            region = "HRAM"
            hram_segments.append((name, addr, size))
        else:
            other_segments.append((name, addr, size))
            
        print(f"{name:<20} | 0x{addr:04X}{' ':<4} | 0x{size:04X}{' ':<4} | {size:<12d} | {region:<12}")
        
    total_rom = sum(size for _, _, size in rom_segments)
    total_wram = sum(size for _, _, size in wram_segments)
    total_hram = sum(size for _, _, size in hram_segments)
    total_vram = sum(size for _, _, size in vram_segments)
    
    print("-" * 74)
    print(f"TOTAL ACTIVE ROM FOOTPRINT:  {total_rom:6d} Bytes ({total_rom / 1024:6.2f} KB)")
    print(f"TOTAL ACTIVE WRAM FOOTPRINT: {total_wram:6d} Bytes ({total_wram / 1024:6.2f} KB)")
    print(f"TOTAL ACTIVE HRAM FOOTPRINT: {total_hram:6d} Bytes ({total_hram:6d} Bytes)")
    print(f"TOTAL ACTIVE VRAM FOOTPRINT: {total_vram:6d} Bytes ({total_vram / 1024:6.2f} KB)")
    print("-" * 74)
    
    # Assertions
    rom_limit = 28672  # 28KB budget
    print(f"Active ROM segment budget: {rom_limit} Bytes (28.00 KB)")
    
    if total_rom > rom_limit:
        print_failure(f"Active ROM segment footprint exceeds 28KB budget by {total_rom - rom_limit} bytes!")
        return False
        
    print_success(f"Active ROM segment footprint is {total_rom} bytes (under 28KB budget). Remaining margin: {rom_limit - total_rom} bytes.")
    return True

# ==============================================================================
# Main Runner
# ==============================================================================
def main():
    print("============================================================")
    print("DANDY DUNGEON GAMEBOY BUILD & SIZE VERIFICATION PIPELINE")
    print("============================================================")
    
    # 1. Fidelity Check (Python side)
    if not run_round_trip_check():
        sys.exit(1)
        
    # 2. ROM Compilation (using lcc via Makefile)
    if not compile_rom():
        sys.exit(1)
        
    # 3. Assert ROM File Size
    if not verify_rom_size():
        sys.exit(1)
        
    # 4. Parse Map File & Audit Segments
    if not analyze_segments():
        sys.exit(1)
        
    print_header("VERIFICATION SUMMARY")
    print_success("All checks passed successfully! The build is production-ready.")
    print("============================================================\n")

if __name__ == "__main__":
    main()
