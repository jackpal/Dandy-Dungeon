#!/usr/bin/env python3
import sys
import os

# Add tools directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import verify_compression as vc
except ImportError as e:
    print(f"Failed to import verify_compression: {e}")
    sys.exit(1)

def test_case(name, data, expect_fail=False):
    print(f"Testing {name}...", end=" ")
    try:
        compressed = vc.compress_pipeline(data)
        decompressed = vc.decompress_pipeline(compressed)
        if expect_fail:
            print("\033[91mFAIL (Expected failure/exception, but round-trip succeeded)\033[0m")
            return False
        if decompressed == data:
            print("\033[92mPASS\033[0m")
            return True
        else:
            print("\033[91mFAIL (Data mismatch!)\033[0m")
            print(f"  Input:  {data[:20]}...")
            print(f"  Output: {decompressed[:20]}...")
            return False
    except Exception as e:
        if expect_fail:
            print(f"\033[92mPASS (Failed as expected with: {type(e).__name__}: {e})\033[0m")
            return True
        else:
            print(f"\033[91mFAIL (Unexpected exception: {type(e).__name__}: {e})\033[0m")
            return False

def main():
    print("============================================================")
    # 1. Empty list
    test_case("Empty List", [])
    
    # 2. Single element
    test_case("Single Element (0)", [0])
    test_case("Single Element (1)", [1])
    
    # 3. Short runs (should not compress)
    test_case("Short Run (length 3)", [1, 1, 1])
    
    # 4. Long runs (should compress)
    test_case("Long Run (length 4)", [1, 1, 1, 1])
    test_case("Standard Level sized all-identical", [1] * 1800)
    
    # 5. No runs (alternating)
    test_case("No Runs (alternating)", [i % 16 for i in range(1800)])
    
    # 6. Run length boundary (255)
    test_case("Run length exactly 255", [1] * 255)
    
    # 7. Run length boundary (256)
    test_case("Run length exactly 256", [1] * 256)
    
    # 8. Large run (1000)
    test_case("Run length 1000", [1] * 1000)
    
    # 9. Marker Byte (255) handling - CRITICAL EDGE CASE
    # A single 255 tile should fail or corrupt because 255 is the RLE marker
    test_case("Single Marker Byte [255]", [255])
    test_case("Marker Byte in a short run [1, 255, 2]", [1, 255, 2])
    test_case("Marker Byte in a long run [255]*4", [255] * 4)
    test_case("Marker Byte at the end [1, 2, 255]", [1, 2, 255])
    
    # 10. Malformed compressed stream behavior (Decompression only)
    print("Testing malformed compressed streams:")
    
    # Truncated stream: ends with marker 255
    try:
        vc.decompress_pipeline([255])
        print("  Truncated [255]: \033[91mFAIL (No exception raised)\033[0m")
    except ValueError as e:
        print(f"  Truncated [255]: \033[92mPASS (Expected ValueError: {e})\033[0m")
        
    # Truncated stream: ends with marker 255 and length
    try:
        vc.decompress_pipeline([255, 10])
        print("  Truncated [255, 10]: \033[91mFAIL (No exception raised)\033[0m")
    except ValueError as e:
        print(f"  Truncated [255, 10]: \033[92mPASS (Expected ValueError: {e})\033[0m")

if __name__ == "__main__":
    main()
