#!/usr/bin/env python3
"""
test_robustness.py
Adversarial robustness testing for dandy-gb/tools/verify_graphics.py.
"""

import os
import sys
import shutil
import subprocess

# Paths
JS_STRIKE_PATH = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-js/strike.js"
C_TILES_PATH = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/tiles.c"
PYTHON_BIN = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/.venv/bin/python3"
VERIFY_SCRIPT = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/verify_graphics.py"

# Backups
JS_BACKUP = JS_STRIKE_PATH + ".bak"
C_BACKUP = C_TILES_PATH + ".bak"

def setup_backups():
    print("Setting up backups...")
    shutil.copy2(JS_STRIKE_PATH, JS_BACKUP)
    shutil.copy2(C_TILES_PATH, C_BACKUP)

def restore_backups():
    print("Restoring backups...")
    if os.path.exists(JS_BACKUP):
        shutil.move(JS_BACKUP, JS_STRIKE_PATH)
    if os.path.exists(C_BACKUP):
        shutil.move(C_BACKUP, C_TILES_PATH)

def run_verify():
    result = subprocess.run([PYTHON_BIN, VERIFY_SCRIPT], capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def run_test_case(name, setup_fn):
    print(f"\n--- Running Test Case: {name} ---")
    setup_backups()
    try:
        setup_fn()
        code, stdout, stderr = run_verify()
        print(f"Exit Code: {code}")
        if stdout:
            print("--- STDOUT ---")
            print(stdout.strip())
        if stderr:
            print("--- STDERR ---")
            print(stderr.strip())
        return code, stdout, stderr
    finally:
        restore_backups()

# --- Test Case Setups ---

def setup_missing_strike_js():
    os.remove(JS_STRIKE_PATH)

def setup_missing_tiles_c():
    os.remove(C_TILES_PATH)

def setup_corrupt_base64():
    # Replace strike.js with a version that has invalid base64 content
    with open(JS_STRIKE_PATH, 'w') as f:
        f.write('const strike = new Image();\n')
        f.write('strike.src = "data:image/png;base64,invalid_base64_content!!!";\n')

def setup_extra_double_quotes():
    # Add an extra double quoted string variable
    with open(JS_BACKUP, 'r') as f:
        content = f.read()
    # Insert a dummy string at the top
    modified = 'const dummy = "this is an extra string that will break base64";\n' + content
    with open(JS_STRIKE_PATH, 'w') as f:
        f.write(modified)

def setup_comments_in_tiles():
    # Insert comments containing hex numbers in tiles.c
    with open(C_BACKUP, 'r') as f:
        content = f.read()
    # We will insert a comment /* 0xAA 0xBB */ inside the array
    # Let's find the opening brace and insert it right after
    modified = content.replace('{', '{ /* 0xAA 0xBB comment with hex */', 1)
    with open(C_TILES_PATH, 'w') as f:
        f.write(modified)

def setup_syntax_change_in_tiles():
    # Change const unsigned char dandy_tiles[] to unsigned char dandy_tiles[]
    with open(C_BACKUP, 'r') as f:
        content = f.read()
    modified = content.replace('const unsigned char dandy_tiles[]', 'unsigned char dandy_tiles[]')
    with open(C_TILES_PATH, 'w') as f:
        f.write(modified)

def setup_incorrect_tile_count():
    # We will truncate the tiles array to only have 16 bytes (1 tile)
    with open(C_BACKUP, 'r') as f:
        content = f.read()
    # Find the array content and replace it with just 16 bytes
    # A simple regex replacement
    import re
    modified = re.sub(
        r'const\s+unsigned\s+char\s+dandy_tiles\[\]\s*=\s*\{([^}]+)\};',
        'const unsigned char dandy_tiles[] = { 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f };',
        content
    )
    with open(C_TILES_PATH, 'w') as f:
        f.write(modified)

# --- Main runner ---

def main():
    results = {}
    
    # 1. Missing strike.js
    code, out, err = run_test_case("Missing strike.js", setup_missing_strike_js)
    results["Missing strike.js"] = (code == 1 and "FileNotFoundError" in err)
    
    # 2. Missing tiles.c
    code, out, err = run_test_case("Missing tiles.c", setup_missing_tiles_c)
    results["Missing tiles.c"] = (code == 1 and "FileNotFoundError" in err)

    # 3. Corrupt base64 in strike.js
    code, out, err = run_test_case("Corrupt base64 in strike.js", setup_corrupt_base64)
    # Expected: binascii.Error or PIL.UnidentifiedImageError or similar, exit code 1
    results["Corrupt base64 in strike.js"] = (code == 1 and ("Error" in err or "UnidentifiedImageError" in err or "Exception" in err or "binascii" in err))

    # 4. Extra double quotes in strike.js
    code, out, err = run_test_case("Extra double quotes in strike.js", setup_extra_double_quotes)
    # Expected: should fail because base64 decoding or image opening fails
    results["Extra double quotes in strike.js"] = (code == 1)

    # 5. Comments containing hex in tiles.c
    code, out, err = run_test_case("Comments containing hex in tiles.c", setup_comments_in_tiles)
    # Expected: The script parses extra bytes, leading to a length mismatch (e.g. 514 bytes found instead of 512), causing it to fail.
    # Or if it doesn't fail, it silently shifts tile bytes, which is a silent failure (even worse!). Let's see.
    results["Comments containing hex in tiles.c"] = (code == 1 and "ValueError" in err)

    # 6. Syntax change in tiles.c
    code, out, err = run_test_case("Syntax change in tiles.c", setup_syntax_change_in_tiles)
    # Expected: ValueError due to array not found
    results["Syntax change in tiles.c"] = (code == 1 and "ValueError" in err)

    # 7. Incorrect tile count
    code, out, err = run_test_case("Incorrect tile count", setup_incorrect_tile_count)
    # Expected: ValueError: Expected 512 bytes, but found 16 bytes.
    results["Incorrect tile count"] = (code == 1 and "ValueError" in err and "Expected 512 bytes" in err)

    print("\n=== Robustness Test Summary ===")
    all_passed = True
    for name, passed in results.items():
        status = "PASSED (failed gracefully/correctly)" if passed else "FAILED (vulnerable or uncaught/silent failure)"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
            
    if all_passed:
        print("\nAll robustness tests passed!")
        sys.exit(0)
    else:
        print("\nSome robustness tests revealed vulnerabilities/flaws!")
        sys.exit(1)

if __name__ == "__main__":
    main()
