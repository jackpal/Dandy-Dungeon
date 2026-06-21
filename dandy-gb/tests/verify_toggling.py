#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import shutil

repo_dir = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb"

def run_cmd(cmd, cwd=repo_dir):
    res = subprocess.run(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return res

def check_result(res, msg):
    if res.returncode != 0:
        print(f"FAIL: {msg}\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}")
        sys.exit(1)

def main():
    print("Starting build toggling verification...")
    
    # 1. Clean build
    print("Running make clean...")
    res = run_cmd("make clean")
    check_result(res, "make clean failed")
        
    if os.path.exists(os.path.join(repo_dir, "obj")) or os.path.exists(os.path.join(repo_dir, "obj_dark")):
        print("FAIL: obj or obj_dark still exist after make clean")
        sys.exit(1)
        
    # 2. Build Classic DMG
    print("Running make...")
    res = run_cmd("make")
    check_result(res, "make failed")
        
    if not os.path.exists(os.path.join(repo_dir, "bin/dandy.gb")):
        print("FAIL: bin/dandy.gb was not created")
        sys.exit(1)
        
    if os.path.exists(os.path.join(repo_dir, "obj_dark")):
        print("FAIL: obj_dark was created during classic build")
        sys.exit(1)
        
    expected_objs = ["main.o", "dandy_core.o", "gameboy_hal.o", "levels.o", "tiles.o"]
    for obj in expected_objs:
        p = os.path.join(repo_dir, "obj", obj)
        if not os.path.exists(p):
            print(f"FAIL: Expected object {p} does not exist")
            sys.exit(1)
            
    # Record initial timestamps for Classic objects
    classic_timestamps = {}
    for obj in expected_objs:
        p = os.path.join(repo_dir, "obj", obj)
        classic_timestamps[obj] = os.path.getmtime(p)
        
    # 3. Build Atmospheric Dark
    print("Running make dark...")
    res = run_cmd("make dark")
    check_result(res, "make dark failed")
        
    if not os.path.exists(os.path.join(repo_dir, "bin/dandy_dark.gb")):
        print("FAIL: bin/dandy_dark.gb was not created")
        sys.exit(1)
        
    for obj in expected_objs:
        p = os.path.join(repo_dir, "obj_dark", obj)
        if not os.path.exists(p):
            print(f"FAIL: Expected dark object {p} does not exist")
            sys.exit(1)
            
    # Record initial timestamps for Dark objects
    dark_timestamps = {}
    for obj in expected_objs:
        p = os.path.join(repo_dir, "obj_dark", obj)
        dark_timestamps[obj] = os.path.getmtime(p)
        
    # Wait 1 second to ensure file system timestamp resolution catches changes
    time.sleep(1.1)
    
    # 4. Modify src/main.c
    main_c_path = os.path.join(repo_dir, "src/main.c")
    print(f"Modifying {main_c_path}...")
    with open(main_c_path, "r") as f:
        content = f.read()
    # Append a harmless space to trigger rebuild
    with open(main_c_path, "w") as f:
        f.write(content + " ")
        
    try:
        # 5. Run make again (Classic)
        print("Running make again...")
        res = run_cmd("make")
        check_result(res, "make failed after modification")
        print(f"Rebuild make stdout:\n{res.stdout}")
            
        # Verify only main.o in obj/ was recompiled (or tiles.o if sprites target updated it, but let's check main.o first)
        new_classic_timestamps = {}
        for obj in expected_objs:
            p = os.path.join(repo_dir, "obj", obj)
            new_classic_timestamps[obj] = os.path.getmtime(p)
            print(f"obj/{obj}: classic_timestamp={classic_timestamps[obj]}, new={new_classic_timestamps[obj]}, diff={new_classic_timestamps[obj] - classic_timestamps[obj]}")
            
        if new_classic_timestamps["main.o"] <= classic_timestamps["main.o"]:
            print("FAIL: obj/main.o was NOT recompiled after modifying src/main.c")
            sys.exit(1)
            
        # Other files like dandy_core.o and gameboy_hal.o should NOT be recompiled
        for obj in ["dandy_core.o", "gameboy_hal.o"]:
            if new_classic_timestamps[obj] > classic_timestamps[obj]:
                print(f"FAIL: obj/{obj} was unnecessarily recompiled (diff={new_classic_timestamps[obj] - classic_timestamps[obj]})")
                sys.exit(1)
                
        # Verify obj_dark/main.o has NOT changed yet!
        new_dark_timestamps_before = {}
        for obj in expected_objs:
            p = os.path.join(repo_dir, "obj_dark", obj)
            new_dark_timestamps_before[obj] = os.path.getmtime(p)
            
        if new_dark_timestamps_before["main.o"] > dark_timestamps["main.o"]:
            print("FAIL: obj_dark/main.o was compiled during classic build")
            sys.exit(1)
            
        # Wait again
        time.sleep(1.1)
        
        # 6. Run make dark again
        print("Running make dark again...")
        res = run_cmd("make dark")
        check_result(res, "make dark failed after modification")
            
        new_dark_timestamps_after = {}
        for obj in expected_objs:
            p = os.path.join(repo_dir, "obj_dark", obj)
            new_dark_timestamps_after[obj] = os.path.getmtime(p)
            
        if new_dark_timestamps_after["main.o"] <= dark_timestamps["main.o"]:
            print("FAIL: obj_dark/main.o was NOT recompiled after modifying src/main.c")
            sys.exit(1)
            
        for obj in ["dandy_core.o", "gameboy_hal.o"]:
            if new_dark_timestamps_after[obj] > dark_timestamps[obj]:
                print(f"FAIL: obj_dark/{obj} was unnecessarily recompiled")
                sys.exit(1)
                
        print("SUCCESS: Build toggling and recompilation logic verified successfully!")
        
    finally:
        # Restore src/main.c to original state
        with open(main_c_path, "w") as f:
            f.write(content)

if __name__ == "__main__":
    main()
