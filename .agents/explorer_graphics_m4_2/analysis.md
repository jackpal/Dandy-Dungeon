# Technical Exploration: Graphics Compiler & Overrides (Milestone 4)

## Executive Summary
This analysis presents a robust, elegant solution for integrating the Classic DMG and Atmospheric Dark floor tile layouts into the GameBoy graphics compiler pipeline. 

By utilizing a standard C preprocessor directive (`#ifdef USE_BLACK_FLOOR`) inside the compiled `src/tiles.c` array initializer, we can support conditional compilation of the empty floor tile (Tile 0) at C compile-time. This approach prevents duplication of the other 31 tiles, keeping the output clean and highly optimized.

To support this design, we will:
1. Define the Classic DMG textured floor (with subtle dots) as a manual override in `overrides.py` and activate it in `selector.py`.
2. Modify `compiler.py` to generate the conditional C preprocessor block inside `src/tiles.c` for Tile 0.
3. Update `verify_graphics.py` and `test_graphics_pipeline.py` to be preprocessor-aware so that they do not break when parsing `src/tiles.c`.

---

## Technical Design & Architecture

### 1. The Role of Palettes vs. Tile Layouts
In Dandy Dungeon's GameBoy port, the graphics pipeline compiles 16x16 pixel-art sprites into 8x8 2bpp tiles. The engine supports two modes:
*   **Classic DMG Mode (Default)**: Background Palette (BGP) is `0xE4` (Color 0 -> White, Color 1 -> Light Gray, Color 2 -> Dark Gray, Color 3 -> Black).
*   **Atmospheric Dark Mode (Compile-Time Toggle)**: BGP is `0x1B` (Color 0 -> Black, Color 1 -> Dark Gray, Color 2 -> Light Gray, Color 3 -> White).

For almost all tiles (walls, doors, keys, etc.) and sprites, the 2bpp pixel index values (0..3) remain identical between both modes. Swapping the hardware palette registers (BGP, OBP0/1) in `src/main.c` is sufficient to achieve the desired visual inversion.

However, **Tile 0 (Empty Floor)** is a special exception:
*   **Classic DMG Mode**: The floor must be White (Color 0) with subtle Light Gray (Color 1) texture dots at specific coordinates like (2,2) and (6,5).
*   **Atmospheric Dark Mode**: The floor must be solid Black (Color 0 in Atmospheric Mode), with **no** texture dots.

Thus, Tile 0 requires different 2bpp pixel data in each mode:
*   **Classic DMG Tile 0**: Value `1` at (2,2) and (6,5), and `0` elsewhere.
*   **Atmospheric Dark Tile 0**: Value `0` everywhere.

---

### 2. Proposing the Conditional C Array
Instead of duplicating the entire `dandy_tiles` array, we propose inserting preprocessor directives directly inside the array initializer in `src/tiles.c`. 

During GBDK compilation, if `-DUSE_BLACK_FLOOR` is passed via `LCCFLAGS`, the preprocessor compiles the solid black Tile 0. Otherwise, it compiles the textured Classic DMG Tile 0.

#### Target Output in `src/tiles.c`:
```c
const unsigned char dandy_tiles[] = {
    /* Tile 0 */
#ifdef USE_BLACK_FLOOR
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
#else
    0x00, 0x00, 0x00, 0x00, 0x20, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00,
#endif
    /* Tile 1 */
    0x42, 0xFF, 0x7E, ...
```

This ensures `dandy_tiles` remains a single contiguous array in VRAM, satisfying the interface contract in `src/tiles.h` and matching the signature:
```c
extern const unsigned char dandy_tiles[32 * 16];
```

---

### 3. Preprocessor-Aware Python Tools and Tests
Python verification tools (such as `tools/verify_graphics.py`) and integration tests (such as `tests/test_graphics_pipeline.py`) naively parse `src/tiles.c` by looking for all hex values inside the `dandy_tiles` array.

If we add the `#ifdef` block, a naive regex parser will find **528 hex values** instead of 512, causing assertion failures.

