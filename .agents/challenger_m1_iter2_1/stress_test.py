import os
import sys
import re
import base64
import shutil
from PIL import Image

# Add tools directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
dandy_gb_dir = os.path.normpath(os.path.join(current_dir, "../../dandy-gb"))
tools_dir = os.path.join(dandy_gb_dir, "tools")
sys.path.append(tools_dir)

import verify_graphics
import extract_sprites

def test_gb_tile_decoding_math():
    print("Running Test: GB 2bpp decoding math correctness...")
    tile_bytes = bytes([
        0x55, 0x33, # Row 0
        0xAA, 0xCC, # Row 1
        0x00, 0x00, # Row 2
        0x00, 0x00, # Row 3
        0x00, 0x00, # Row 4
        0x00, 0x00, # Row 5
        0x00, 0x00, # Row 6
        0x00, 0x00  # Row 7
    ])

    # 1. Background palette decoding (Classic DMG, default)
    bg_palette_dmg = [
        (255, 255, 255, 255),
        (170, 170, 170, 255),
        (85, 85, 85, 255),
        (0, 0, 0, 255)
    ]
    bg_img_dmg = verify_graphics.decode_gb_tile(tile_bytes, is_sprite=False, use_dark_floor=False)
    bg_pixels_dmg = bg_img_dmg.load()

    expected_bg_dmg_row0 = [bg_palette_dmg[c] for c in [0, 1, 2, 3, 0, 1, 2, 3]]
    expected_bg_dmg_row1 = [bg_palette_dmg[c] for c in [3, 2, 1, 0, 3, 2, 1, 0]]

    for x in range(8):
        assert bg_pixels_dmg[x, 0] == expected_bg_dmg_row0[x], f"BG DMG Row 0 Col {x} mismatch: got {bg_pixels_dmg[x, 0]}, expected {expected_bg_dmg_row0[x]}"
        assert bg_pixels_dmg[x, 1] == expected_bg_dmg_row1[x], f"BG DMG Row 1 Col {x} mismatch: got {bg_pixels_dmg[x, 1]}, expected {expected_bg_dmg_row1[x]}"

    # 2. Background palette decoding (Atmospheric, dark floor)
    bg_palette_dark = [
        (0, 0, 0, 255),
        (85, 85, 85, 255),
        (170, 170, 170, 255),
        (255, 255, 255, 255)
    ]
    bg_img_dark = verify_graphics.decode_gb_tile(tile_bytes, is_sprite=False, use_dark_floor=True)
    bg_pixels_dark = bg_img_dark.load()

    expected_bg_dark_row0 = [bg_palette_dark[c] for c in [0, 1, 2, 3, 0, 1, 2, 3]]
    expected_bg_dark_row1 = [bg_palette_dark[c] for c in [3, 2, 1, 0, 3, 2, 1, 0]]

    for x in range(8):
        assert bg_pixels_dark[x, 0] == expected_bg_dark_row0[x], f"BG Dark Row 0 Col {x} mismatch: got {bg_pixels_dark[x, 0]}, expected {expected_bg_dark_row0[x]}"
        assert bg_pixels_dark[x, 1] == expected_bg_dark_row1[x], f"BG Dark Row 1 Col {x} mismatch: got {bg_pixels_dark[x, 1]}, expected {expected_bg_dark_row1[x]}"

    # 3. Sprite palette decoding
    sprite_palette = [
        (0, 0, 0, 0),
        (255, 255, 255, 255),
        (85, 85, 85, 255),
        (0, 0, 0, 255)
    ]
    sprite_img = verify_graphics.decode_gb_tile(tile_bytes, is_sprite=True)
    sprite_pixels = sprite_img.load()

    expected_sprite_row0 = [sprite_palette[c] for c in [0, 1, 2, 3, 0, 1, 2, 3]]
    expected_sprite_row1 = [sprite_palette[c] for c in [3, 2, 1, 0, 3, 2, 1, 0]]

    for x in range(8):
        assert sprite_pixels[x, 0] == expected_sprite_row0[x], f"Sprite Row 0 Col {x} mismatch: got {sprite_pixels[x, 0]}, expected {expected_sprite_row0[x]}"
        assert sprite_pixels[x, 1] == expected_sprite_row1[x], f"Sprite Row 1 Col {x} mismatch: got {sprite_pixels[x, 1]}, expected {expected_sprite_row1[x]}"

    print("→ PASS: GB 2bpp decoding math is 100% correct.")


