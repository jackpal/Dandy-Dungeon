#!/usr/bin/env python3
import sys
import os
import unittest

# Add the tools directory to path
sys.path.append("/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools")

import verify_compression

class TestCompressionStress(unittest.TestCase):
    def test_empty_list(self):
        """Test with an empty tile list."""
        raw = []
        compressed = verify_compression.compress_pipeline(raw)
        decompressed = verify_compression.decompress_pipeline(compressed)
        self.assertEqual(raw, decompressed)
        self.assertEqual(compressed, [])

    def test_all_identical_below_threshold(self):
        """Test runs of identical tiles below RLE threshold (run length < 4)."""
        for l in range(1, 4):
            raw = [1] * l
            compressed = verify_compression.compress_pipeline(raw)
            decompressed = verify_compression.decompress_pipeline(compressed)
            self.assertEqual(raw, decompressed)
            self.assertEqual(compressed, raw) # No compression should occur

    def test_all_identical_at_threshold(self):
        """Test runs of identical tiles at RLE threshold (run length == 4)."""
        raw = [1] * 4
        compressed = verify_compression.compress_pipeline(raw)
        decompressed = verify_compression.decompress_pipeline(compressed)
        self.assertEqual(raw, decompressed)
        # Should compress to: [255, run_len, tile] -> [255, 4, 1]
        self.assertEqual(compressed, [255, 4, 1])

    def test_all_identical_max_single_run(self):
        """Test run of identical tiles at max single run length (255)."""
        raw = [1] * 255
        compressed = verify_compression.compress_pipeline(raw)
        decompressed = verify_compression.decompress_pipeline(compressed)
        self.assertEqual(raw, decompressed)
        self.assertEqual(compressed, [255, 255, 1])

    def test_all_identical_exceeding_single_run(self):
        """Test runs of identical tiles exceeding max single run length (e.g. 256, 300)."""
        # 256 tiles: should be compressed as [255, 255, 1] + [1]
        raw_256 = [1] * 256
        compressed_256 = verify_compression.compress_pipeline(raw_256)
        decompressed_256 = verify_compression.decompress_pipeline(compressed_256)
        self.assertEqual(raw_256, decompressed_256)
        self.assertEqual(compressed_256, [255, 255, 1, 1])

        # 300 tiles: should be compressed as [255, 255, 1] + [255, 45, 1] (since 45 >= 4)
        raw_300 = [1] * 300
        compressed_300 = verify_compression.compress_pipeline(raw_300)
        decompressed_300 = verify_compression.decompress_pipeline(compressed_300)
        self.assertEqual(raw_300, decompressed_300)
        self.assertEqual(compressed_300, [255, 255, 1, 255, 45, 1])

    def test_no_identical_tiles(self):
        """Test with no runs of identical tiles (unique/alternating tiles)."""
        raw = list(range(16)) * 10
        compressed = verify_compression.compress_pipeline(raw)
        decompressed = verify_compression.decompress_pipeline(compressed)
        self.assertEqual(raw, decompressed)
        self.assertEqual(compressed, raw) # Should not compress anything

    def test_alternating_runs(self):
        """Test alternating runs of varying lengths."""
        raw = [1] * 10 + [2] * 3 + [3] * 300 + [4] * 2
        # Expected:
        # [1]*10 -> [255, 10, 1]
        # [2]*3  -> [2, 2, 2]
        # [3]*300 -> [255, 255, 3] + [255, 45, 3]
        # [4]*2  -> [4, 4]
        expected = [255, 10, 1, 2, 2, 2, 255, 255, 3, 255, 45, 3, 4, 4]
        compressed = verify_compression.compress_pipeline(raw)
        decompressed = verify_compression.decompress_pipeline(compressed)
        self.assertEqual(raw, decompressed)
        self.assertEqual(compressed, expected)

    def test_invalid_tile_values_non_marker(self):
        """Test with tile values outside valid range 0-15 but not equal to the RLE marker (255)."""
        raw = [100, 100, 100, 100, 200, 200]
        compressed = verify_compression.compress_pipeline(raw)
        decompressed = verify_compression.decompress_pipeline(compressed)
        self.assertEqual(raw, decompressed)
        self.assertEqual(compressed, [255, 4, 100, 200, 200])

    def test_invalid_tile_values_marker_vulnerability(self):
        """
        Adversarial test: Test behavior when the tile list contains the RLE marker (255) itself.
        This demonstrates the vulnerability/limitation of the simple RLE design.
        """
        # Case A: Truncated stream error when 255 is at the end as a literal
        raw_a = [255]
        compressed_a = verify_compression.compress_pipeline(raw_a)
        self.assertEqual(compressed_a, [255]) # Compressed as literal
        
        # Decompressing should fail or raise ValueError
        with self.assertRaises(ValueError) as ctx:
            verify_compression.decompress_pipeline(compressed_a)
        self.assertIn("truncated run-length encoding", str(ctx.exception))
        print("\n[VULNERABILITY CONFIRMED] Decompressing literal 255 at end of stream raises ValueError.")

        # Case B: Silent data corruption when 255 is followed by other tiles
        raw_b = [255, 5, 10]
        compressed_b = verify_compression.compress_pipeline(raw_b)
        self.assertEqual(compressed_b, [255, 5, 10]) # All compressed as literals since runs < 4
        
        # Decompressing should interpret [255, 5, 10] as "5 runs of tile 10"
        decompressed_b = verify_compression.decompress_pipeline(compressed_b)
        self.assertNotEqual(raw_b, decompressed_b)
        self.assertEqual(decompressed_b, [10] * 5)
        print(f"[VULNERABILITY CONFIRMED] Silent data corruption: original {raw_b} decompressed to {decompressed_b}!")

if __name__ == "__main__":
    unittest.main()
