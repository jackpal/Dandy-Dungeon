#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import shutil
import re

repo_dir = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb"

def get_tmp_files():
    try:
        return set(os.listdir("/tmp"))
    except Exception:
        return set()

def get_active_processes():
    # Get list of running processes for this user containing 'pyboy', 'python', or 'lcc'
    try:
        res = subprocess.run("ps -u $USER -o pid,comm,args", shell=True, stdout=subprocess.PIPE, text=True)
        return res.stdout.splitlines()
    except Exception:
        return []

def check_roms():
    dandy_path = os.path.join(repo_dir, "bin/dandy.gb")
    dandy_dark_path = os.path.join(repo_dir, "bin/dandy_dark.gb")
    dandy_exists = os.path.exists(dandy_path) and os.path.getsize(dandy_path) > 0
    dandy_dark_exists = os.path.exists(dandy_dark_path) and os.path.getsize(dandy_dark_path) > 0
    return dandy_exists, dandy_dark_exists

def check_pngs():
    downscale_path = os.path.join(repo_dir, "teamwork_graphics/downscale_preview.png")
    audit_path = os.path.join(repo_dir, "teamwork_graphics/graphics_audit.png")
    audit_dark_path = os.path.join(repo_dir, "teamwork_graphics/graphics_audit_dark.png")
    return os.path.exists(downscale_path), os.path.exists(audit_path), os.path.exists(audit_dark_path)

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, cwd=repo_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return res.returncode, res.stdout, res.stderr

def search_for_errors(stdout, stderr):
    combined = stdout + "\n" + stderr
    # Look for common compiler errors/warnings/collisions
    indicators = [
        r"(?i)error:",
        r"(?i)undefined identifier",
        r"(?i)warning:.*undefined",
        r"(?i)collision",
        r"(?i)stomp",
        r"(?i)permission denied",
        r"(?i)sharing violation",
        r"(?i)failed to write",
        r"(?i)multiple definition",
        r"(?i)syntax error",
        r"(?i)fatal error"
    ]
    found = []
    for pattern in indicators:
        matches = re.findall(pattern, combined)
        if matches:
            found.append(pattern)
    return found

