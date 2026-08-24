#!/usr/bin/env python3
import os
import shutil
import subprocess
import tempfile
import sys

ORIGINAL_WORKSPACE = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb"
ORIGINAL_JS = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-js"

def log(msg):
    print(f"[ISOLATED-EMU-TEST] {msg}", flush=True)

def run_cmd(cmd, cwd):
    res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return res

def main():
    with tempfile.TemporaryDirectory(prefix="dandy_emu_sandbox_") as sandbox_dir:
        log(f"Setting up isolated sandbox in {sandbox_dir}...")
        isolated_gb = os.path.join(sandbox_dir, "dandy-gb")
        isolated_js = os.path.join(sandbox_dir, "dandy-js")
        
        os.makedirs(isolated_gb, exist_ok=True)
        os.symlink(ORIGINAL_JS, isolated_js)
        
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
                
        # Symlink virtual env
        os.symlink(os.path.join(ORIGINAL_WORKSPACE, ".venv"), os.path.join(isolated_gb, ".venv"))
        log("Sandbox ready. Starting compilation...")
        
        # Build both ROMs
        res = run_cmd("make clean && make && make dark", isolated_gb)
        if res.returncode != 0:
            log(f"FAIL: Compilation failed: {res.stderr}")
            sys.exit(1)
        log("Compilation successful. Running PyBoy emulator E2E tests...")
        
        # Run test_emu
        res = run_cmd("make test_emu", isolated_gb)
        log(f"Stdout:\n{res.stdout}")
        log(f"Stderr:\n{res.stderr}")
        
        if res.returncode == 0:
            log("PASS: PyBoy E2E emulator tests passed successfully for both Classic and Atmospheric Dark ROMs!")
            sys.exit(0)
        else:
            log("FAIL: PyBoy E2E emulator tests failed.")
            sys.exit(1)

if __name__ == "__main__":
    main()
