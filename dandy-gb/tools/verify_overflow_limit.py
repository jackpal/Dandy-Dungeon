#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess

current_dir = os.path.dirname(os.path.abspath(__file__))
dandy_gb_dir = os.path.normpath(os.path.join(current_dir, ".."))
convert_script = os.path.join(current_dir, "convert_levels.py")
convert_backup = os.path.join(current_dir, "convert_levels.py.backup")

# Set GBDK environment
gbdk_bin_path = "/usr/local/google/home/jackpal/Developer/gbdk/bin"
env = os.environ.copy()
if os.path.exists(gbdk_bin_path):
    env["PATH"] = gbdk_bin_path + os.pathsep + env["PATH"]
    env["GBDKDIR"] = "/usr/local/google/home/jackpal/Developer/gbdk/"

def run_cmd(cmd, cwd=None):
    res = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return res.returncode, res.stdout.decode(), res.stderr.decode()

def main():
    if not os.path.exists(convert_script):
        print(f"Error: {convert_script} not found!")
        sys.exit(1)
        
    # Backup convert_levels.py
    print(f"Backing up {convert_script}...")
    shutil.copy(convert_script, convert_backup)
    
    try:
        # We will try compiling with different number of levels
        for num_levels in range(10, 27):
            print(f"\n--- Testing build with {num_levels} levels ---")
            
            # Read current file
            with open(convert_backup, "r") as f:
                content = f.read()
                
            # Replace the levels limit line
            # We want to replace levels = levels[:9] or whatever with levels = levels[:num_levels]
            modified_content = re.sub(
                r'levels\s*=\s*levels\[:\d+\]',
                f'levels = levels[:{num_levels}]',
                content
            )
            
            # Write modified file
            with open(convert_script, "w") as f:
                f.write(modified_content)
                
            # Run levels conversion
            print(f"Running level conversion for {num_levels} levels...")
            ret, out, err = run_cmd([sys.executable, "convert_levels.py"], cwd=current_dir)
            if ret != 0:
                print(f"Conversion failed for {num_levels} levels:")
                print(err)
                continue
                
            # Run clean and build
            print("Cleaning and compiling...")
            run_cmd(["make", "clean"], cwd=dandy_gb_dir)
            ret, out, err = run_cmd(["make"], cwd=dandy_gb_dir)
            
            if ret != 0:
                print(f"\033[91mBUILD FAILED at {num_levels} levels!\033[0m")
                print("Compiler/Linker Error Output:")
                print(err.strip())
                print(out.strip())
                break
            else:
                # Check if ROM exists and print size
                rom_path = os.path.join(dandy_gb_dir, "bin", "dandy.gb")
                if os.path.exists(rom_path):
                    rom_size = os.path.getsize(rom_path)
                    print(f"\033[92mBUILD SUCCESSFUL. ROM size: {rom_size} bytes\033[0m")
                else:
                    print("\033[91mBUILD SUCCESSFUL but ROM file not found!\033[0m")
                    break
                    
    finally:
        # Restore convert_levels.py
        print(f"\nRestoring {convert_script} from backup...")
        if os.path.exists(convert_backup):
            shutil.copy(convert_backup, convert_script)
            os.remove(convert_backup)
            print("Restoration complete.")

if __name__ == "__main__":
    import re
    main()
