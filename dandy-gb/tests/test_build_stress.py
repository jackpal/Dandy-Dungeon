#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil

repo_dir = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb"

def get_tmp_files():
    try:
        return set(os.listdir("/tmp"))
    except Exception:
        return set()

def main():
    print("Starting clean build stress test (10 iterations)...")
    
    # Capture initial state of /tmp
    tmp_before = get_tmp_files()
    
    # Capture initial untracked/ignored files in workspace
    res = subprocess.run("git status --ignored --porcelain", shell=True, cwd=repo_dir, stdout=subprocess.PIPE, text=True)
    workspace_before = set(res.stdout.splitlines())
    
    iterations = 10
    success = True
    
    for i in range(1, iterations + 1):
        print(f"Iteration {i}/{iterations}...")
        # Run clean and build
        res = subprocess.run("make clean && make", shell=True, cwd=repo_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"FAIL: Build failed at iteration {i}!")
            print(f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}")
            success = False
            break
            
    if not success:
        sys.exit(1)
        
    print("Builds completed successfully. Checking for leaks...")
    
    # Check /tmp leaks
    tmp_after = get_tmp_files()
    leaked_tmp = tmp_after - tmp_before
    # Filter out common system temp files if any (e.g. Chrome, systemd, etc.)
    # We only care about leaks from our tools (usually starting with 'tmp' or similar python temp patterns, or gbdk files)
    actual_leaked_tmp = []
    for f in leaked_tmp:
        # Ignore common system files
        if f.startswith("systemd-private-") or f.startswith(".font-unix") or f.startswith(".ICE-unix"):
            continue
        actual_leaked_tmp.append(f)
        
    if actual_leaked_tmp:
        print(f"FAIL: Leaked files/directories found in /tmp: {actual_leaked_tmp}")
        success = False
    else:
        print("PASS: No temporary files/directories leaked in /tmp.")
        
    # Check workspace leaks (files created but not cleaned by make clean)
    # Let's run make clean first to see if it cleans everything it should
    print("Running make clean for final workspace check...")
    subprocess.run("make clean", shell=True, cwd=repo_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    res = subprocess.run("git status --ignored --porcelain", shell=True, cwd=repo_dir, stdout=subprocess.PIPE, text=True)
    workspace_after = set(res.stdout.splitlines())
    
    leaked_workspace = workspace_after - workspace_before
    if leaked_workspace:
        print(f"FAIL: Leaked untracked/ignored files found in workspace after make clean: {leaked_workspace}")
        success = False
    else:
        print("PASS: No leaked files in workspace after make clean.")
        
    if success:
        print("Stress test PASSED successfully!")
        sys.exit(0)
    else:
        print("Stress test FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()
