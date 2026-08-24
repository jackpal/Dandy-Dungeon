import os
import sys

# Add dandy-gb/tools to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../dandy-gb/tools")))

try:
    import verify_compression as vc
except ImportError as e:
    print(f"Error importing verify_compression: {e}")
    sys.exit(1)

def run_edge_case_tests():
    print("============================================================")
    print("PYTHON PIPELINE EDGE-CASE LEVEL VERIFICATION")
    print("============================================================")

    # Helper to generate a valid level with border walls
    def make_level(inner_tiles):
        if len(inner_tiles) != 1624:
            raise ValueError(f"Expected 1624 inner tiles, got {len(inner_tiles)}")
        return vc.reconstruct_edge_walls(inner_tiles)

    # 1. All Space level (inner tiles = 0)
    all_space_inner = [0] * 1624
    all_space_lvl = make_level(all_space_inner)
    
    # 2. All Wall level (inner tiles = 1)
    all_wall_inner = [1] * 1624
    all_wall_lvl = make_level(all_wall_inner)
    
    # 3. Maximum Density level (inner tiles = 15)
    max_density_inner = [15] * 1624
    max_density_lvl = make_level(max_density_inner)
    
    # 4. Sparse level (a single generator in the center, rest spaces)
    sparse_inner = [0] * 1624
    sparse_inner[812] = 13 # Generator 1
    sparse_lvl = make_level(sparse_inner)
    
    # 5. Dense level (alternating doors and monsters)
    dense_inner = [2 if i % 2 == 0 else 9 for i in range(1624)]
    dense_lvl = make_level(dense_inner)

    test_cases = [
        ("All Space Level (Min Density)", all_space_lvl, all_space_inner),
        ("All Wall Level (High Wall Count)", all_wall_lvl, all_wall_inner),
        ("Max Density Level (6-bit tiles)", max_density_lvl, max_density_inner),
        ("Sparse Level (Mostly Space)", sparse_lvl, sparse_inner),
        ("Dense Level (Alternating Tiles)", dense_lvl, dense_inner),
    ]

    all_passed = True
    for name, lvl, inner in test_cases:
        print(f"Testing {name}...")
        
        # 1. Elision check
        elided = vc.elide_edge_walls(lvl)
        if elided != inner:
            print(f"  [FAIL] Edge Wall Elision mismatch!")
            all_passed = False
            continue
            
        # 2. Compress
        try:
            compressed = vc.scheme_b2_compress(elided)
        except Exception as e:
            print(f"  [FAIL] Compression raised exception: {e}")
            all_passed = False
            continue
            
        # Theoretical size calculations
        # Space (0) -> 1 bit
        # Wall (1) -> 2 bits
        # Other (2-15) -> 6 bits
        bits_needed = sum(1 if t == 0 else (2 if t == 1 else 6) for t in elided)
        expected_bytes = (bits_needed + 7) // 8
        actual_bytes = len(compressed)
        
        print(f"  - Theoretical size: {bits_needed} bits ({expected_bytes} bytes)")
        print(f"  - Actual compressed size: {actual_bytes} bytes")
        
        if actual_bytes != expected_bytes:
            print(f"  [FAIL] Compressed size mismatch! Expected {expected_bytes}, got {actual_bytes}")
            all_passed = False
            continue
            
        # 3. Decompress
        try:
            decompressed_elided = vc.scheme_b2_decompress(compressed)
        except Exception as e:
            print(f"  [FAIL] Decompression raised exception: {e}")
            all_passed = False
            continue
            
        if decompressed_elided != elided:
            print(f"  [FAIL] Decompressed elided mismatch!")
            all_passed = False
            continue
            
        # 4. Reconstruction
        reconstructed = vc.reconstruct_edge_walls(decompressed_elided)
        if reconstructed != lvl:
            print(f"  [FAIL] Reconstruction mismatch!")
            all_passed = False
            continue
            
        print(f"  [PASS] 100% round-trip fidelity verified.")

    print("\n============================================================")
    if all_passed:
        print("ALL PYTHON PIPELINE EDGE-CASE TESTS PASSED SUCCESSFULLY!")
    else:
        print("SOME PIPELINE EDGE-CASE TESTS FAILED!")
    print("============================================================\n")
    return all_passed

if __name__ == "__main__":
    run_edge_case_tests()
