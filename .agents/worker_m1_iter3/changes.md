# Changes Summary — Milestone 1, Iteration 3

This document summarizes the changes made to the GameBoy graphics conversion and verification tools to resolve parser robustness issues and resource leaks, along with verification and build outputs.

---

## 1. Code Changes

### 1.1. C Parser Comment Stripping Swap
**File**: `dandy-gb/tools/verify_graphics.py`  
**Rationale**: Swapping the order of comment stripping ensures single-line comments (`//...`) are removed *before* multi-line comments (`/*...*/`). This prevents a single-line comment containing a block-comment start sequence (e.g., `// comment with /*`) from fooling the block comment stripper and swallowing active data.

```diff
@@ -61,10 +61,10 @@
     with open(tiles_c_path, "r") as f:
         content = f.read()
 
-    # Strip multi-line comments
-    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
     # Strip single-line comments
     content = re.sub(r'//.*?\n', '\n', content)
+    # Strip multi-line comments
+    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
 
     # Match the dandy_tiles array content (allowing optional size in brackets)
```

---

### 1.2. JS Parser Comment Stripping Robustness
**File**: `dandy-gb/tools/extract_sprites.py`  
**Rationale**: Stripping all comments (both single-line and block comments) from the JS file content *before* executing the regular expression to extract the base64 string. This prevents commented-out assignments (e.g., `// strike.src = ...`) preceding the active one from being matched by the regex.

```diff
@@ -4,6 +4,15 @@
 from PIL import Image
 
 def extract_base64_from_js(content):
+    # Strip all comments from the JS content before running the extractor
+    comment_pattern = re.compile(r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|/\*.*?\*/|//[^\n]*)', re.DOTALL)
+    def replacer(m):
+        s = m.group(0)
+        if s.startswith('/'):
+            return ''
+        return s
+    content = comment_pattern.sub(replacer, content)
+
     # Match the assignment to strike.src.
     # It must start with strike.src = followed by the data URL prefix and either:
```

---

### 1.3. PIL Image Resource Management
**File**: `dandy-gb/tools/verify_graphics.py`  
**Rationale**: Wrapping the original sheet load and the generated/saved audit sheet in context managers (`with` statements) to prevent open file descriptors from leaking.

