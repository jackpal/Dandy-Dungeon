#!/usr/bin/env python3
import sys
import os
import shutil
import tempfile
import traceback

# Add the tools directory to the path so we can import verify_graphics
sys.path.append("/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools")
import verify_graphics

# Helper to create a temp directory
TEMP_DIR = tempfile.mkdtemp(prefix="graphics_challenger_")

# Save original paths for reference or cleanup
ORIG_JS_PATH = verify_graphics.JS_STRIKE_PATH
ORIG_C_PATH = verify_graphics.C_TILES_PATH
ORIG_OUT_DIR = verify_graphics.OUTPUT_DIR
ORIG_REF_PATH = verify_graphics.REFERENCE_PNG_PATH
ORIG_AUDIT_PATH = verify_graphics.AUDIT_PNG_PATH

# Redirect output paths to our temp directory to avoid touching the actual repo files
verify_graphics.OUTPUT_DIR = TEMP_DIR
verify_graphics.REFERENCE_PNG_PATH = os.path.join(TEMP_DIR, "strike_original.png")
verify_graphics.AUDIT_PNG_PATH = os.path.join(TEMP_DIR, "graphics_audit.png")

# Valid base64 string representing a tiny 1x1 PNG (or we can use a small valid PNG)
# Let's use a real 256x32 png base64 from the actual strike.js to test valid cases.
# We can extract the real base64 first.
with open(ORIG_JS_PATH, 'r') as f:
    real_js_content = f.read()

def reset_paths():
    verify_graphics.JS_STRIKE_PATH = os.path.join(TEMP_DIR, "strike.js")
    verify_graphics.C_TILES_PATH = os.path.join(TEMP_DIR, "tiles.c")

reset_paths()

def test_missing_js_file():
    print("\n--- Test 1: Missing strike.js ---")
    reset_paths()
    if os.path.exists(verify_graphics.JS_STRIKE_PATH):
        os.remove(verify_graphics.JS_STRIKE_PATH)
    
    try:
        verify_graphics.extract_reference_png()
        print("FAIL: Expected FileNotFoundError or similar, but script succeeded (or didn't raise).")
        return False
    except FileNotFoundError as e:
        print(f"PASS: Correctly raised FileNotFoundError: {e}")
        return True
    except Exception as e:
        print(f"FAIL: Raised unexpected exception: {type(e).__name__}: {e}")
        return False

def test_missing_c_file():
    print("\n--- Test 2: Missing tiles.c ---")
    reset_paths()
    if os.path.exists(verify_graphics.C_TILES_PATH):
        os.remove(verify_graphics.C_TILES_PATH)
        
    try:
        verify_graphics.parse_tiles_c()
        print("FAIL: Expected FileNotFoundError or similar, but script succeeded.")
        return False
    except FileNotFoundError as e:
        print(f"PASS: Correctly raised FileNotFoundError: {e}")
        return True
    except Exception as e:
        print(f"FAIL: Raised unexpected exception: {type(e).__name__}: {e}")
        return False

def test_corrupt_base64():
    print("\n--- Test 3: Corrupt/invalid base64 in strike.js ---")
    reset_paths()
    # Write a strike.js with invalid base64 characters
    with open(verify_graphics.JS_STRIKE_PATH, 'w') as f:
        f.write('const strike = new Image();\n')
        f.write('strike.src = "data:image/png;base64,!!!INVALID_BASE64!!!";\n')
        
    try:
        verify_graphics.extract_reference_png()
        print("FAIL: Script did not raise error for corrupt base64.")
        return False
    except Exception as e:
        # base64.b64decode or PIL might fail. Let's see what it raises.
        print(f"PASS: Raised exception as expected: {type(e).__name__}: {e}")
        return True

def test_extra_double_quoted_strings():
    print("\n--- Test 4: Extra double-quoted strings in strike.js (Parser Fragility) ---")
    reset_paths()
    # Write a strike.js that has another double-quoted string before/after the image
    with open(verify_graphics.JS_STRIKE_PATH, 'w') as f:
        f.write('const name = "strike_sprite_sheet";\n')
        f.write('const strike = new Image();\n')
        f.write('strike.src = "data:image/png;base64," +\n')
        # write a valid base64 part representing the actual PNG or a small PNG
        f.write('"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=";\n')
        
    try:
        # The parser will extract "strike_sprite_sheet" and the base64 string,
        # join them together, and try to decode.
        ref_path = verify_graphics.extract_reference_png()
        
        # Now try to load the image with PIL. If the image is corrupt (due to prepended garbage),
        # PIL will raise an UnidentifiedImageError or OSError.
        from PIL import Image
        img = Image.open(ref_path)
        img.verify() # Verify image integrity
        print("FAIL: Image was successfully opened and verified by PIL despite corruption!")
        return False
    except Exception as e:
        print(f"PASS: Correctly failed (either base64 decode failed or PIL could not open/verify the corrupt image): {type(e).__name__}: {e}")
        return True