To resolve this, we will make the Python parser preprocessor-aware using a simple regular expression to strip the inactive branch before parsing. The active branch will be selected based on the `--dark-floor` command-line flag or the test parameter:

```python
# Simple Python preprocessor emulation
if use_dark_floor:
    content = re.sub(r'#ifdef\s+USE_BLACK_FLOOR\s+(.*?)\s+#else\s+(.*?)\s+#endif', r'\1', content, flags=re.DOTALL)
else:
    content = re.sub(r'#ifdef\s+USE_BLACK_FLOOR\s+(.*?)\s+#else\s+(.*?)\s+#endif', r'\2', content, flags=re.DOTALL)
```

---

## Detailed Code Modifications

### 1. `dandy-gb/downscale/overrides.py`
Redefine the override for Tile 0 (`HAND_DRAWN_GLYPHS[0]`) to represent the Classic DMG floor tile with texture dots at (2,2) and (6,5) (using 0-based indexing).

```python
<<<<
    # 0: TILE_SPACE (Empty corridor floor -> Solid Black)
    0: [
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000"
    ],
====
    # 0: TILE_SPACE (Empty corridor floor -> Classic DMG: subtle Light Gray dots, Atmospheric Dark: solid Black)
    0: [
        "00000000",
        "00000000",
        "00100000",  # Light Gray dot at (2,2)
        "00000000",
        "00000000",
        "00000010",  # Light Gray dot at (6,5)
        "00000000",
        "00000000"
    ],
>>>>
```

### 2. `dandy-gb/downscale/selector.py`
Route Tile 0 to use the manual override (which defines the Classic DMG floor layout) rather than the mathematical downscaling from the source sheet.

```python
<<<<
    # Background / Structure Tiles
    0: "mathematical",  # Space (floor)
====
    # Background / Structure Tiles
    0: "manual",        # Space (floor)
>>>>
```

### 3. `dandy-gb/downscale/compiler.py`
Modify `GameBoyCompiler.compile` to generate the conditional preprocessor block in `src/tiles.c` for Tile 0.

```python
<<<<
        for t_idx, tile_bytes in enumerate(compiled_tiles):
            c_content.append(f"    /* Tile {t_idx} */")
            hex_rows = []
            for row_idx in range(0, len(tile_bytes), 8):
                chunk = tile_bytes[row_idx:row_idx+8]
                hex_str = ", ".join([f"0x{val:02X}" for val in chunk])
                hex_rows.append(f"    {hex_str}")
            c_content.append(",\n".join(hex_rows) + ("," if t_idx < 31 else ""))
====
        for t_idx, tile_bytes in enumerate(compiled_tiles):
            if t_idx == 0:
                # Compile solid black tile for Atmospheric Dark mode
                black_tile = np.zeros((8, 8), dtype=np.uint8)
                black_tile_bytes = cls.pack_tile(black_tile)
                
                # Generate hex strings for black tile (Atmospheric Dark)
                black_hex_rows = []
                for row_idx in range(0, len(black_tile_bytes), 8):
                    chunk = black_tile_bytes[row_idx:row_idx+8]
                    hex_str = ", ".join([f"0x{val:02X}" for val in chunk])
                    black_hex_rows.append(f"    {hex_str}")
                
                # Generate hex strings for classic tile (Classic DMG)
                classic_hex_rows = []
                for row_idx in range(0, len(tile_bytes), 8):
                    chunk = tile_bytes[row_idx:row_idx+8]
                    hex_str = ", ".join([f"0x{val:02X}" for val in chunk])
                    classic_hex_rows.append(f"    {hex_str}")
                
                c_content.append("    /* Tile 0 */")
                c_content.append("#ifdef USE_BLACK_FLOOR")
                c_content.append(",\n".join(black_hex_rows) + ",")
                c_content.append("#else")
                c_content.append(",\n".join(classic_hex_rows) + ",")
                c_content.append("#endif")
            else:
                c_content.append(f"    /* Tile {t_idx} */")
                hex_rows = []
                for row_idx in range(0, len(tile_bytes), 8):
                    chunk = tile_bytes[row_idx:row_idx+8]
                    hex_str = ", ".join([f"0x{val:02X}" for val in chunk])
                    hex_rows.append(f"    {hex_str}")
                c_content.append(",\n".join(hex_rows) + ("," if t_idx < 31 else ""))
>>>>
```

