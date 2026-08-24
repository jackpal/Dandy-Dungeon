#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess

# Paths
REPO_DIR = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb"
TILES_C_PATH = os.path.join(REPO_DIR, "src", "tiles.c")
TILES_C_BAK_PATH = os.path.join(REPO_DIR, "src", "tiles.c.bak")
VERIFY_SCRIPT = os.path.join(REPO_DIR, "tools", "verify_graphics.py")
PYTHON_EXEC = os.path.join(REPO_DIR, ".venv", "bin", "python")

def build_mock_tiles_c(values):
    array_str = ", ".join(values)
    return f"""
    const unsigned char dandy_tiles[] = {{
        {array_str}
    }};
    """

def run_verify():
    res = subprocess.run(
        [PYTHON_EXEC, VERIFY_SCRIPT],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return res.returncode, res.stdout, res.stderr

def test_scenario(name, values, expected_err_substring):
    print(f"--- Running Test Scenario: {name} ---")
    mock_content = build_mock_tiles_c(values)
    with open(TILES_C_PATH, "w") as f:
        f.write(mock_content)
    
    code, stdout, stderr = run_verify()
    print(f"Exit Code: {code}")
    print(f"Stderr:\n{stderr.strip()}")
    
    # Assertions
    if code != 1:
        print(f"[-] FAIL: Expected exit code 1, got {code}")
        return False
    if "Validation Error:" not in stderr:
        print(f"[-] FAIL: Expected 'Validation Error:' prefix in stderr")
        return False
    if expected_err_substring.lower() not in stderr.lower():
        print(f"[-] FAIL: Expected substring '{expected_err_substring}' in stderr")
        return False
        
    print("[+] PASS")
    return True

def main():
    if not os.path.exists(TILES_C_PATH):
        print(f"Error: {TILES_C_PATH} not found.")
        sys.exit(1)
        
    # Backup original tiles.c
    print(f"Backing up {TILES_C_PATH} to {TILES_C_BAK_PATH}...")
    shutil.copy(TILES_C_PATH, TILES_C_BAK_PATH)
    
    success = True
    try:
        # Case 1: Truncated array
        values_truncated = ["0x00"] * 511
        if not test_scenario("Truncated tile array", values_truncated, "Expected exactly 512 values"):
            success = False
            
        # Case 2: Empty array
        values_empty = []
        if not test_scenario("Empty tile array", values_empty, "Expected exactly 512 values"):
            success = False
            
        # Case 3: Invalid hex characters (0xGG)
        values_invalid_hex = ["0x00"] * 512
        values_invalid_hex[15] = "0xGG"
        if not test_scenario("Invalid hex characters (0xGG)", values_invalid_hex, "Invalid token '0xGG'"):
            success = False
            
        # Case 4: Negative values (-1)
        values_negative = ["0x00"] * 512
        values_negative[42] = "-1"
        if not test_scenario("Negative values (-1)", values_negative, "Invalid token '-1'"):
            success = False
            
        # Case 5: Out-of-bounds numbers (256)
        values_oob_dec = ["0x00"] * 512
        values_oob_dec[100] = "256"
        if not test_scenario("Out-of-bounds decimal (256)", values_oob_dec, "out of 0-255 range"):
            success = False
            
        # Case 6: Out-of-bounds numbers (0x100)
        values_oob_hex = ["0x00"] * 512
        values_oob_hex[200] = "0x100"
        if not test_scenario("Out-of-bounds hex (0x100)", values_oob_hex, "out of 0-255 range"):
            success = False

        # Case 7: Negative hex (-0x01)
        values_negative_hex = ["0x00"] * 512
        values_negative_hex[10] = "-0x01"
        if not test_scenario("Negative hex (-0x01)", values_negative_hex, "Invalid token '-0x01'"):
            success = False

    finally:
        # Restore original tiles.c
        print(f"Restoring original {TILES_C_PATH} from backup...")
        shutil.copy(TILES_C_BAK_PATH, TILES_C_PATH)
        os.remove(TILES_C_BAK_PATH)
        print("Restored.")
        
    if success:
        print("\n[+] ALL EMPIRICAL TEST SCENARIOS PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("\n[-] SOME EMPIRICAL TEST SCENARIOS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
