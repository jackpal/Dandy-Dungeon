import os
import sys
import shutil
import subprocess
import re

# Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.normpath(os.path.join(current_dir, "../.."))
tiles_c_path = os.path.join(repo_root, "dandy-gb/src/tiles.c")
tiles_c_backup = os.path.join(repo_root, "dandy-gb/src/tiles.c.bak")
strike_png_path = os.path.join(repo_root, "dandy-gb/teamwork_graphics/strike_original.png")
strike_png_backup = os.path.join(repo_root, "dandy-gb/teamwork_graphics/strike_original.png.bak")
verifier_path = os.path.join(repo_root, "dandy-gb/tools/verify_graphics.py")
venv_python = os.path.join(repo_root, "dandy-gb/.venv/bin/python")

# Read original tiles.c
with open(tiles_c_path, "r") as f:
    original_tiles_c = f.read()

def setup_backups():
    if not os.path.exists(tiles_c_backup):
        shutil.copy2(tiles_c_path, tiles_c_backup)
    if os.path.exists(strike_png_path) and not os.path.exists(strike_png_backup):
        shutil.copy2(strike_png_path, strike_png_backup)

def restore_backups():
    if os.path.exists(tiles_c_backup):
        shutil.copy2(tiles_c_backup, tiles_c_path)
        os.remove(tiles_c_backup)
    if os.path.exists(strike_png_backup):
        shutil.copy2(strike_png_backup, strike_png_path)
        os.remove(strike_png_backup)

def run_verifier():
    result = subprocess.run([venv_python, verifier_path], capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def run_test_case(name, setup_fn, expect_success=True):
    print(f"Running Test Case: {name} ... ", end="")
    setup_fn()
    success, stdout, stderr = run_verifier()
    
    # Clean up state immediately after run
    restore_backups()
    
    if success == expect_success:
        print("PASS")
        return True
    else:
        print("FAIL")
        print(f"  Expected Success: {expect_success}, Got: {success}")
        print(f"  Stdout: {stdout.strip()}")
        print(f"  Stderr: {stderr.strip()}")
        return False

def main():
    setup_backups()
    failures = 0
    
    try:
        # Test Case 1: Baseline (Should succeed)
        def setup_baseline():
            pass # Use original files
        if not run_test_case("Baseline (Original files)", setup_baseline, expect_success=True):
            failures += 1

        # Test Case 2: Missing tiles.c
        def setup_missing_tiles_c():
            if os.path.exists(tiles_c_path):
                os.remove(tiles_c_path)
        if not run_test_case("Missing tiles.c", setup_missing_tiles_c, expect_success=False):
            # We expect a failure (FileNotFoundError)
            pass

        # Test Case 3: Explicit array size in C
        # e.g., const unsigned char dandy_tiles[512] = { ... };
        # This is extremely common C syntax.
        def setup_explicit_size():
            modified = original_tiles_c.replace("dandy_tiles[]", "dandy_tiles[512]")
            with open(tiles_c_path, "w") as f:
                f.write(modified)
        if not run_test_case("Explicit Array Size dandy_tiles[512]", setup_explicit_size, expect_success=False):
            # We expect it to FAIL because the regex expects empty brackets []
            pass

        # Test Case 4: Uppercase hex prefix 0X
        # e.g. 0X00 instead of 0x00
        def setup_uppercase_hex():
            modified = original_tiles_c.replace("0x", "0X").replace("0X2bpp", "0x2bpp") # avoid replacing comments if any
            with open(tiles_c_path, "w") as f:
                f.write(modified)
        if not run_test_case("Uppercase Hex Prefix 0X", setup_uppercase_hex, expect_success=False):
            # We expect it to FAIL because the regex expects lowercase '0x'
            pass

        # Test Case 5: Comments containing hex values inside the array
        # This will trick the regex into matching the comment value as a tile byte
        def setup_comment_hex():
            # Let's insert a comment like /* index 0x00 */ inside the array content
            modified = original_tiles_c.replace("const unsigned char dandy_tiles[] = {", 
                                                "const unsigned char dandy_tiles[] = {\n    /* offset 0xAA */")
            with open(tiles_c_path, "w") as f:
                f.write(modified)
        if not run_test_case("Hex in Comments inside Array", setup_comment_hex, expect_success=False):
            # We expect it to FAIL because the count of hex values will be 513 instead of 512
            pass

        # Test Case 6: Missing strike_original.png
        def setup_missing_png():
            if os.path.exists(strike_png_path):
                os.remove(strike_png_path)
        if not run_test_case("Missing strike_original.png", setup_missing_png, expect_success=False):
            # We expect it to FAIL (FileNotFoundError)
            pass

    finally:
        restore_backups()

    if failures == 0:
        print("\n[+] All verifier stress-test scenarios run successfully.")
    else:
        print(f"\n[-] Found {failures} unexpected failures in verifier stress-tests.")
        sys.exit(1)

if __name__ == "__main__":
    main()
