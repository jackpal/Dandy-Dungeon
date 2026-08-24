#!/usr/bin/env python3
import os
import subprocess
import time
import shutil

DANDY_GB_DIR = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb"

def run_cmd(cmd, cwd=DANDY_GB_DIR):
    res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return res

def check_exists(path):
    return os.path.exists(os.path.join(DANDY_GB_DIR, path))

def get_mtime(path):
    return os.path.getmtime(os.path.join(DANDY_GB_DIR, path))

def main():
    print("=== STARTING BUILD SYSTEM STALE OBJECTS TEST ===")
    
    # 1. Clean build
    print("Running make clean...")
    res = run_cmd("make clean")
    if res.returncode != 0:
        print(f"FAIL: make clean failed: {res.stderr}")
        return False
        
    if check_exists("obj") or check_exists("obj_dark") or check_exists("bin/dandy.gb") or check_exists("bin/dandy_dark.gb"):
        print("FAIL: make clean did not remove all build directories/files.")
        return False
    print("Pass: Cleaned successfully.")
    
    # 2. Build Classic DMG
    print("Running make...")
    res = run_cmd("make")
    if res.returncode != 0:
        print(f"FAIL: make failed: {res.stderr}")
        return False
        
    if not check_exists("obj/main.o") or not check_exists("bin/dandy.gb"):
        print("FAIL: make did not build obj/main.o or bin/dandy.gb.")
        return False
    if check_exists("obj_dark") or check_exists("bin/dandy_dark.gb"):
        print("FAIL: make built obj_dark or dandy_dark.gb when it shouldn't have.")
        return False
    print("Pass: make (Classic DMG) built successfully in obj/ and bin/dandy.gb.")
    
    # Save initial mtimes
    mtime_main_o = get_mtime("obj/main.o")
    mtime_core_o = get_mtime("obj/dandy_core.o")
    mtime_rom = get_mtime("bin/dandy.gb")
    
    # 3. Build Atmospheric Dark Mode
    print("Running make dark...")
    res = run_cmd("make dark")
    if res.returncode != 0:
        print(f"FAIL: make dark failed: {res.stderr}")
        return False
        
    if not check_exists("obj_dark/main.o") or not check_exists("bin/dandy_dark.gb"):
        print("FAIL: make dark did not build obj_dark/main.o or bin/dandy_dark.gb.")
        return False
    print("Pass: make dark built successfully in obj_dark/ and bin/dandy_dark.gb.")
    
    # 4. Modify src/main.c and verify incremental build behavior
    # Sleep to ensure timestamp difference
    time.sleep(1.1)
    
    main_c_path = os.path.join(DANDY_GB_DIR, "src/main.c")
    with open(main_c_path, "r") as f:
        original_content = f.read()
        
    try:
        print("Touching src/main.c to trigger rebuild...")
        # Append a dummy comment
        with open(main_c_path, "a") as f:
            f.write("\n// Dummy comment to force recompilation\n")
            
        # Run make again
        print("Running make again...")
        res = run_cmd("make")
        if res.returncode != 0:
            print(f"FAIL: subsequent make failed: {res.stderr}")
            return False
            
        new_mtime_main_o = get_mtime("obj/main.o")
        new_mtime_core_o = get_mtime("obj/dandy_core.o")
        new_mtime_rom = get_mtime("bin/dandy.gb")
        
        if new_mtime_main_o <= mtime_main_o:
            print("FAIL: obj/main.o was not rebuilt after src/main.c modification.")
            return False
        if new_mtime_core_o != mtime_core_o:
            print("FAIL: obj/dandy_core.o was rebuilt when it should not have been (unaffected file).")
            return False
        if new_mtime_rom <= mtime_rom:
            print("FAIL: bin/dandy.gb was not rebuilt after main.o updated.")
            return False
            
        print("Pass: Incremental make rebuilt ONLY main.o and dandy.gb.")
        
        # Now do the same for dark
        mtime_main_dark_o = get_mtime("obj_dark/main.o")
        mtime_core_dark_o = get_mtime("obj_dark/dandy_core.o")
        mtime_rom_dark = get_mtime("bin/dandy_dark.gb")
        
        time.sleep(1.1)
        # Touch again
        with open(main_c_path, "a") as f:
            f.write("// Another dummy comment\n")
            
        print("Running make dark again...")
        res = run_cmd("make dark")
        if res.returncode != 0:
            print(f"FAIL: subsequent make dark failed: {res.stderr}")
            return False
            
        new_mtime_main_dark_o = get_mtime("obj_dark/main.o")
        new_mtime_core_dark_o = get_mtime("obj_dark/dandy_core.o")
        new_mtime_rom_dark = get_mtime("bin/dandy_dark.gb")
        
        if new_mtime_main_dark_o <= mtime_main_dark_o:
            print("FAIL: obj_dark/main.o was not rebuilt after src/main.c modification.")
            return False
        if new_mtime_core_dark_o != mtime_core_dark_o:
            print("FAIL: obj_dark/dandy_core.o was rebuilt when it should not have been.")
            return False
        if new_mtime_rom_dark <= mtime_rom_dark:
            print("FAIL: bin/dandy_dark.gb was not rebuilt.")
            return False
            
        print("Pass: Incremental make dark rebuilt ONLY main.o and dandy_dark.gb.")
        
    finally:
        # Restore original main.c
        with open(main_c_path, "w") as f:
            f.write(original_content)
        print("Restored original src/main.c.")
        
    print("=== BUILD SYSTEM STALE OBJECTS TEST PASSED SUCCESSFULLY ===")
    return True

if __name__ == "__main__":
    import sys
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
