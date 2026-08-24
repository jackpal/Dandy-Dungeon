#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess

# Add GBDK to PATH if it exists in the Developer directory
gbdk_bin_path = "/usr/local/google/home/jackpal/Developer/gbdk/bin"
if os.path.exists(gbdk_bin_path):
    os.environ["PATH"] = gbdk_bin_path + os.pathsep + os.environ["PATH"]
    # Set GBDKDIR environment variable (must have trailing slash)
    os.environ["GBDKDIR"] = "/usr/local/google/home/jackpal/Developer/gbdk/"

dandy_gb_dir = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb"
convert_py_path = os.path.join(dandy_gb_dir, "tools", "convert_levels.py")
convert_py_backup = convert_py_path + ".bak"

def restore_backup():
    if os.path.exists(convert_py_backup):
        shutil.copy2(convert_py_backup, convert_py_path)
        os.remove(convert_py_backup)
        print("Restored convert_levels.py from backup.")

def run_build(num_levels):
    print(f"\n--- Testing build with {num_levels} levels ---")
    
    # Modify convert_levels.py
    with open(convert_py_path, "r") as f:
        content = f.read()
    
    # Replace the mitigation line: levels = levels[:5]
    modified_content = content.replace("levels = levels[:5]", f"levels = levels[:{num_levels}]")
    
    with open(convert_py_path, "w") as f:
        f.write(modified_content)
        
    try:
        # Run make clean
        print("Running 'make clean'...")
        clean_res = subprocess.run(["make", "clean"], cwd=dandy_gb_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if clean_res.returncode != 0:
            print("make clean failed!")
            print("STDOUT:", clean_res.stdout.decode())
            print("STDERR:", clean_res.stderr.decode())
            return False, "make clean failed"
        
        print("Running 'make'...")
        res = subprocess.run(["make"], cwd=dandy_gb_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if res.returncode == 0:
            print(f"SUCCESS: Build succeeded with {num_levels} levels.")
            # Check ROM size
            rom_path = os.path.join(dandy_gb_dir, "bin", "dandy.gb")
            if os.path.exists(rom_path):
                print(f"ROM size: {os.path.getsize(rom_path)} bytes")
            return True, ""
        else:
            print(f"FAILURE: Build failed with {num_levels} levels. Exit code: {res.returncode}")
            stderr_output = res.stderr.decode()
            print("Error output:")
            # Just print the first 20 lines of error to avoid bloat
            lines = stderr_output.splitlines()
            print("\n".join(lines[:20]))
            if len(lines) > 20:
                print(f"... and {len(lines) - 20} more lines.")
            return False, stderr_output
            
    finally:
        # Restore the original file content for next iteration
        with open(convert_py_path, "w") as f:
            f.write(content)

def main():
    # Make backup of convert_levels.py
    shutil.copy2(convert_py_path, convert_py_backup)
    print("Created backup of convert_levels.py")
    
    try:
        # 1. Test 5 levels (should succeed)
        success_5, err_5 = run_build(5)
        if not success_5:
            print("ERROR: 5 levels failed to build!")
            return
        
        # 2. Test all 26 levels (should overflow)
        success_all, err_all = run_build(26)
        
        # 3. Find the exact limit incrementally
        # Let's try to find at what number of levels it first overflows
        limit = None
        for n in range(6, 27):
            success, err = run_build(n)
            if not success:
                limit = n - 1
                print(f"\n[LIMIT FOUND] Maximum levels that can be compiled before bank overflow: {limit}")
                print(f"Compiling {n} levels triggers overflow/failure.")
                break
        
        if limit is None:
            print("\n[WARNING] No bank overflow was triggered even with 26 levels!")
            
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        restore_backup()

if __name__ == "__main__":
    main()