def test_decimal_values_in_c():
    print("\n--- Test 5a: Decimal values in tiles.c ---")
    reset_paths()
    # Write a valid tiles.c but using decimal values instead of hex
    # e.g., 0, 0, 119, 0 instead of 0x00, 0x00, 0x77, 0x00
    with open(verify_graphics.C_TILES_PATH, 'w') as f:
        f.write('const unsigned char dandy_tiles[] = {\n')
        # 512 decimal zeros
        f.write(', '.join(['0'] * 512))
        f.write('\n};\n')
        
    try:
        verify_graphics.parse_tiles_c()
        print("FAIL: Parser succeeded or did not raise error, but did it find 512 bytes? (Should fail because it only matches 0x[0-9a-fA-F]{2})")
        return False
    except ValueError as e:
        print(f"PASS: Correctly raised ValueError (parser failed to extract decimal values as expected): {e}")
        return True
    except Exception as e:
        print(f"FAIL: Raised unexpected exception type: {type(e).__name__}: {e}")
        return False

def test_sized_array_declaration():
    print("\n--- Test 5b: Sized array declaration (const unsigned char dandy_tiles[512]) ---")
    reset_paths()
    with open(verify_graphics.C_TILES_PATH, 'w') as f:
        f.write('const unsigned char dandy_tiles[512] = {\n')
        f.write(', '.join(['0x00'] * 512))
        f.write('\n};\n')
        
    try:
        verify_graphics.parse_tiles_c()
        print("FAIL: Sized array declaration was parsed successfully? Wait, the regex uses `dandy_tiles\\[\\]`, so this should fail!")
        return False
    except ValueError as e:
        print(f"PASS: Correctly raised ValueError (parser failed on sized array declaration as expected): {e}")
        return True
    except Exception as e:
        print(f"FAIL: Raised unexpected exception: {type(e).__name__}: {e}")
        return False

def test_missing_unsigned_qualifier():
    print("\n--- Test 5c: Omission of 'unsigned' keyword (const char dandy_tiles[]) ---")
    reset_paths()
    with open(verify_graphics.C_TILES_PATH, 'w') as f:
        f.write('const char dandy_tiles[] = {\n')
        f.write(', '.join(['0x00'] * 512))
        f.write('\n};\n')
        
    try:
        verify_graphics.parse_tiles_c()
        print("FAIL: Array without 'unsigned' was parsed? Regex has `const\\s+unsigned\\s+char`, so this should fail.")
        return False
    except ValueError as e:
        print(f"PASS: Correctly raised ValueError (parser failed on missing 'unsigned' as expected): {e}")
        return True
    except Exception as e:
        print(f"FAIL: Raised unexpected exception: {type(e).__name__}: {e}")
        return False

def test_formatting_variations():
    print("\n--- Test 5d: Formatting variations (multiple spaces, comments, newlines) ---")
    reset_paths()
    with open(verify_graphics.C_TILES_PATH, 'w') as f:
        f.write('const   unsigned   char   dandy_tiles[]   =   {\n')
        # write 512 hex values with comments and weird spacing
        vals = []
        for i in range(32):
            vals.append(f'/* Tile {i} */')
            for _ in range(16):
                vals.append('0x00')
        f.write(',\n'.join(vals))
        f.write('\n};\n')
        
    try:
        tiles = verify_graphics.parse_tiles_c()
        if len(tiles) == 32 and all(len(t) == 16 for t in tiles):
            print("PASS: Parser is robust to spacing, comments, and newlines inside the array.")
            return True
        else:
            print(f"FAIL: Parser returned unexpected tiles: {len(tiles)} tiles.")
            return False
    except Exception as e:
        print(f"FAIL: Parser failed to handle comments/spacing: {type(e).__name__}: {e}")
        return False

def test_clean_run_with_valid_mock_files():
    print("\n--- Test 6: Clean run with valid mock files (End-to-End) ---")
    reset_paths()
    
    # Write valid strike.js using real base64
    with open(verify_graphics.JS_STRIKE_PATH, 'w') as f:
        f.write(real_js_content)
        
    # Write valid tiles.c using actual tiles.c content
    with open(ORIG_C_PATH, 'r') as f:
        real_c_content = f.read()
    with open(verify_graphics.C_TILES_PATH, 'w') as f:
        f.write(real_c_content)
        
    try:
        verify_graphics.main()
        # Verify that output files were created in the temp directory
        ref_exists = os.path.exists(verify_graphics.REFERENCE_PNG_PATH)
        audit_exists = os.path.exists(verify_graphics.AUDIT_PNG_PATH)
        if ref_exists and audit_exists:
            print("PASS: End-to-End run succeeded and generated correct outputs.")
            return True
        else:
            print(f"FAIL: Outputs missing. strike_original: {ref_exists}, graphics_audit: {audit_exists}")
            return False
    except Exception as e:
        print(f"FAIL: End-to-End run failed: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False

def main():
    results = {}
    results['missing_js'] = test_missing_js_file()
    results['missing_c'] = test_missing_c_file()
    results['corrupt_base64'] = test_corrupt_base64()
    results['extra_quotes'] = test_extra_double_quoted_strings()
    results['decimal_values'] = test_decimal_values_in_c()
    results['sized_array'] = test_sized_array_declaration()
    results['missing_unsigned'] = test_missing_unsigned_qualifier()
    results['formatting_variations'] = test_formatting_variations()
    results['clean_run'] = test_clean_run_with_valid_mock_files()
    
    print("\n==========================================")
    print("Stress Test Summary:")
    all_ok = True
    for test, passed in results.items():
        status = "PASSED (Robust/Expected failure)" if passed else "FAILED"
        if not passed:
            all_ok = False
        print(f" - {test}: {status}")
    print("==========================================")
    
    # Cleanup temp dir
    shutil.rmtree(TEMP_DIR)
    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()
