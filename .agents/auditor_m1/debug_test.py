import os
import sys
import shutil
import glob
import gc
import resource

# Add tests and dandy-gb to path
dandy_gb_dir = '/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb'
sys.path.insert(0, dandy_gb_dir)
sys.path.insert(0, os.path.join(dandy_gb_dir, 'tests'))

from dandy_env import DandyEnv

def check_lib():
    lib_path = os.path.join(dandy_gb_dir, 'libdandy_test.so')
    exists = os.path.exists(lib_path)
    size = os.path.getsize(lib_path) if exists else -1
    print(f"[Debug] libdandy_test.so exists: {exists}, size: {size}")

def get_temp_env_dirs():
    return glob.glob(os.path.join(dandy_gb_dir, 'tests/.temp_envs/dandy_env_*'))

def main():
    print("--- Starting Debug Run ---")
    check_lib()
    
    # 1. Clean up temp dirs
    print("Cleaning up temp dirs...")
    for d in get_temp_env_dirs():
        print(f"Deleting temp dir: {d}")
        shutil.rmtree(d)
    check_lib()
    
    # 2. Warmup and Stress Run
    print("Starting stress run (1000 iterations)...")
    for i in range(1000):
        try:
            env = DandyEnv()
            env.init()
            env.step([0, 0, 0, 0])
            del env
        except Exception as e:
            print(f"Failed at iteration {i}: {e}")
            check_lib()
            sys.exit(1)
        if i % 100 == 0:
            print(f"Iteration {i}...")
            check_lib()
            gc.collect()
        
    print("Stress run finished.")
    check_lib()

if __name__ == '__main__':
    main()
