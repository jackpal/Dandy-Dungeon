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

# Add GBDK to PATH if it exists in the Developer directory
gbdk_bin_path = "/usr/local/google/home/jackpal/Developer/gbdk/bin"
if os.path.exists(gbdk_bin_path):
    os.environ["PATH"] = gbdk_bin_path + os.pathsep + os.environ["PATH"]
    # Set GBDKDIR environment variable (must have trailing slash)
    os.environ["GBDKDIR"] = "/usr/local/google/home/jackpal/Developer/gbdk/"

# Paths relative to the dandy-gb directory
current_dir = os.path.dirname(os.path.abspath(__file__))
dandy_gb_dir = os.path.normpath(os.path.join(current_dir, ".."))
rom_path = os.path.join(dandy_gb_dir, "bin", "dandy.gb")
map_path = os.path.join(dandy_gb_dir, "bin", "dandy.map")
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
# 1. Level Compression & Reconstruction Pipeline (Modular)
# ==============================================================================
ENCODING = " *DudKF$i123mnop"

def char_to_tile_id(c):
    try:
        return ENCODING.index(c)
    except ValueError:
        return 0

# --- STAGE 1: Level Loader ---
def load_raw_levels(js_path):
    """Reads levels from levels.js and returns a list of flat 60x30 lists of tile IDs."""
    if not os.path.exists(js_path):
        raise FileNotFoundError(f"levels.js not found at {js_path}")
        
    print(f"Reading levels from {js_path}...")
    with open(js_path, "r") as f:
        content = f.read()
    
    all_strings = re.findall(r'"([^"]*)"', content)
    level_rows = [s for s in all_strings if len(s) == 60]
    
    levels = []
    for i in range(0, len(level_rows), 30):
        rows = level_rows[i:i+30]
        flat_tiles = []
        for row in rows:
            flat_tiles.extend([char_to_tile_id(c) for c in row])
            while len(flat_tiles) % 60 != 0:
                flat_tiles.append(0)
        levels.append(flat_tiles)
    return levels

# --- STAGE 2: Compression Pipeline ---
def compress_pipeline(raw_tiles):
    """
    Runs the compression pipeline using Edge Wall Elision and Scheme B2.
    """
    elided_tiles = elide_edge_walls(raw_tiles)
    compressed_data = scheme_b2_compress(elided_tiles)
    return compressed_data

# --- STAGE 3: Decompression & Reconstruction Pipeline ---
def decompress_pipeline(compressed_data):
    """
    Runs the decompression and reconstruction pipeline using Scheme B2 and EWE.
    """
    elided_tiles = scheme_b2_decompress(compressed_data)
    reconstructed_tiles = reconstruct_edge_walls(elided_tiles)
    return reconstructed_tiles

# --- Pipeline Helpers (Edge Wall Elision & Scheme B2) ---
def elide_edge_walls(tile_ids):
    """Extracts the inner 58x28 grid (1624 tiles) from a flat 60x30 map (1800 tiles)."""
    if len(tile_ids) != 1800:
        raise ValueError(f"Expected 1800 tiles, got {len(tile_ids)}")
    elided = []
    for y in range(1, 29):
        for x in range(1, 59):
            idx = y * 60 + x
            elided.append(tile_ids[idx])
    return elided

def reconstruct_edge_walls(elided_tiles):
    """Reconstructs the 60x30 map from 1624 inner tiles, pre-filling borders with Wall (ID 1)."""
    if len(elided_tiles) != 1624:
        raise ValueError(f"Expected 1624 elided tiles, got {len(elided_tiles)}")
    reconstructed = [1] * 1800  # Pre-fill entire map with Wall (ID 1)
    elided_idx = 0
    for y in range(1, 29):
        for x in range(1, 59):
            map_idx = y * 60 + x
            reconstructed[map_idx] = elided_tiles[elided_idx]
            elided_idx += 1
    return reconstructed

def scheme_b2_compress(tile_ids):
    """Compresses tile IDs using Scheme B2 prefix coding and packs them MSB-first into bytes."""
    bit_str = ""
    for tile in tile_ids:
        if tile == 0:
            bit_str += "0"
        elif tile == 1:
            bit_str += "10"
        elif 2 <= tile <= 15:
            bit_str += "11" + f"{tile:04b}"
        else:
            raise ValueError(f"Invalid tile ID: {tile}")
            
    compressed_bytes = []
    for i in range(0, len(bit_str), 8):
        byte_chunk = bit_str[i:i+8]
        if len(byte_chunk) < 8:
            # Pad the final byte with 0s to byte boundary
            byte_chunk = byte_chunk + "0" * (8 - len(byte_chunk))
        compressed_bytes.append(int(byte_chunk, 2))
        
    return compressed_bytes

