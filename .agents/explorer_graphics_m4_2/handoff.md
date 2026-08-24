# Handoff Report: Palette & Sprite Integration (Milestone 4)

This report details the exploration and recommendations for the Graphics Compiler & Overrides portion of Milestone 4.

---

## 1. Observation

During our technical exploration, we inspected the following files and observed:

### A. Floor Tile Design & Selector
In `dandy-gb/downscale/selector.py`, Tile 0 (empty floor) is currently configured to use mathematical downscaling rather than a manual override:
```python
10:     0: "mathematical",  # Space (floor)
```
In `dandy-gb/downscale/overrides.py`, the manual override for Tile 0 is currently defined as solid black:
```python
5:     # 0: TILE_SPACE (Empty corridor floor -> Solid Black)
6:     0: [
7:         "00000000",
8:         "00000000",
9:         "00000000",
10:         "00000000",
11:         "00000000",
12:         "00000000",
13:         "00000000",
14:         "00000000"
15:     ],
```

### B. Compiler Output
In `dandy-gb/downscale/compiler.py`, the C output generation loops through all 32 tiles sequentially, packing them and writing them directly into the single `const unsigned char dandy_tiles[]` array:
```python
79:         for t_idx, tile_bytes in enumerate(compiled_tiles):
80:             c_content.append(f"    /* Tile {t_idx} */")
81:             hex_rows = []
82:             for row_idx in range(0, len(tile_bytes), 8):
83:                 chunk = tile_bytes[row_idx:row_idx+8]
84:                 hex_str = ", ".join([f"0x{val:02X}" for val in chunk])
85:                 hex_rows.append(f"    {hex_str}")
86:             c_content.append(",\n".join(hex_rows) + ("," if t_idx < 31 else ""))
```
This produces a single flat list of 512 bytes in `src/tiles.c`:
```c
5: const unsigned char dandy_tiles[] = {
6:     /* Tile 0 */
7:     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
8:     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
9:     /* Tile 1 */
```

### C. Tool and Test Constraints
In `dandy-gb/tools/verify_graphics.py`, the parsing routine naively counts the tokens in the `dandy_tiles` array, strictly enforcing that it must contain exactly 512 values:
```python
100:     if len(tokens) != 512:
101:         raise ValueError(f"Expected exactly 512 values (32 tiles * 16 bytes), but found {len(tokens)}")
```
Similarly, in the integration test `dandy-gb/tests/test_graphics_pipeline.py`:
```python
41:         hex_values = re.findall(r"0x[0-9a-fA-F]{2}", array_content)
42:         self.assertEqual(len(hex_values), 512, f"Expected 512 hex values, found {len(hex_values)}")
```

---

## 2. Logic Chain

1. **Hardware Palette Limitations & Opportunities**:
   * The GameBoy's background rendering in Classic DMG mode and Atmospheric Dark mode can be inverted almost entirely by changing the BGP hardware register (from `0xE4` to `0x1B`). This palette inversion automatically swaps light and dark values for all structural tiles (walls, doors, stairs) and sprites.
   * Swapping the hardware palette is highly efficient because the 2bpp pixel data itself does not need to change between the modes for 31 out of 32 tiles.
2. **The Special Case of Tile 0 (Floor)**:
   * The empty floor (Tile 0) is the sole exception. In Classic DMG, it must have subtle Light Gray dots (Color 1) on a White background (Color 0). In Atmospheric Dark, it must be solid Black (Color 0 in Atmospheric Mode) without any dots.
   * If we did not change Tile 0, the palette inversion in Atmospheric Mode would render the classic dots as Dark Gray (Color 1) on a Black background (Color 0). To satisfy the design requirement of a "solid Black" floor, we must compile a different 2bpp layout for Tile 0 in each mode.
3. **C Preprocessor Architecture**:
   * To compile the correct floor tile at compile-time without duplicating the other 31 tiles (which would waste valuable ROM space), the compiler should wrap Tile 0 inside `#ifdef USE_BLACK_FLOOR`/`#else`/`#endif` blocks directly within the `dandy_tiles` array in `src/tiles.c`.
4. **Resolution of Tool & Test Collisions**:
   * Wrapping Tile 0 in preprocessor blocks will increase the number of hex values in the raw C file to 528.
   * This causes `verify_graphics.py` and `test_graphics_pipeline.py` to fail because they count raw tokens without running the C preprocessor.
   * To prevent this breakage, we must modify the Python parsers to emulate the preprocessor, stripping the inactive branch based on the `--dark-floor` command-line flag or the test parameter.

---

## 3. Caveats

* **Macro-Conditioning in GameBoy Engine**: This investigation is focused on the **Graphics Compiler & Overrides**. The actual GameBoy C engine (`src/main.c`) also needs to implement compile-time toggle `#ifdef USE_BLACK_FLOOR` to configure the hardware palette registers (`BGP_REG`, `OBP0_REG`, `OBP1_REG`) correctly. That work is out-of-scope for the compiler task but is noted in the verification plan.
* **Manual Override Reliance**: We assume that setting Tile 0 to `"manual"` is the most robust way to guarantee the exact coordinates of the texture dots. If mathematical downscaling of the floor tile is desired in the future, the design can still support it, but the Classic DMG manual override ensures 100% adherence to the visual spec.

---

## 4. Conclusion

We recommend implementing compile-time conditional generation of Tile 0 inside the `dandy_tiles` array in `src/tiles.c` by modifying the python graphics compiler and downscaling overrides. 

Specifically:
1. Redefine Tile 0 override in `overrides.py` with dots at (2,2) and (6,5), and set it to `"manual"` in `selector.py`.
2. Generate the `#ifdef USE_BLACK_FLOOR` block in `compiler.py` for Tile 0, compiling the solid black tile for the `#ifdef` branch and the classic DMG tile for the `#else` branch.
3. Update `verify_graphics.py` and `test_graphics_pipeline.py` to be preprocessor-aware so that they do not break and can test both rendering branches.

---

## 5. Verification Method

Once the changes are implemented by the implementing agent, they can be verified independently using the following steps:

1. **Regenerate Assets**:
   Run `make sprites` to compile the sprite sheet.
2. **Inspect C File**:
   Verify that `src/tiles.c` contains the following block:
   ```c
       /* Tile 0 */
   #ifdef USE_BLACK_FLOOR
       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
   #else
       0x00, 0x00, 0x00, 0x00, 0x20, 0x00, 0x00, 0x00,
       0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00,
   #endif
   ```
3. **Run Unit & Integration Tests**:
   Run `make test` to ensure all Python tests pass successfully.
4. **Visual Verification**:
   * Run `python3 tools/verify_graphics.py` and check `teamwork_graphics/graphics_audit.png`. The top-left cell (Tile 0) must be White and contain two subtle Light Gray dots.
   * Run `python3 tools/verify_graphics.py --dark-floor` and check `teamwork_graphics/graphics_audit_dark.png`. The top-left cell (Tile 0) must be solid Black.
