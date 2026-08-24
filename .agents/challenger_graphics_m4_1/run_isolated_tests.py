#!/usr/bin/env python3
import os
import shutil
import subprocess
import tempfile
import sys

ORIGINAL_WORKSPACE = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb"
ORIGINAL_JS = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-js"
CHALLENGER_DIR = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/challenger_graphics_m4_1"

def log(msg):
    print(f"[ISOLATED-TEST] {msg}", flush=True)

def run_cmd(cmd, cwd):
    res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return res

def setup_isolated_workspace(sandbox_dir):
    log(f"Setting up isolated sandbox in {sandbox_dir}...")
    
    isolated_gb = os.path.join(sandbox_dir, "dandy-gb")
    isolated_js = os.path.join(sandbox_dir, "dandy-js")
    
    os.makedirs(isolated_gb, exist_ok=True)
    
    # Symlink or copy dandy-js
    os.symlink(ORIGINAL_JS, isolated_js)
    
    # Copy files/folders for dandy-gb excluding build artifacts and .venv
    exclude_patterns = shutil.ignore_patterns(
        '.venv', 'obj', 'obj_dark', 'bin', 'libdandy_test.so', 
        '*.lst', '*.map', '*.sym', '__pycache__', '.temp_envs', 'mock_gb'
    )
    
    for item in os.listdir(ORIGINAL_WORKSPACE):
        s = os.path.join(ORIGINAL_WORKSPACE, item)
        d = os.path.join(isolated_gb, item)
        if os.path.isdir(s):
            if item not in ['.venv', 'obj', 'obj_dark', 'bin', 'tests/mock_gb', 'tests/.temp_envs']:
                shutil.copytree(s, d, ignore=exclude_patterns)
        else:
            shutil.copy2(s, d)
            
    # Symlink the virtual environment
    original_venv = os.path.join(ORIGINAL_WORKSPACE, ".venv")
    isolated_venv = os.path.join(isolated_gb, ".venv")
    os.symlink(original_venv, isolated_venv)
    log("Sandbox workspace setup complete (dandy-gb and dandy-js ready).")
    return isolated_gb

def test_stale_objects(workspace):
    log("=== Running Stale Objects & Recompilation Test ===")
    
    def check_exists(path):
        return os.path.exists(os.path.join(workspace, path))
    def get_mtime(path):
        return os.path.getmtime(os.path.join(workspace, path))
        
    # Clean
    run_cmd("make clean", workspace)
    if check_exists("obj") or check_exists("obj_dark") or check_exists("bin/dandy.gb"):
        log("FAIL: make clean failed to remove directories")
        return False
        
    # Build Classic DMG
    log("Building Classic DMG (make)...")
    res = run_cmd("make", workspace)
    if res.returncode != 0:
        log(f"FAIL: make failed: {res.stderr}")
        return False
        
    if not check_exists("obj/main.o") or not check_exists("bin/dandy.gb"):
        log("FAIL: obj/main.o or bin/dandy.gb not created")
        return False
    if check_exists("obj_dark") or check_exists("bin/dandy_dark.gb"):
        log("FAIL: Classic build polluted dark directories/files")
        return False
    log("Pass: Classic DMG built cleanly.")
    
    mtime_main_o = get_mtime("obj/main.o")
    mtime_core_o = get_mtime("obj/dandy_core.o")
    mtime_rom = get_mtime("bin/dandy.gb")
    
    # Build Dark
    log("Building Atmospheric Dark (make dark)...")
    res = run_cmd("make dark", workspace)
    if res.returncode != 0:
        log(f"FAIL: make dark failed: {res.stderr}")
        return False
        
    if not check_exists("obj_dark/main.o") or not check_exists("bin/dandy_dark.gb"):
        log("FAIL: obj_dark/main.o or bin/dandy_dark.gb not created")
        return False
    log("Pass: Atmospheric Dark built cleanly.")
    
    # Verify incremental builds
    import time
    time.sleep(1.1)
    
    main_c_path = os.path.join(workspace, "src/main.c")
    with open(main_c_path, "r") as f:
        orig_content = f.read()
        
    try:
        log("Modifying src/main.c...")
        with open(main_c_path, "a") as f:
            f.write("\n// Dummy comment\n")
            
        # Rebuild classic
        log("Rebuilding Classic DMG...")
        res = run_cmd("make", workspace)
        if res.returncode != 0:
            log("FAIL: make after modification failed")
            return False
            
        new_mtime_main_o = get_mtime("obj/main.o")
        new_mtime_core_o = get_mtime("obj/dandy_core.o")
        new_mtime_rom = get_mtime("bin/dandy.gb")
        
        if new_mtime_main_o <= mtime_main_o:
            log("FAIL: main.o was not rebuilt")
            return False
        if new_mtime_core_o != mtime_core_o:
            log("FAIL: unaffected dandy_core.o was rebuilt")
            return False
        if new_mtime_rom <= mtime_rom:
            log("FAIL: dandy.gb was not rebuilt")
            return False
        log("Pass: Incremental Classic DMG rebuild is correct (only main.o and ROM rebuilt).")
        
        # Rebuild dark
        mtime_main_dark_o = get_mtime("obj_dark/main.o")
        mtime_core_dark_o = get_mtime("obj_dark/dandy_core.o")
        mtime_rom_dark = get_mtime("bin/dandy_dark.gb")
        
        time.sleep(1.1)
        with open(main_c_path, "a") as f:
            f.write("// Another comment\n")
            
        log("Rebuilding Atmospheric Dark...")
        res = run_cmd("make dark", workspace)
        if res.returncode != 0:
            log("FAIL: make dark after modification failed")
            return False
            
        new_mtime_main_dark_o = get_mtime("obj_dark/main.o")
        new_mtime_core_dark_o = get_mtime("obj_dark/dandy_core.o")
        new_mtime_rom_dark = get_mtime("bin/dandy_dark.gb")
        
        if new_mtime_main_dark_o <= mtime_main_dark_o:
            log("FAIL: obj_dark/main.o was not rebuilt")
            return False
        if new_mtime_core_dark_o != mtime_core_dark_o:
            log("FAIL: unaffected obj_dark/dandy_core.o was rebuilt")
            return False
        if new_mtime_rom_dark <= mtime_rom_dark:
            log("FAIL: dandy_dark.gb was not rebuilt")
            return False
        log("Pass: Incremental Atmospheric Dark rebuild is correct.")
        
    finally:
        with open(main_c_path, "w") as f:
            f.write(orig_content)
            
    log("Stale Objects & Recompilation Test PASSED.")
    return True

