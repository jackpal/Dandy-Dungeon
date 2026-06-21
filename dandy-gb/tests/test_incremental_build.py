#!/usr/bin/env python3
"""
Stress and correctness tests for the GameBoy build system (Makefile).
Verifies:
1. Parallel safety under high concurrency (make -j16)
2. Incremental rebuild accuracy:
   - Touching a C source file only rebuilds that file and relinks.
   - Touching an asset file (strike_original.png) triggers asset downscaling, compilation, and relinking, but not other C files.
   - Touching a header file triggers rebuilds of only the files that include it.
"""

import os
import sys
import unittest
import subprocess
import time
import shutil

# Add repository root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.normpath(os.path.join(current_dir, ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

class TestBuildSystemStress(unittest.TestCase):

    def setUp(self):
        # Ensure we start from a clean state and a successful initial build
        self.run_make("clean")
        self.run_make("")
        # Restore test_lib for other tests in the suite since clean deletes it
        self.run_make("test_lib")

    def tearDown(self):
        # Clean up after ourselves, but restore the ROM and test_lib so we don't leave the workspace broken
        self.run_make("clean")
        self.run_make("")
        self.run_make("test_lib")

    def run_make(self, target, extra_args="", jobs=1):
        job_flag = f"-j{jobs}" if jobs > 1 else ""
        cmd = f"make {job_flag} {target} {extra_args}"
        res = subprocess.run(
            cmd,
            shell=True,
            cwd=repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return res

    def touch_file(self, filepath):
        """Updates the modification time of a file to current time (like touch)."""
        abs_path = os.path.join(repo_root, filepath)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Cannot touch non-existent file: {abs_path}")
        # We sleep briefly to ensure the filesystem mtime resolution registers a change
        time.sleep(1.1)
        os.utime(abs_path, None)

    # =========================================================================
    # 1. Parallel Safety Stress Tests
    # =========================================================================

    def test_parallel_build_stress(self):
        """Run clean followed by high-concurrency parallel build multiple times to check for races."""
        iterations = 5
        jobs_count = 16
        print(f"\n[Parallel Build Stress] Running {iterations} iterations with -j{jobs_count}...")
        
        for i in range(iterations):
            # Clean first
            res_clean = self.run_make("clean")
            self.assertEqual(res_clean.returncode, 0, f"make clean failed at iteration {i}")
            
            # Parallel build
            res_build = self.run_make("", jobs=jobs_count)
            self.assertEqual(
                res_build.returncode, 0,
                f"Parallel build failed at iteration {i}!\nSTDOUT:\n{res_build.stdout}\nSTDERR:\n{res_build.stderr}"
            )
            
            # Verify the ROM was created
            rom_path = os.path.join(repo_root, "bin/dandy.gb")
            self.assertTrue(os.path.exists(rom_path), f"ROM was not created at iteration {i}!")

    # =========================================================================
    # 2. Incremental Rebuild Correctness Tests
    # =========================================================================

    def test_incremental_touch_c_file(self):
        """Touching dandy_core.c should only recompile dandy_core.o and relink dandy.gb."""
        print("\n[Incremental Test] Touching src/dandy_core.c...")
        self.touch_file("src/dandy_core.c")
        
        res = self.run_make("")
        self.assertEqual(res.returncode, 0, f"Incremental build failed: {res.stderr}")
        
        stdout = res.stdout
        # Should contain compiling dandy_core.c
        self.assertIn("dandy_core.c", stdout)
        # Should contain linking command
        self.assertIn("bin/dandy.gb", stdout)
        
        # Should NOT contain compiling main.c, gameboy_hal.c, levels.c, tiles.c
        self.assertNotIn("main.c", stdout)
        self.assertNotIn("gameboy_hal.c", stdout)
        self.assertNotIn("levels.c", stdout)
        self.assertNotIn("tiles.c", stdout)

    def test_incremental_touch_asset_file(self):
        """Touching strike_original.png should downscale sprites, recompile tiles.o, and relink, but not other C files."""
        print("\n[Incremental Test] Touching teamwork_graphics/strike_original.png...")
        self.touch_file("teamwork_graphics/strike_original.png")
        
        res = self.run_make("")
        self.assertEqual(res.returncode, 0, f"Incremental build failed: {res.stderr}")
        
        stdout = res.stdout
        print("DEBUG STDOUT:", repr(stdout))
        print("DEBUG 'levels.c' in stdout:", 'levels.c' in stdout)
        # Should run the sprite downscale compiler
        self.assertIn("downscale_sprites.py", stdout)
        # Should compile tiles.c to tiles.o
        self.assertIn("tiles.c", stdout)
        # Should compile main.c to main.o because main.c depends on tiles.h
        self.assertIn("main.c", stdout)
        # Should relink
        self.assertIn("bin/dandy.gb", stdout)
        
        # Should NOT compile dandy_core.c, gameboy_hal.c, levels.c
        self.assertNotIn("dandy_core.c", stdout)
        self.assertNotIn("gameboy_hal.c", stdout)
        self.assertNotIn("levels.c", stdout)

    def test_incremental_touch_tiles_h(self):
        """Touching src/tiles.h should trigger recompilation of main.o and tiles.o (due to includes)."""
        print("\n[Incremental Test] Touching src/tiles.h...")
        self.touch_file("src/tiles.h")
        
        res = self.run_make("")
        self.assertEqual(res.returncode, 0, f"Incremental build failed: {res.stderr}")
        
        stdout = res.stdout
        # main.o and tiles.o should be recompiled
        self.assertIn("main.c", stdout)
        self.assertIn("tiles.c", stdout)
        # Should relink
        self.assertIn("bin/dandy.gb", stdout)
        
        # Should NOT compile dandy_core.c, gameboy_hal.c, levels.c
        self.assertNotIn("dandy_core.c", stdout)
        self.assertNotIn("gameboy_hal.c", stdout)
        self.assertNotIn("levels.c", stdout)

    def test_incremental_touch_levels_h(self):
        """Touching src/levels.h should trigger recompilation of dandy_core.o and levels.o."""
        print("\n[Incremental Test] Touching src/levels.h...")
        self.touch_file("src/levels.h")
        
        res = self.run_make("")
        self.assertEqual(res.returncode, 0, f"Incremental build failed: {res.stderr}")
        
        stdout = res.stdout
        # dandy_core.o and levels.o should be recompiled
        self.assertIn("dandy_core.c", stdout)
        self.assertIn("levels.c", stdout)
        # Should relink
        self.assertIn("bin/dandy.gb", stdout)
        
        # Should NOT compile main.c, gameboy_hal.c, tiles.c
        self.assertNotIn("main.c", stdout)
        self.assertNotIn("gameboy_hal.c", stdout)
        self.assertNotIn("tiles.c", stdout)

if __name__ == "__main__":
    unittest.main()
