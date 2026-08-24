#!/usr/bin/env python3
"""
test_silent_corruption.py
Tests if comments containing hex values inside tiles.c can cause silent corruption
by satisfying the 512-byte requirement while replacing actual compiled tiles.
"""

import os
import sys
import shutil
import subprocess

# Paths
C_TILES_PATH = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/tiles.c"
PYTHON_BIN = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/.venv/bin/python3"
VERIFY_SCRIPT = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/verify_graphics.py"
C_BACKUP = C_TILES_PATH + ".bak"

def setup_silent_corruption():
    print("Setting up silent corruption mock in tiles.c...")
    # Read the original tiles.c
    with open(C_TILES_PATH, 'r') as f:
        content = f.read()
        
    # We need to find the dandy_tiles array contents
    import re
    array_match = re.search(r'const\s+unsigned\s+char\s+dandy_tiles\[\]\s*=\s*\{([^}]+)\};', content)
    if not array_match:
        raise ValueError("Could not find dandy_tiles array in tiles.c")
        
    array_str = array_match.group(1)
    
    # Extract all hex values
    hex_vals = re.findall(r'0x[0-9a-fA-F]{2}', array_str)
    print(f"Original hex count: {len(hex_vals)}")
    
    # Take the first 31 tiles (31 * 16 = 496 bytes)
    truncated_hex_vals = hex_vals[:496]
    
    # Now, format the 31 tiles, and add the 32nd tile as a comment containing hex values
    hex_strs = []
    for i, val in enumerate(truncated_hex_vals):
        hex_strs.append(val)
        if (i + 1) % 16 == 0:
            hex_strs.append("\n")
            
    # Assemble the new array content
    new_array_content = ", ".join(hex_strs)
    # Add the comment representing the 32nd tile (16 bytes)
    comment_tile = "\n    /* Commented-out 32nd tile:\n    0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0x00\n    */\n"
    
    # Replace the old array with the new array
    modified = re.sub(
        r'const\s+unsigned\s+char\s+dandy_tiles\[\]\s*=\s*\{([^}]+)\};',
        f'const unsigned char dandy_tiles[] = {{\n{new_array_content},{comment_tile}}};',
        content
    )
    
    with open(C_TILES_PATH, 'w') as f:
        f.write(modified)

def main():
    # 1. Back up
    shutil.copy2(C_TILES_PATH, C_BACKUP)
    
    try:
        # 2. Setup mock
        setup_silent_corruption()
        
        # 3. Run verification script
        print("Running verify_graphics.py...")
        result = subprocess.run([PYTHON_BIN, VERIFY_SCRIPT], capture_output=True, text=True)
        
        print(f"Exit Code: {result.returncode}")
        if result.stdout:
            print("--- STDOUT ---")
            print(result.stdout.strip())
        if result.stderr:
            print("--- STDERR ---")
            print(result.stderr.strip())
            
        if result.returncode == 0:
            print("\n[VULNERABILITY CONFIRMED] Silent Corruption Vulnerability exists!")
            print("The script successfully parsed commented-out hex values, completed with exit code 0, and generated an audit sheet containing commented-out data as if it were compiled!")
            sys.exit(0)
        else:
            print("\n[SECURE] The script failed to parse the commented-out tiles (or detected the issue).")
            sys.exit(1)
            
    finally:
        # 4. Restore
        if os.path.exists(C_BACKUP):
            shutil.move(C_BACKUP, C_TILES_PATH)

if __name__ == "__main__":
    main()