def test_tiles_c_comment_stripping_robustness():
    print("\nRunning Test: tiles.c comment stripping robustness...")
    original_tiles_c = os.path.join(dandy_gb_dir, "src/tiles.c")
    
    with open(original_tiles_c, "r") as f:
        orig_content = f.read()

    orig_bytes = verify_graphics.parse_tiles_c(original_tiles_c)

    def run_parser_on_modified(modified_content, test_desc):
        temp_file = os.path.join(current_dir, "temp_tiles.c")
        with open(temp_file, "w") as f:
            f.write(modified_content)
        try:
            parsed_bytes = verify_graphics.parse_tiles_c(temp_file)
            assert parsed_bytes == orig_bytes, f"{test_desc} failed: parsed bytes do not match original bytes"
            print(f"  → PASS: {test_desc}")
            return True
        except Exception as e:
            print(f"  → FAIL: {test_desc} - Raised: {e}")
            return False
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    # Scenario 1: Standard comments with hex values inside the array
    modified_1 = orig_content.replace(
        "0x00, 0x00, 0x00, 0x00,",
        "0x00, 0x00, // 0x55, 0x66, 0x77 commented hex\n0x00, 0x00, /* 0xAA, 0xBB */"
    )
    run_parser_on_modified(modified_1, "Standard single/multi-line comments with hex values")

    # Scenario 2: Comments containing quotes and weird symbols
    modified_2 = orig_content.replace(
        "0x00, 0x00, 0x00, 0x00,",
        "0x00, 0x00, // comment with 'single quotes' and \"double quotes\"\n0x00, 0x00, /* comment with * and / and + */"
    )
    run_parser_on_modified(modified_2, "Comments with quotes and symbols")

    # Scenario 3: Single-line comment containing /* (nested comment bug)
    modified_3 = orig_content.replace(
        "0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,",
        "0x00, 0x00, // comment with /*\n0x00, 0x00, /* another comment */ 0x00, 0x00, 0x00, 0x00,"
    )
    run_parser_on_modified(modified_3, "Single-line comment containing /* (nested comment bug)")

    # Scenario 4: A comment containing '}' inside the array
    modified_4 = orig_content.replace(
        "0x00, 0x00, 0x00, 0x00,",
        "0x00, 0x00, // comment with } closing brace\n0x00, 0x00,"
    )
    run_parser_on_modified(modified_4, "Comment containing '}' inside the array")


def test_js_extraction_robustness():
    print("\nRunning Test: strike.js base64 extraction robustness...")
    original_strike_js = os.path.normpath(os.path.join(dandy_gb_dir, "../dandy-js/strike.js"))

    with open(original_strike_js, "r") as f:
        orig_content = f.read()

    orig_base64 = extract_sprites.extract_base64_from_js(orig_content)

    def run_extractor_on_modified(modified_content, test_desc):
        try:
            parsed_base64 = extract_sprites.extract_base64_from_js(modified_content)
            assert parsed_base64 == orig_base64, f"{test_desc} failed: extracted base64 does not match original"
            print(f"  → PASS: {test_desc}")
            return True
        except Exception as e:
            print(f"  → FAIL: {test_desc} - Raised: {e}")
            return False

    # Scenario 1: Unrelated double-quoted strings and comments before/after strike.src
    modified_1 = f"""
    // This is a header comment with "quotes" and strike.src reference
    const config = {{
        name: "strike",
        type: "image/png",
        dummy_src: "data:image/png;base64,unrelatedbase64data=="
    }};
    
    {orig_content}
    
    console.log("Finished loading strike.src!");
    """
    run_extractor_on_modified(modified_1, "Unrelated strings and comments in the file")

    # Scenario 2: Comments inside the strike.src assignment block containing quotes and pluses
    modified_2 = orig_content.replace(
        'strike.src = "data:image/png;base64," +',
        'strike.src = "data:image/png;base64," + // comment with "quotes" and + \n'
    )
    run_extractor_on_modified(modified_2, "Comments inside assignment block containing quotes/pluses")

    # Scenario 3: Commented-out strike.src assignment BEFORE the active one
    modified_3 = f"""
    // strike.src = "data:image/png;base64,INVALID_COMMENTED_OUT_BASE64_DATA==";
    {orig_content}
    """
    run_extractor_on_modified(modified_3, "Commented-out strike.src assignment before active one")

    # Scenario 4: Commented-out strike.src block comment BEFORE the active one
    modified_4 = f"""
    /*
    strike.src = "data:image/png;base64,INVALID_BLOCK_COMMENTED_DATA==";
    */
    {orig_content}
    """
    run_extractor_on_modified(modified_4, "Block commented-out strike.src assignment before active one")

    # Scenario 5: strike.src inside an unescaped string before the active assignment
    modified_5 = f"""
    console.log('Debugging strike.src = "data:image/png;base64,INVALID_STRING_DATA=="');
    {orig_content}
    """
    run_extractor_on_modified(modified_5, "strike.src inside a string before active assignment")


def check_for_resource_leaks():
    print("\nRunning Test: Resource leaks check...")
    import builtins
    original_open = builtins.open
    open_files = {}

    def tracked_open(file, mode='r', *args, **kwargs):
        f = original_open(file, mode, *args, **kwargs)
        open_files[f] = (file, mode)
        orig_close = f.close
        def tracked_close():
            if f in open_files:
                del open_files[f]
            orig_close()
        f.close = tracked_close
        return f

    builtins.open = tracked_open
    
    try:
        extract_sprites.extract()
        verify_graphics.main([])
    except Exception as e:
        print(f"Error running pipeline: {e}")
    finally:
        builtins.open = original_open

    if open_files:
        print("  → WARNING: The following files were opened but not closed during execution:")
        for f, (name, mode) in open_files.items():
            print(f"    - File: {name} (Mode: {mode})")
    else:
        print("  → PASS: No files were left open (all opened files were closed).")


if __name__ == "__main__":
    print("=================== STRESS TESTING GRAPHICS TOOLS ===================")
    test_gb_tile_decoding_math()
    test_tiles_c_comment_stripping_robustness()
    test_js_extraction_robustness()
    check_for_resource_leaks()
    print("=====================================================================")