```diff
@@ -199,10 +199,7 @@
 
     # 2. Load original spritesheet
     print(f"Loading original sprite sheet from {strike_png_path}...")
-    original_sheet = Image.open(strike_png_path)
-    if original_sheet.size != (256, 32):
-        raise ValueError(f"Expected original sprite sheet dimensions 256x32, but got {original_sheet.size}")
-
+    
     # 3. Create audit grid: 4 columns, 8 rows of comparison blocks.
     grid_cols = 4
     grid_rows = 8
@@ -209,73 +209,75 @@
     cell_h = 128
 
-    # Neutral dark-gray grid background to separate cells and provide professional contrast
-    audit_img = Image.new("RGBA", (grid_cols * cell_w, grid_rows * cell_h), (80, 80, 80, 255))
-
-    try:
-        nn_filter = Image.Resampling.NEAREST
-    except AttributeError:
-        nn_filter = Image.NEAREST
-
-    # Category sets
-    bg_indices = set(list(range(9)) + list(range(12, 16)) + list(range(20, 24)) + list(range(28, 32)))
-    sprite_indices = set(list(range(9, 12)) + list(range(16, 20)) + list(range(24, 28)))
-
-    # Pre-generate checkerboard pattern for sprites
-    checkerboard = create_checkerboard(128, 128, check_size=16, color1=200, color2=220)
-
-    print("Stitching side-by-side comparison sheet...")
-    for i in range(32):
-        col = i % grid_cols
-        row = i // grid_cols
-        cell_x = col * cell_w
-        cell_y = row * cell_h
-
-        # A. Crop original 16x16 sprite using the explicit layout mapping dictionary
-        js_index = GB_TO_JS_MAPPING.get(i, i)
-        orig_col = js_index % 16
-        orig_row = js_index // 16
-        orig_box = (orig_col * 16, orig_row * 16, (orig_col + 1) * 16, (orig_row + 1) * 16)
-        orig_tile = original_sheet.crop(orig_box)
-        orig_upscaled = orig_tile.resize((128, 128), nn_filter)
-        orig_rgba = orig_upscaled.convert("RGBA")
-
-        # B. Decode Game Boy 8x8 tile
-        tile_offset = i * 16
-        tile_data = tiles_bytes[tile_offset:tile_offset+16]
-        
-        is_sprite = i in sprite_indices
-        gb_tile = decode_gb_tile(tile_data, is_sprite=is_sprite, use_dark_floor=args.dark_floor)
-        gb_upscaled = gb_tile.resize((128, 128), nn_filter)
-
-        # C. Draw onto audit sheet
-        if is_sprite:
-            # Sprite transparency audit: use checkerboard backgrounds
-            audit_img.paste(checkerboard, (cell_x, cell_y))
-            audit_img.paste(checkerboard, (cell_x + 128, cell_y))
-            
-            # Alpha paste original sprite and GB tile over checkerboard
-            audit_img.paste(orig_rgba, (cell_x, cell_y), orig_rgba)
-            audit_img.paste(gb_upscaled, (cell_x + 128, cell_y), gb_upscaled)
-        else:
-            # Background tile audit: use the active mode's floor color (Color 0) as solid background
-            bg_color = (0, 0, 0, 255) if args.dark_floor else (255, 255, 255, 255)
-            solid_bg = Image.new("RGBA", (128, 128), bg_color)
-            
-            audit_img.paste(solid_bg, (cell_x, cell_y))
-            audit_img.paste(solid_bg, (cell_x + 128, cell_y))
-            
-            # Paste original sprite and GB tile
-            audit_img.paste(orig_rgba, (cell_x, cell_y), orig_rgba)
-            audit_img.paste(gb_upscaled, (cell_x + 128, cell_y))
-
-    # Convert to RGB before saving (audit image is fully opaque RGB)
-    final_rgb_img = audit_img.convert("RGB")
-    
-    # Ensure target directory exists
-    os.makedirs(os.path.dirname(output_path), exist_ok=True)
-    print(f"Saving audit sheet to {output_path}...")
-    final_rgb_img.save(output_path)
-    print("Verification and audit sheet generation complete!")
+
+    with Image.open(strike_png_path) as original_sheet, \
+         Image.new("RGBA", (grid_cols * cell_w, grid_rows * cell_h), (80, 80, 80, 255)) as audit_img:
+         
+        if original_sheet.size != (256, 32):
+            raise ValueError(f"Expected original sprite sheet dimensions 256x32, but got {original_sheet.size}")
+
+        try:
+            nn_filter = Image.Resampling.NEAREST
+        except AttributeError:
+            nn_filter = Image.NEAREST
+
+        # Category sets
+        bg_indices = set(list(range(9)) + list(range(12, 16)) + list(range(20, 24)) + list(range(28, 32)))
+        sprite_indices = set(list(range(9, 12)) + list(range(16, 20)) + list(range(24, 28)))
+
+        # Pre-generate checkerboard pattern for sprites
+        checkerboard = create_checkerboard(128, 128, check_size=16, color1=200, color2=220)
+
+        print("Stitching side-by-side comparison sheet...")
+        for i in range(32):
+            col = i % grid_cols
+            row = i // grid_cols
+            cell_x = col * cell_w
+            cell_y = row * cell_h
+
+            # A. Crop original 16x16 sprite using the explicit layout mapping dictionary
+            js_index = GB_TO_JS_MAPPING.get(i, i)
+            orig_col = js_index % 16
+            orig_row = js_index // 16
+            orig_box = (orig_col * 16, orig_row * 16, (orig_col + 1) * 16, (orig_row + 1) * 16)
+            orig_tile = original_sheet.crop(orig_box)
+            orig_upscaled = orig_tile.resize((128, 128), nn_filter)
+            orig_rgba = orig_upscaled.convert("RGBA")
+
+            # B. Decode Game Boy 8x8 tile
+            tile_offset = i * 16
+            tile_data = tiles_bytes[tile_offset:tile_offset+16]
+            
+            is_sprite = i in sprite_indices
+            gb_tile = decode_gb_tile(tile_data, is_sprite=is_sprite, use_dark_floor=args.dark_floor)
+            gb_upscaled = gb_tile.resize((128, 128), nn_filter)
+
+            # C. Draw onto audit sheet
+            if is_sprite:
+                # Sprite transparency audit: use checkerboard backgrounds
+                audit_img.paste(checkerboard, (cell_x, cell_y))
+                audit_img.paste(checkerboard, (cell_x + 128, cell_y))
+                
+                # Alpha paste original sprite and GB tile over checkerboard
+                audit_img.paste(orig_rgba, (cell_x, cell_y), orig_rgba)
+                audit_img.paste(gb_upscaled, (cell_x + 128, cell_y), gb_upscaled)
+            else:
+                # Background tile audit: use the active mode's floor color (Color 0) as solid background
+                bg_color = (0, 0, 0, 255) if args.dark_floor else (255, 255, 255, 255)
+                solid_bg = Image.new("RGBA", (128, 128), bg_color)
+                
+                audit_img.paste(solid_bg, (cell_x, cell_y))
+                audit_img.paste(solid_bg, (cell_x + 128, cell_y))
+                
+                # Paste original sprite and GB tile
+                audit_img.paste(orig_rgba, (cell_x, cell_y), orig_rgba)
+                audit_img.paste(gb_upscaled, (cell_x + 128, cell_y))
+
+        # Convert to RGB before saving (audit image is fully opaque RGB)
+        with audit_img.convert("RGB") as final_rgb_img:
+            # Ensure target directory exists
+            os.makedirs(os.path.dirname(output_path), exist_ok=True)
+            print(f"Saving audit sheet to {output_path}...")
+            final_rgb_img.save(output_path)
+            print("Verification and audit sheet generation complete!")
```