### 4. `dandy-gb/tools/verify_graphics.py`
Update the C file parser to preprocess the content before extracting the hex values.

```python
<<<<
def parse_tiles_c(tiles_c_path):
    """
    Parses tiles.c to extract the dandy_tiles 2bpp binary data.
    Robustly strips comments and handles hex/decimal values and array sizes.
    """
    if not os.path.exists(tiles_c_path):
        raise FileNotFoundError(f"Source tiles definition file not found at: {tiles_c_path}")
        
    print(f"Reading tiles definition from {tiles_c_path}...")
    with open(tiles_c_path, "r") as f:
        content = f.read()

    # Step 1: Strip comments from the entire file content first to prevent matching commented-out arrays
    content_no_comments = strip_c_comments(content)
====
def parse_tiles_c(tiles_c_path, use_dark_floor=False):
    """
    Parses tiles.c to extract the dandy_tiles 2bpp binary data.
    Robustly strips comments, emulates the C preprocessor for USE_BLACK_FLOOR,
    and handles hex/decimal values and array sizes.
    """
    if not os.path.exists(tiles_c_path):
        raise FileNotFoundError(f"Source tiles definition file not found at: {tiles_c_path}")
        
    print(f"Reading tiles definition from {tiles_c_path} (use_dark_floor={use_dark_floor})...")
    with open(tiles_c_path, "r") as f:
        content = f.read()

    # Step 1: Strip comments from the entire file content first to prevent matching commented-out arrays
    content_no_comments = strip_c_comments(content)

    # Step 1.5: Emulate the C preprocessor for USE_BLACK_FLOOR
    if use_dark_floor:
        content_no_comments = re.sub(
            r'#ifdef\s+USE_BLACK_FLOOR\s+(.*?)\s+#else\s+(.*?)\s+#endif',
            r'\1',
            content_no_comments,
            flags=re.DOTALL
        )
    else:
        content_no_comments = re.sub(
            r'#ifdef\s+USE_BLACK_FLOOR\s+(.*?)\s+#else\s+(.*?)\s+#endif',
            r'\2',
            content_no_comments,
            flags=re.DOTALL
        )
>>>>
```

And update its invocation in `_main`:
```python
<<<<
    # 1. Parse tiles
    tiles_bytes = parse_tiles_c(tiles_c_path)
====
    # 1. Parse tiles
    tiles_bytes = parse_tiles_c(tiles_c_path, use_dark_floor=args.dark_floor)
>>>>
```

### 5. `dandy-gb/tests/test_graphics_pipeline.py`
Update `test_independent_tile_decoding` in the unit tests to preprocess the file content for both modes, ensuring complete test coverage for both compilation targets.