def scheme_b2_decompress(compressed_bytes):
    """Decompresses packed bytes back into 1624 tile IDs using Scheme B2."""
    bit_str = "".join(f"{b:08b}" for b in compressed_bytes)
    tile_ids = []
    i = 0
    while len(tile_ids) < 1624 and i < len(bit_str):
        if bit_str[i] == '0':
            tile_ids.append(0)
            i += 1
        elif bit_str[i:i+2] == '10':
            tile_ids.append(1)
            i += 2
        elif bit_str[i:i+2] == '11':
            if i + 6 > len(bit_str):
                raise ValueError("Truncated bitstream during tile decoding")
            tile_id = int(bit_str[i+2:i+6], 2)
            tile_ids.append(tile_id)
            i += 6
        else:
            raise ValueError(f"Malformed bitstream prefix at bit index {i}")
            
    if len(tile_ids) < 1624:
        raise ValueError(f"Incomplete bitstream: only decoded {len(tile_ids)}/1624 tiles")
        
    return tile_ids

# --- Pipeline Runner & Fidelity Assertion ---
def run_round_trip_check():
    print_header("1. Level Compression Round-Trip Fidelity Check")
    
    try:
        levels = load_raw_levels(levels_js_path)
    except Exception as e:
        print_failure(str(e))
        return False
        
    print(f"Loaded {len(levels)} levels. Performing pipeline round-trip checks...")
    
    for l_idx, raw_tiles in enumerate(levels):
        # Run Compression Pipeline
        compressed = compress_pipeline(raw_tiles)
        
        # Run Decompression Pipeline
        decompressed = decompress_pipeline(compressed)
        
        # Fidelity Assertion
        if decompressed != raw_tiles:
            print_failure(f"Level {l_idx} failed pipeline round-trip compression fidelity check!")
            return False
            
    print_success(f"All {len(levels)} levels passed modular pipeline compression/decompression with 100% fidelity.")
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
        r'^\s*([_A-Za-z0-9]+)\s+([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+=\s+(\d+)\.?\s+bytes',
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
            
        # Resolve banked addresses using 16-bit offset
        offset = addr & 0xFFFF
        region = "Unknown"
        if (addr < 0x8000) or (offset < 0x8000 and addr >= 0x10000):
            region = "ROM"
            rom_segments.append((name, addr, size))
        elif (0x8000 <= addr < 0xA000) or (0x8000 <= offset < 0xA000 and addr >= 0x10000):
            region = "VRAM"
            vram_segments.append((name, addr, size))
        elif (0xC000 <= addr < 0xE000) or (0xC000 <= offset < 0xE000 and addr >= 0x10000):
            region = "WRAM"
            wram_segments.append((name, addr, size))
        elif (0xFF80 <= addr <= 0xFFFE) or (0xFF80 <= offset <= 0xFFFE and addr >= 0x10000):
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
# 5. Run E2E Tests
# ==============================================================================
def run_e2e_tests():
    print_header("5. Running E2E Test Suite (make test_lib && make test)")
    
    # 1. Compile Test Library
    print("Compiling test library...")
    lib_res = subprocess.run(["make", "test_lib"], cwd=dandy_gb_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if lib_res.returncode != 0:
        print_failure("make test_lib failed:")
        print(lib_res.stderr.decode())
        return False
        
    # 2. Run E2E Tests
    print("Running E2E tests...")
    test_res = subprocess.run(["make", "test"], cwd=dandy_gb_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(test_res.stdout.decode())
    if test_res.returncode != 0:
        print_failure("E2E tests failed:")
        print(test_res.stderr.decode())
        return False
        
    print_success("All E2E tests passed successfully.")
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
        
    # 5. Run E2E Tests
    if not run_e2e_tests():
        sys.exit(1)
        
    print_header("VERIFICATION SUMMARY")
    print_success("All checks passed successfully! The build is production-ready.")
    print("============================================================\n")

if __name__ == "__main__":
    main()