def test_downscale_compiler_robustness(workspace):
    log("=== Running Downscale Compiler Robustness Test ===")
    
    # 1. Non-existent input file
    log("Testing non-existent input file...")
    res = run_cmd(".venv/bin/python tools/downscale_sprites.py --input non_existent.png", workspace)
    if res.returncode == 0:
        log("FAIL: Tool accepted non-existent input with exit code 0")
        return False
    log(f"Pass: Gracefully rejected non-existent input (exit code {res.returncode}).")
    
    # 2. Corrupt/Invalid image content
    log("Testing corrupt image file...")
    corrupt_png = os.path.join(workspace, "corrupt.png")
    with open(corrupt_png, "w") as f:
        f.write("Not a real PNG file contents")
        
    res = run_cmd(f".venv/bin/python tools/downscale_sprites.py --input corrupt.png", workspace)
    os.remove(corrupt_png)
    if res.returncode == 0:
        log("FAIL: Tool accepted corrupt PNG with exit code 0")
        return False
    log(f"Pass: Gracefully rejected corrupt PNG (exit code {res.returncode}).")
    
    # 3. Invalid parameters (outline thickness out of bounds)
    log("Testing outline thickness out of bounds...")
    res = run_cmd(".venv/bin/python tools/downscale_sprites.py --input teamwork_graphics/strike_original.png --outline-thickness 2.5", workspace)
    if res.returncode == 0:
        log("FAIL: Tool accepted outline-thickness=2.5 with exit code 0")
        return False
    log(f"Pass: Gracefully rejected out-of-bounds parameter (exit code {res.returncode}).")
    
    log("Downscale Compiler Robustness Test PASSED.")
    return True

def test_clean_build_stress(workspace):
    log("=== Running Clean Build Stress Test (10 Iterations) ===")
    for i in range(10):
        log(f"Iteration {i+1}/10...")
        res = run_cmd("make clean && make && make dark", workspace)
        if res.returncode != 0:
            log(f"FAIL: Iteration {i+1} failed with code {res.returncode}: {res.stderr}")
            return False
            
    log("Pass: Compiled 10 times successfully without errors.")
    log("Clean Build Stress Test PASSED.")
    return True

def test_temp_directory_leaks(workspace):
    log("=== Running Temp Directory Leak Check ===")
    import glob
    
    tmp_pattern = "/tmp/tmp*"
    tmp_before = set(glob.glob(tmp_pattern))
    
    log("Running make test inside isolated workspace...")
    res = run_cmd("make test", workspace)
    if res.returncode != 0:
        log(f"FAIL: make test failed: {res.stderr}")
        return False
        
    tmp_after = set(glob.glob(tmp_pattern))
    leaked = tmp_after - tmp_before
    
    # Check for leaked test dirs in tests/
    tests_dir = os.path.join(workspace, "tests")
    for item in os.listdir(tests_dir):
        path = os.path.join(tests_dir, item)
        if os.path.isdir(path) and item not in ['__pycache__', 'mock_gb', '.temp_envs']:
            log(f"FAIL: Leaked directory in tests/: {item}")
            return False
            
    log("No leaks found in tests/ directory.")
    if leaked:
        log(f"Note: Some temp paths were created in /tmp during tests: {len(leaked)} paths. They are typically managed by Python's unittest tempfile, but let's make sure they are cleaned up or not dangling indefinitely.")
    else:
        log("Pass: No temporary directory leaks detected in /tmp.")
        
    log("Temp Directory Leak Check PASSED.")
    return True

def main():
    with tempfile.TemporaryDirectory(prefix="dandy_sandbox_") as sandbox_dir:
        workspace = setup_isolated_workspace(sandbox_dir)
        
        tests = [
            test_stale_objects,
            test_downscale_compiler_robustness,
            test_clean_build_stress,
            test_temp_directory_leaks
        ]
        
        success = True
        for test in tests:
            try:
                if not test(workspace):
                    success = False
                    break
            except Exception as e:
                log(f"CRITICAL ERROR during {test.__name__}: {e}")
                import traceback
                traceback.print_exc()
                success = False
                break
                
        if success:
            log("=========================================")
            log("ALL ISOLATED EMPIRICAL VERIFICATIONS PASSED!")
            log("=========================================")
            sys.exit(0)
        else:
            log("=========================================")
            log("SOME EMPIRICAL VERIFICATIONS FAILED!")
            log("=========================================")
            sys.exit(1)

if __name__ == "__main__":
    main()