---

## 2. Verification Outputs

### 2.1. Sprite Extraction Execution Output
Executing `extract_sprites.py` successfully parses the JS file and outputs:
```
Reading sprite sheet from /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-js/strike.js...
Decoding base64 string of length 2736...
Saving to /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/strike_original.png...
Verified image size: 256x32
Extraction and verification successful!
```

### 2.2. Graphics Audit Sheet Generation Output
Executing `verify_graphics.py` successfully parses the C tiles definitions and outputs:
```
Reading tiles definition from /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/tiles.c...
Loading original sprite sheet from /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/strike_original.png...
Stitching side-by-side comparison sheet...
Saving audit sheet to /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/graphics_audit.png...
Verification and audit sheet generation complete!
```

### 2.3. Robustness Unit Tests Output
Executing the newly written robustness test suite `test_robustness.py` proves both parser robustness fixes pass cleanly:
```
Reading tiles definition from /tmp/tmpdx8awv3u.c...
..
----------------------------------------------------------------------
Ran 2 tests in 0.004s

OK
```

---

## 3. GBDK Build Compilation Output

Executing `make clean && make` in `dandy-gb/` results in a fully clean, successful compilation:
```
rm -rf obj bin
rm -f web/*.js web/*.wasm
rm -f *.lst *.map *.sym
rm -rf tests/mock_gb tests/.temp_envs
rm -f libdandy_test.so
Clean complete.
Converting levels from JS to C header...
python3 tools/convert_levels.py
Reading levels from /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-js/levels.js...
Found 26 levels.
Writing C header to /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/levels.h...
Level  0: Raw=1800B -> B2= 357B (Saved 80.2%)
Level  1: Raw=1800B -> B2= 323B (Saved 82.1%)
Level  2: Raw=1800B -> B2= 391B (Saved 78.3%)
Level  3: Raw=1800B -> B2= 383B (Saved 78.7%)
Level  4: Raw=1800B -> B2= 656B (Saved 63.6%)
Level  5: Raw=1800B -> B2= 610B (Saved 66.1%)
Level  6: Raw=1800B -> B2= 409B (Saved 77.3%)
Level  7: Raw=1800B -> B2= 390B (Saved 78.3%)
Level  8: Raw=1800B -> B2= 492B (Saved 72.7%)
Level  9: Raw=1800B -> B2= 358B (Saved 80.1%)
Level 10: Raw=1800B -> B2= 292B (Saved 83.8%)
Level 11: Raw=1800B -> B2= 354B (Saved 80.3%)
Level 12: Raw=1800B -> B2= 383B (Saved 78.7%)
Level 13: Raw=1800B -> B2= 449B (Saved 75.1%)
Level 14: Raw=1800B -> B2= 389B (Saved 78.4%)
Level 15: Raw=1800B -> B2= 370B (Saved 79.4%)
Level 16: Raw=1800B -> B2= 304B (Saved 83.1%)
Level 17: Raw=1800B -> B2= 452B (Saved 74.9%)
Level 18: Raw=1800B -> B2= 288B (Saved 84.0%)
Level 19: Raw=1800B -> B2= 304B (Saved 83.1%)
Level 20: Raw=1800B -> B2= 425B (Saved 76.4%)
Level 21: Raw=1800B -> B2= 398B (Saved 77.9%)
Level 22: Raw=1800B -> B2= 338B (Saved 81.2%)
Level 23: Raw=1800B -> B2= 316B (Saved 82.4%)
Level 24: Raw=1800B -> B2= 403B (Saved 77.6%)
Level 25: Raw=1800B -> B2=1216B (Saved 32.4%)
--------------------------------------------------
TOTAL MAP BUDGET Footprint in ROM:
Raw uncompressed:  46800 Bytes (45.7 KB)
B2 compressed:     11050 Bytes (10.8 KB)
Overall savings:   76.4%
--------------------------------------------------
Writing C source to /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/levels.c...
Conversion complete!
Compiling pristine BMP sprite assets...
python3 tools/compile_bmp_sprites.py
Compiling 32 native 8x8 pixel-art glyphs into GBDK 2bpp format...
Writing C header to /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/tiles.h...
Writing C source to /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/tiles.c...
Sprite compilation complete! Output: 512 bytes of perfectly designed, un-aliased native 8x8 GameBoy assets.
/usr/local/google/home/jackpal/Developer/gbdk/bin/lcc -Wf--opt-code-size -c -o obj/main.o src/main.c
/usr/local/google/home/jackpal/Developer/gbdk/bin/lcc -Wf--opt-code-size -c -o obj/dandy_core.o src/dandy_core.c
/usr/local/google/home/jackpal/Developer/gbdk/bin/lcc -Wf--opt-code-size -c -o obj/gameboy_hal.o src/gameboy_hal.c
/usr/local/google/home/jackpal/Developer/gbdk/bin/lcc -Wf-bo1 -c -o obj/levels.o src/levels.c
/usr/local/google/home/jackpal/Developer/gbdk/bin/lcc -Wf--opt-code-size -c -o obj/tiles.o src/tiles.c
/usr/local/google/home/jackpal/Developer/gbdk/bin/lcc -Wa-l -Wl-m -Wl-yo2 -o bin/dandy.gb obj/main.o obj/dandy_core.o obj/gameboy_hal.o obj/levels.o obj/tiles.o
----------------------------------------
Build successful: bin/dandy.gb
----------------------------------------
```

---

## 4. Paths to Regenerated Images

1. **Original Sprite Sheet**:  
   `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/strike_original.png`
2. **Graphics Audit Sheet (DMG Palette)**:  
   `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/graphics_audit.png`