```python
<<<<
    def test_independent_tile_decoding(self):
        """Independently parse tiles.c and decode them, asserting pixel-for-pixel match."""
        # 1. Parse tiles.c using our own independent regex to verify parse_tiles_c
        with open(self.tiles_c_path, "r") as f:
            content = f.read()
        
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        content = re.sub(r'//.*?\n', '\n', content)
        
        match = re.search(r"const\s+unsigned\s+char\s+dandy_tiles\s*(?:\[[^\]]*\])?\s*=\s*\{([^}]+)\}", content, re.DOTALL)
        self.assertTrue(match, "Could not find dandy_tiles array in tiles.c")
        
        array_content = match.group(1)
        hex_values = re.findall(r"0x[0-9a-fA-F]{2}", array_content)
        self.assertEqual(len(hex_values), 512, f"Expected 512 hex values, found {len(hex_values)}")
        
        independent_bytes = bytes(int(val, 16) for val in hex_values)
        
        # Parse using tools/verify_graphics.py
        pipeline_bytes = verify_graphics.parse_tiles_c(self.tiles_c_path)
        self.assertEqual(independent_bytes, pipeline_bytes, "Parsed bytes do not match pipeline bytes")
====
    def test_independent_tile_decoding(self):
        """Independently parse tiles.c and decode them, asserting pixel-for-pixel match."""
        with open(self.tiles_c_path, "r") as f:
            content = f.read()
            
        def preprocess_content(c, use_dark):
            c = re.sub(r'/\*.*?\*/', '', c, flags=re.DOTALL)
            c = re.sub(r'//.*?\n', '\n', c)
            if use_dark:
                c = re.sub(r'#ifdef\s+USE_BLACK_FLOOR\s+(.*?)\s+#else\s+(.*?)\s+#endif', r'\1', c, flags=re.DOTALL)
            else:
                c = re.sub(r'#ifdef\s+USE_BLACK_FLOOR\s+(.*?)\s+#else\s+(.*?)\s+#endif', r'\2', c, flags=re.DOTALL)
            return c

        sprite_indices = set(list(range(9, 12)) + list(range(16, 20)) + list(range(24, 28)))

        # Test both branches: Classic DMG (use_dark_floor=False) and Atmospheric (use_dark_floor=True)
        for use_dark_floor in [False, True]:
            preprocessed_content = preprocess_content(content, use_dark_floor)
            match = re.search(r"const\s+unsigned\s+char\s+dandy_tiles\s*(?:\[[^\]]*\])?\s*=\s*\{([^}]+)\}", preprocessed_content, re.DOTALL)
            self.assertTrue(match, f"Could not find dandy_tiles array in preprocessed tiles.c (use_dark_floor={use_dark_floor})")
            
            array_content = match.group(1)
            hex_values = re.findall(r"0x[0-9a-fA-F]{2}", array_content)
            self.assertEqual(len(hex_values), 512, f"Expected 512 hex values in mode (use_dark_floor={use_dark_floor}), found {len(hex_values)}")
            
            independent_bytes = bytes(int(val, 16) for val in hex_values)
            
            # Parse using tools/verify_graphics.py
            pipeline_bytes = verify_graphics.parse_tiles_c(self.tiles_c_path, use_dark_floor=use_dark_floor)
            self.assertEqual(independent_bytes, pipeline_bytes, f"Parsed bytes do not match pipeline bytes (use_dark_floor={use_dark_floor})")
>>>>
```

---

## Verification Plan

To verify the proposed changes independently once they are implemented:
1.  **Generate the Tiles**:
    Run `make sprites` (which executes `downscale_sprites.py` under the hood) to regenerate `src/tiles.c` and `src/tiles.h`.
2.  **Inspect `src/tiles.c`**:
    Open the generated `src/tiles.c` and confirm that Tile 0 is wrapped inside the `#ifdef USE_BLACK_FLOOR` block, containing the solid black bytes (`0x00`s) and the classic DMG textured bytes (`0x20` and `0x02` at the correct rows).
3.  **Run Unit & Integration Tests**:
    Run `make test` to execute all python tests. Confirm that `test_graphics_selector.py` and `test_graphics_pipeline.py` pass without errors.
4.  **Run Visual Audits**:
    *   Run `python3 tools/verify_graphics.py` to generate `graphics_audit.png` (Classic DMG). Inspect the floor tile (top-left, Tile 0) to verify it is White and contains subtle Light Gray texture dots at (2,2) and (6,5).
    *   Run `python3 tools/verify_graphics.py --dark-floor` to generate `graphics_audit_dark.png` (Atmospheric Dark). Inspect the floor tile to verify it is solid Black.
5.  **Compile the Game ROM**:
    *   Run `make clean && make` to build the default Classic DMG ROM (`bin/dandy.gb`).
    *   To build the Atmospheric Dark ROM, compile with the preprocessor flag `USE_BLACK_FLOOR` added to `LCCFLAGS` (e.g., `make LCCFLAGS="-Wa-l -Wl-m -Wl-yo2 -DUSE_BLACK_FLOOR"`). Verify that both build successfully.
