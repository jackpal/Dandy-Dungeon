# Handoff Report — graphics_m1_1

## 1. Observation
- **Code Locations**:
  - `dandy-gb/tools/extract_sprites.py` (Sprite extraction script)
  - `dandy-gb/tools/verify_graphics.py` (Graphics verification script)
  - `dandy-gb/src/tiles.c` (GBDK 2bpp tiles data)
  - `dandy-gb/src/main.c` (Hardware palette configuration)
  - `dandy-js/strike.js` (Original JavaScript sprite sheet)
- **Harness & Verification Output**:
  - The independent verification script `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/teamwork_preview_challenger_graphics_m1_1/verify_pipeline.py` was executed and all tests passed:
    ```
    SUCCESS: Robustness edge cases tested successfully! Documented regex limitations.
    .SUCCESS: 32 tiles decoded independently and verified pixel-for-pixel against graphics_audit.png!
    SUCCESS: Exact nearest-neighbor upscaling verified with zero blur or antialiasing!
    ..
    ----------------------------------------------------------------------
    Ran 3 tests in 1.187s

    OK
    ```
- **Palette configurations observed in `src/main.c`**:
  - `BGP_REG = 0x1B;` (BGP mapping: Color 0 -> Black, 1 -> Dark Gray, 2 -> Light Gray, 3 -> White)
  - `OBP0_REG = 0xE0;` (OBP0 mapping: Color 0 -> Transparent, 1 -> White, 2 -> Dark Gray, 3 -> Black)
- **Upscaling logic in `verify_graphics.py`**:
  - Uses `Image.Resampling.NEAREST` or `Image.NEAREST` to upscale sprites and decoded tiles by $8\times$ and $16\times$ respectively.

---

## 2. Logic Chain
1. **Palette Correctness**:
   - The observed hardware registers in `src/main.c` are `BGP_REG = 0x1B` and `OBP0_REG = 0xE0`.
   - Decoding this bit-configuration matches the exact color arrays defined in `verify_graphics.py`:
     - BGP: `colors = [(0, 0, 0), (96, 96, 96), (176, 176, 176), (255, 255, 255)]`
     - OBP0: `colors = [(0, 0, 0), (255, 255, 255), (96, 96, 96), (0, 0, 0)]` (with transparent mapped to black for rendering).
   - This proves that background tiles and sprite tiles are mapped to their correct respective color schemes in the visual audit sheet.
2. **Upscaling Exactness**:
   - The test script `verify_pipeline.py` sampled every single pixel within each upscaled $16\times16$ block in `graphics_audit.png`.
   - Since all pixels in each block were found to be completely uniform and matched the source pixel's decoded color, the upscaling is mathematically proven to be exact nearest-neighbor (no interpolation, filtering, or blurring).
3. **Decoded Pixel Correctness**:
   - The independent 2bpp Game Boy decoder implemented in `verify_pipeline.py` matched the pixels rendered in `graphics_audit.png` pixel-for-pixel.
   - This proves that the decoding logic in `verify_graphics.py` is 100% correct.
4. **Extraction Logic Robustness**:
   - Systematic syntax variation testing showed that `extract_sprites.py`'s regex successfully handles extra whitespace/newlines.
   - However, the regex is fragile to syntax modifications in `strike.js`, such as single quotes (`'`), ES6 backticks (\``), or a lack of concatenation (`+`). These edge cases have been fully documented.

---

## 3. Caveats
- The verification only covers static graphics extraction and rendering. It does not cover runtime tile collision, map indexing, or dynamic sprite positioning during gameplay.
- Robustness findings show that changes to the formatting style of `dandy-js/strike.js` (e.g. auto-formatting via Prettier using single quotes or ES6 backticks) will break the extraction script unless the regex is updated.

---

## 4. Conclusion
The graphics extraction and verification pipeline is **correct, pixel-perfect, and fully functional**. The verdict is a clear, binary **PASS**. 

To prevent future breakage of the extraction tool, a minor recommendation is made to enhance the regex robustness in `extract_sprites.py` to support single quotes, backticks, and single-string assignments.

---

## 5. Verification Method
To independently rerun the verification, execute the following commands in the workspace:

```bash
# 1. Activate virtual environment and run the pipeline tools
cd /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb
.venv/bin/python3 tools/extract_sprites.py
.venv/bin/python3 tools/verify_graphics.py

# 2. Execute the independent test suite
.venv/bin/python3 /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/teamwork_preview_challenger_graphics_m1_1/verify_pipeline.py
```

All tests must return `OK`.
