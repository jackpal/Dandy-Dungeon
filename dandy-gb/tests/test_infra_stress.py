import unittest
import os
import sys
import gc
import shutil
import tempfile
import glob
import resource
import subprocess
import time

# Ensure tests/ directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dandy_env import DandyEnv

def get_open_fd_count():
    try:
        return len(os.listdir('/proc/self/fd'))
    except Exception:
        return 0

def get_mapped_lib_count():
    try:
        paths = set()
        with open('/proc/self/maps', 'r') as f:
            for line in f:
                if 'libdandy_test.so' in line:
                    parts = line.split()
                    if len(parts) >= 6:
                        paths.add(parts[5])
        return len(paths)
    except Exception:
        return 0

def get_rss_kb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

def get_temp_env_dirs():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return glob.glob(os.path.join(script_dir, '.temp_envs/dandy_env_*'))

class TestInfraStress(unittest.TestCase):
    
    def tearDown(self):
        if hasattr(self, "env"):
            del self.env

    def test_lifecycle_and_leak_stability_1000_runs(self):
        """Instantiate and delete DandyEnv 1000 times to verify no FD, library, temp dir, or memory leaks."""
        print("\n--- Starting Lifecycle and Leak Stability Test (1000 iterations) ---")
        
        # Clean up any leftover temp dirs from previous runs first
        for d in get_temp_env_dirs():
            try:
                shutil.rmtree(d)
            except Exception:
                pass
                
        gc.collect()
        
        start_fd = get_open_fd_count()
        start_libs = get_mapped_lib_count()
        start_temp_dirs = len(get_temp_env_dirs())
        start_rss = get_rss_kb()
        
        print(f"Initial state: FDs={start_fd}, Mapped Libs={start_libs}, Temp Dirs={start_temp_dirs}, RSS={start_rss} KB")
        
        # Warm up with 5 runs to let ctypes/libc stabilize their internal caches
        for _ in range(5):
            env = DandyEnv()
            env.init()
            env.step([0, 0, 0, 0])
            del env
        for _ in range(3):
            gc.collect()
            time.sleep(0.005)
        
        stable_fd = get_open_fd_count()
        stable_libs = get_mapped_lib_count()
        stable_temp_dirs = len(get_temp_env_dirs())
        stable_rss = get_rss_kb()
        print(f"Stabilized state (after warmup): FDs={stable_fd}, Mapped Libs={stable_libs}, Temp Dirs={stable_temp_dirs}, RSS={stable_rss} KB")
        
        # Run 1000 iterations
        for i in range(1000):
            env = DandyEnv()
            env.init()
            env.step([0, 0, 0, 0])
            del env
            # Periodic GC to keep memory clean
            if i % 100 == 0:
                gc.collect()
                
        for _ in range(3):
            gc.collect()
            time.sleep(0.005)
        
        end_fd = get_open_fd_count()
        end_libs = get_mapped_lib_count()
        end_temp_dirs = len(get_temp_env_dirs())
        end_rss = get_rss_kb()
        
        print(f"Final state (after 1000 runs): FDs={end_fd}, Mapped Libs={end_libs}, Temp Dirs={end_temp_dirs}, RSS={end_rss} KB")
        
        # Assertions
        # 1. File Descriptors: should not grow by more than a tiny buffer (e.g. 1-2 due to python internals, but ideally 0)
        self.assertLessEqual(end_fd, stable_fd + 2, f"FD leak detected! Stablized: {stable_fd}, End: {end_fd}")
        
        # 2. Shared Library mappings: must remain identical
        self.assertEqual(end_libs, stable_libs, f"Shared library handle leak detected! Stabilized: {stable_libs}, End: {end_libs}")
        
        # 3. Temp directories: must not leak (no growth compared to stable baseline)
        self.assertLessEqual(end_temp_dirs, stable_temp_dirs, f"Temp directory leak detected! Leftover: {get_temp_env_dirs()}")
        
        # 4. Memory: RSS should remain stable (allowing a small overhead, e.g., 5MB/5120KB for Python's allocator fragmentation, but not unbounded growth)
        rss_growth = end_rss - stable_rss
        print(f"RSS Memory Growth: {rss_growth} KB")
        self.assertLessEqual(rss_growth, 5120, f"Memory leak detected! RSS grew by {rss_growth} KB")

    def test_state_isolation_parallel(self):
        """Verify that multiple concurrent DandyEnv instances have 100% isolated states."""
        print("\n--- Starting Parallel State Isolation Test ---")
        
        envs = [DandyEnv() for _ in range(5)]
        for env in envs:
            env.init()
            
        # Write unique states to each environment
        for idx, env in enumerate(envs):
            env.current_level = idx + 10
            env.set_player_health(0, 100 + idx * 10)
            
            # Create a unique map
            custom_map = [env.TILE_SPACE] * env.MAP_SIZE
            custom_map[0] = env.TILE_WALL + idx
            env.dandy_map = custom_map
            
        # Verify isolation
        for idx, env in enumerate(envs):
            self.assertEqual(env.current_level, idx + 10)
            self.assertEqual(env.get_player_health(0), 100 + idx * 10)
            self.assertEqual(env.dandy_map[0], env.TILE_WALL + idx)
            
        # Delete envs one by one and check the remaining ones
        for i in range(4):
            envs.pop(0) # Pop the first one correctly (this triggers deletion)
            gc.collect()
            
            # Verify the remaining envs still have their correct isolated state
            for idx, env in enumerate(envs):
                # The remaining envs are originally at index i+1+idx
                orig_idx = i + 1 + idx
                self.assertEqual(env.current_level, orig_idx + 10)
                self.assertEqual(env.get_player_health(0), 100 + orig_idx * 10)
                self.assertEqual(env.dandy_map[0], env.TILE_WALL + orig_idx)

    def test_robustness_extreme_inputs_direct(self):
        """Test extreme and boundary inputs directly on DandyEnv python wrapper without crashing."""
        print("\n--- Starting Direct Robustness Tests ---")
        env = DandyEnv()
        env.init()
        
        # 1. Invalid player indices on safe Python accessors
        # env.get_player(idx) should raise IndexError on invalid index
        with self.assertRaises(IndexError):
            env.get_player(-1)
        with self.assertRaises(IndexError):
            env.get_player(4)
        with self.assertRaises(IndexError):
            env.get_player(100)
            
        # 2. Invalid inputs size to step
        with self.assertRaises(ValueError):
            env.step([])
        with self.assertRaises(ValueError):
            env.step([1, 2])
        with self.assertRaises(ValueError):
            env.step([0, 0, 0, 0, 0])
            
        # 3. Extreme health values (signed 16-bit integer, should handle large and negative)
        env.set_player_health(0, -32768)
        self.assertEqual(env.get_player_health(0), -32768)
        env.set_player_health(0, 32767)
        self.assertEqual(env.get_player_health(0), 32767)
        env.set_player_health(0, 0)
        self.assertEqual(env.get_player_health(0), 0)

    def test_robustness_out_of_bounds_level_crash(self):
        """Verify that loading an invalid level index triggers an out-of-bounds read and crashes (SIGSEGV)."""
        print("\n--- Starting Level Out-of-Bounds Crash Test (Subprocess) ---")
        
        test_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Run in a subprocess to protect the main test runner from segfaults
        code = f"""
import sys
sys.path.insert(0, "{test_dir}")
from dandy_env import DandyEnv
env = DandyEnv()
env.init()
env.load_level(100) # Out of bounds (only 26 levels exist)
print("SUCCESS")
"""
        
        p = subprocess.Popen(
            [sys.executable, "-c", code],
            cwd=test_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = p.communicate()
        
        print(f"Level OOB exit code: {p.returncode} (expected < 0 due to SIGSEGV)")
        print(f"Level OOB stdout: {stdout.decode().strip()}")
        print(f"Level OOB stderr: {stderr.decode().strip()}")
        
        # With bounds checking implemented in the C engine, loading an invalid level index
        # should now be handled safely (clamped to the maximum level) and NOT crash (exit code 0).
        self.assertEqual(p.returncode, 0, f"Engine crashed or failed with exit code {p.returncode}! Out-of-bounds level index should be handled safely.")
        self.assertIn("SUCCESS", stdout.decode(), "Subprocess did not complete successfully or print SUCCESS.")

    def test_robustness_out_of_bounds_player_y_corruption(self):
        """Verify that setting an out-of-bounds player y-coordinate causes out-of-bounds writes (silent memory corruption)."""
        print("\n--- Starting Player Y Out-of-Bounds Corruption Test (Subprocess) ---")
        
        test_dir = os.path.dirname(os.path.abspath(__file__))
        
        code = f"""
import sys
sys.path.insert(0, "{test_dir}")
import ctypes
from dandy_env import DandyEnv
env = DandyEnv()
env.init()

# Cast dandy_map to a larger pointer to observe out-of-bounds memory
map_ptr = ctypes.cast(ctypes.addressof(env._dandy_map), ctypes.POINTER(ctypes.c_uint8))

# Set the memory at 2314 (which corresponds to row_offsets[255] + player_x[0] = 2304 + 10 = 2314)
# to a known value to verify if it gets overwritten during the step
map_ptr[2314] = 99
print(f"BEFORE - Memory at 2314: {{map_ptr[2314]}}")

# Force player 0 y-coordinate out of bounds (row_offsets only has 30 elements)
env.set_player_position(0, 10, 255)

# Step the environment with player 0 moving. This will trigger do_player_buttons(),
# which attempts to write the player tile to dandy_map[row_offsets[255] + 10] (out of bounds),
# causing silent memory corruption of whatever lies at index 2314!
env.step([env.BUTTON_RIGHT, 0, 0, 0])

after_val = map_ptr[2314]
print(f"AFTER - Memory at 2314: {{after_val}}")

# If the out-of-bounds write occurred, the value at 2314 should have been overwritten
# to either 0 (TILE_SPACE, if cleared) or 26 (GET_PLAYER_TILE, if not cleared/failed move).
# In either case, it should NOT be 99!
if after_val in (0, 26):
    print("CORRUPTION_DETECTED")
else:
    print("NO_CORRUPTION")
"""
        
        p = subprocess.Popen(
            [sys.executable, "-c", code],
            cwd=test_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = p.communicate()
        
        output_str = stdout.decode()
        print(f"Subprocess output:\n{output_str}")
        print(f"Subprocess stderr:\n{stderr.decode()}")
        
        # With bounds checking implemented in the C engine, setting an out-of-bounds player y-coordinate
        # should now be safely clamped, preventing any out-of-bounds memory write/corruption.
        self.assertEqual(p.returncode, 0, f"Engine crashed with exit code {p.returncode}!")
        self.assertIn("NO_CORRUPTION", output_str, "Memory corruption detected! Out-of-bounds y-coordinate was not safely clamped.")

if __name__ == '__main__':
    unittest.main()
