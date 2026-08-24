import os
import subprocess
import sys
import glob
import psutil

def get_temp_dirs():
    # Find all temp directories matching /tmp/tmp*
    return set(glob.glob("/tmp/tmp*"))

def get_matching_processes():
    # Find all running processes matching python/pyboy/lcc
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline:
                cmdline_str = " ".join(cmdline).lower()
                if "python" in cmdline_str or "pyboy" in cmdline_str or "lcc" in cmdline_str:
                    processes.append((proc.info['pid'], cmdline_str))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return processes

def run_iteration(iteration_num):
    print(f"\n=== Resource Audit Iteration {iteration_num} ===")
    
    # Pre-run state
    temp_dirs_before = get_temp_dirs()
    procs_before = get_matching_processes()
    
    print(f"Before run: {len(temp_dirs_before)} temp dirs in /tmp, {len(procs_before)} active python/pyboy/lcc processes.")
    
    # Run make test
    print("Running: make test...")
    res_test = subprocess.run(["make", "test"], cwd="/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb", capture_output=True, text=True)
    if res_test.returncode != 0:
        print("ERROR: 'make test' failed!")
        print("STDOUT:\n", res_test.stdout)
        print("STDERR:\n", res_test.stderr)
        return False
    else:
        print("make test passed successfully.")
        
    # Run make test_emu
    print("Running: make test_emu...")
    res_emu = subprocess.run(["make", "test_emu"], cwd="/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb", capture_output=True, text=True)
    if res_emu.returncode != 0:
        print("ERROR: 'make test_emu' failed!")
        print("STDOUT:\n", res_emu.stdout)
        print("STDERR:\n", res_emu.stderr)
        return False
    else:
        print("make test_emu passed successfully.")
        
    # Post-run state
    temp_dirs_after = get_temp_dirs()
    procs_after = get_matching_processes()
    
    # Calculate leaks
    leaked_dirs = temp_dirs_after - temp_dirs_before
    # Filter out processes that were already running before
    leaked_procs = [p for p in procs_after if p not in procs_before]
    
    print(f"After run: {len(temp_dirs_after)} temp dirs in /tmp, {len(procs_after)} active processes.")
    
    success = True
    if leaked_dirs:
        print(f"FAIL: Leaked {len(leaked_dirs)} temp directories: {leaked_dirs}")
        success = False
    else:
        print("PASS: No temp directories leaked.")
        
    if leaked_procs:
        print(f"FAIL: Leaked {len(leaked_procs)} processes: {leaked_procs}")
        success = False
    else:
        print("PASS: No processes leaked.")
        
    return success

def main():
    success = True
    for i in range(1, 4):
        # Run clean before each iteration to start fresh
        subprocess.run(["make", "clean"], cwd="/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb", capture_output=True)
        if not run_iteration(i):
            success = False
            
    if success:
        print("\nALL 3 ITERATIONS COMPLETED WITH ZERO LEAKS. VERDICT: PASS")
        sys.exit(0)
    else:
        print("\nLEAKS OR FAILURES DETECTED IN ONE OR MORE ITERATIONS. VERDICT: FAIL")
        sys.exit(1)

if __name__ == "__main__":
    main()