def run_stress_tests():
    print("======================================================================")
    print("STARTING EMPIRICAL STRESS TESTS FOR BUILD SYSTEM REMEDIATION (ROUND 2)")
    print("======================================================================\n")

    passed_all = True
    iterations = 10

    # ----------------------------------------------------------------------
    # TEST 1: Parallel Clean Build Stress-Test (Scenario 1)
    # ----------------------------------------------------------------------
    print(f"--- TEST 1: Parallel Clean Build (make clean && make -j8 all dark) - {iterations} iterations ---")
    t1_failures = 0
    for i in range(1, iterations + 1):
        # Clean first
        run_cmd("make clean")
        
        # Run parallel build
        ret, out, err = run_cmd("make -j8 all dark")
        
        # Check results
        dandy, dandy_dark = check_roms()
        downscale, _, _ = check_pngs()
        errors = search_for_errors(out, err)
        
        if ret != 0 or not dandy or not dandy_dark or not downscale or errors:
            print(f"  [Iteration {i}] FAIL!")
            print(f"    Exit Code: {ret}")
            print(f"    ROMs: dandy.gb={dandy}, dandy_dark.gb={dandy_dark}")
            print(f"    Downscale PNG: {downscale}")
            print(f"    Errors detected in logs: {errors}")
            if err:
                print(f"    STDERR:\n{err}")
            t1_failures += 1
            passed_all = False
        else:
            print(f"  [Iteration {i}] PASS")
            
    if t1_failures == 0:
        print(f"==> TEST 1 RESULT: 100% SUCCESS (0/{iterations} failed)\n")
    else:
        print(f"==> TEST 1 RESULT: FAILED ({t1_failures}/{iterations} failed)\n")

    # ----------------------------------------------------------------------
    # TEST 2: Concurrent Parallel Build Stress-Test (Scenario 2)
    # ----------------------------------------------------------------------
    print(f"--- TEST 2: Concurrent Parallel Build (make -j8 all & make -j8 dark; wait) - {iterations} iterations ---")
    t2_failures = 0
    for i in range(1, iterations + 1):
        # Clean first
        run_cmd("make clean")
        
        # Run concurrent parallel builds in a wrapper to capture output
        ret, out, err = run_cmd("make -j8 all & make -j8 dark; wait")
        
        # Check results
        dandy, dandy_dark = check_roms()
        downscale, _, _ = check_pngs()
        errors = search_for_errors(out, err)
        
        if ret != 0 or not dandy or not dandy_dark or not downscale or errors:
            print(f"  [Iteration {i}] FAIL!")
            print(f"    Exit Code: {ret}")
            print(f"    ROMs: dandy.gb={dandy}, dandy_dark.gb={dandy_dark}")
            print(f"    Downscale PNG: {downscale}")
            print(f"    Errors detected in logs: {errors}")
            if err:
                print(f"    STDERR:\n{err}")
            t2_failures += 1
            passed_all = False
        else:
            print(f"  [Iteration {i}] PASS")
            
    if t2_failures == 0:
        print(f"==> TEST 2 RESULT: 100% SUCCESS (0/{iterations} failed)\n")
    else:
        print(f"==> TEST 2 RESULT: FAILED ({t2_failures}/{iterations} failed)\n")

    # ----------------------------------------------------------------------
    # TEST 3: Clean Target Integrity Check
    # ----------------------------------------------------------------------
    print("--- TEST 3: Clean Target Integrity Check ---")
    # First, run a full build & run test to generate all three PNGs
    run_cmd("make clean")
    run_cmd("make -j8 all dark")
    run_cmd("make test") # Generates the audit PNGs
    
    downscale, audit, audit_dark = check_pngs()
    print(f"  Generated PNGs before clean: downscale={downscale}, audit={audit}, audit_dark={audit_dark}")
    if not (downscale and audit and audit_dark):
        print("  FAIL: Not all three PNGs were successfully generated!")
        passed_all = False
    else:
        # Run clean
        ret, out, err = run_cmd("make clean")
        downscale_after, audit_after, audit_dark_after = check_pngs()
        print(f"  PNGs after clean: downscale={downscale_after}, audit={audit_after}, audit_dark={audit_dark_after}")
        
        # Check for other git-tracked files
        res = subprocess.run("git status --porcelain", shell=True, cwd=repo_dir, stdout=subprocess.PIPE, text=True)
        # We expect some modifications to Makefile, src/main.c etc because they are unstaged modifications in the workspace.
        # But we must NOT see any deleted source files that are git-tracked.
        untracked_deleted = [line for line in res.stdout.splitlines() if line.startswith(" D ")]
        
        if downscale_after or audit_after or audit_dark_after:
            print("  FAIL: Some generated PNG files were not deleted by make clean!")
            passed_all = False
        elif untracked_deleted:
            print(f"  FAIL: Git-tracked files were deleted: {untracked_deleted}")
            passed_all = False
        else:
            print("  PASS: Clean target integrity check succeeded. All generated PNGs deleted, no other assets deleted.")
            
    print("")

    # ----------------------------------------------------------------------
    # TEST 4: Test Suite Resource & Leak Audit
    # ----------------------------------------------------------------------
    print("--- TEST 4: Test Suite Resource & Leak Audit ---")
    # Capture initial state of /tmp and running processes
    tmp_before = get_tmp_files()
    procs_before = get_active_processes()
    
    test_runs = 3
    t4_passed = True
    
    for r in range(1, test_runs + 1):
        print(f"  Running test suite iteration {r}/{test_runs}...")
        
        # Run make test
        ret_test, out_test, err_test = run_cmd("make test")
        if ret_test != 0:
            print(f"    FAIL: 'make test' failed at iteration {r}!")
            print(f"    STDERR:\n{err_test}")
            t4_passed = False
            passed_all = False
            break
            
        # Run make test_emu
        ret_emu, out_emu, err_emu = run_cmd("make test_emu")
        if ret_emu != 0:
            print(f"    FAIL: 'make test_emu' failed at iteration {r}!")
            print(f"    STDERR:\n{err_emu}")
            t4_passed = False
            passed_all = False
            break
            
    if t4_passed:
        print("  Checking for leaks...")
        tmp_after = get_tmp_files()
        procs_after = get_active_processes()
        
        # Compare /tmp files
        leaked_tmp = tmp_after - tmp_before
        actual_leaked_tmp = []
        for f in leaked_tmp:
            # Filter out standard system/desktop temp files
            if f.startswith("systemd-private-") or f.startswith(".font-unix") or f.startswith(".ICE-unix") or f.startswith(".X11-unix"):
                continue
            actual_leaked_tmp.append(f)
            
        # Compare running processes
        leaked_procs = []
        # Look for new pyboy or python processes that might be lingering
        for p in procs_after:
            if p not in procs_before:
                if 'pyboy' in p.lower() or 'python' in p.lower() or 'lcc' in p.lower():
                    leaked_procs.append(p)
                    
        if actual_leaked_tmp:
            print(f"    FAIL: Leaked temp files/directories in /tmp: {actual_leaked_tmp}")
            passed_all = False
        elif leaked_procs:
            print(f"    FAIL: Leaked background processes: {leaked_procs}")
            passed_all = False
        else:
            print("    PASS: No temporary directories or processes leaked. All resources cleanly reclaimed.")
    else:
        print("  FAIL: Test execution was unstable or failed.")

    print("\n======================================================================")
    if passed_all:
        print("OVERALL VERDICT: PASS")
    else:
        print("OVERALL VERDICT: FAIL")
    print("======================================================================")
    
    if passed_all:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    run_stress_tests()
