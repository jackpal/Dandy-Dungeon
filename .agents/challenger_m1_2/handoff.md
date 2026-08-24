# Handoff Report — Challenger 2 (Milestone 1)

## 1. Observation
We conducted correctness, robustness, and vulnerability testing on the graphics verification tool `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/verify_graphics.py`.

The following commands and outputs were obtained:
- **Baseline Correctness Tests**: We ran `test_2bpp_decoding.py` (which implements independent 2bpp and nearest-neighbor upscaling validators).
  Output:
  ```
  Running test_decoding_correctness...
  Generated tile bytes: ['0x55', '0x33', '0xaa', '0xcc', '0xf', '0xf', '0xf0', '0xf', '0xf', '0x55', '0xf0', '0xaa', '0x55', '0x0', '0x55', '0xff']
  Decoding correctness test PASSED!
  Running test_upscaling_correctness...
  Nearest-neighbor upscaling correctness test PASSED!
  All correctness tests passed!
  ```
- **Robustness Tests**: We ran `test_robustness.py` to test various error conditions (missing files, syntax changes, incorrect sizes). All of these resulted in proper failures (exit code 1) with traceback or custom error messages:
  - Missing `strike.js` $\to$ `FileNotFoundError`
  - Missing `tiles.c` $\to$ `FileNotFoundError`
  - Corrupt base64 in `strike.js` $\to$ `PIL.UnidentifiedImageError`
  - Extra double quotes in `strike.js` $\to$ `binascii.Error: Incorrect padding`
  - Comments containing hex in `tiles.c` (extra bytes) $\to$ `ValueError: Expected 512 bytes (32 tiles * 16 bytes), but found 514 bytes.`
  - Syntax change in `tiles.c` $\to$ `ValueError: Could not find dandy_tiles array in tiles.c`
- **Silent Comment-Based Corruption**: We ran `test_silent_corruption.py` to test the case where one tile is commented out but its hex values remain in the comment (31 active tiles + 1 commented-out tile).
  Output:
  ```
  Setting up silent corruption mock in tiles.c...
  Original hex count: 512
  Running verify_graphics.py...
  Exit Code: 0
  ...
  Successfully generated visual comparison sheet at: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/graphics_audit.png

  [VULNERABILITY CONFIRMED] Silent Corruption Vulnerability exists!
  The script successfully parsed commented-out hex values, completed with exit code 0, and generated an audit sheet containing commented-out data as if it were compiled!
  ```

---

## 2. Logic Chain
1. **2bpp Correctness**: In `verify_graphics.py` (lines 92-99), `low` and `high` bytes are read in pairs, and bitwise operations extract bit 0 and bit 1 to compute the color index. Since our independent test `test_2bpp_decoding.py` matched this against the GBDK specification byte-by-byte and pixel-by-pixel for a complex color pattern, the 2bpp decoding math is correct.
2. **Upscaling Correctness**: `Image.NEAREST` was tested by upscaling a single-pixel image 16x. We verified that the target pixel became a perfect 16x16 square with sharp boundaries and no interpolation artifacts, confirming the upscaling math is correct.
3. **Silent Comment Corruption**: The regex in `verify_graphics.py` (line 75) uses `re.findall(r'0x[0-9a-fA-F]{2}', array_str)` to extract hex values. Because it does not strip C-style comments first, it extracts hex values inside comments. Under a scenario where a tile is commented out but its hex is left as a comment, the script reads 512 bytes, exits with `0`, and shows the commented-out tile as "verified." However, the compiler ignores the comment, resulting in only 31 compiled tiles. This masks a critical out-of-bounds memory read bug in the game ROM.

---

## 3. Caveats
- No emulator-level verification of the Game Boy ROM was performed, but the length mismatch and resulting memory-safety implications on Game Boy hardware were proven analytically.
- File descriptor leaks were not observed on the current environment during testing because PIL/OS handles them gracefully, but using a context manager for `Image.open` remains a recommended practice.

---

## 4. Conclusion
The graphics extraction and verification tool `verify_graphics.py` is **algorithmically correct** but **syntactically insecure/fragile**. It can be tricked into certifying a broken, incomplete asset array as fully verified, which can result in severe ROM bugs.

**Key Actionable Recommendations**:
1. Strip C-style comments from `tiles.c` before executing the regex search.
2. Narrow the regex in `strike.js` to target the `strike.src` assignment specifically, rather than matching all double-quoted strings globally.
3. Wrap `Image.open` in a `with` block to prevent potential file descriptor leaks in other environments.

---

## 5. Verification Method
To independently run the test suite and verify these findings, run the following commands from the `dandy-gb/` directory:
1. **Verify Correctness (2bpp & Upscaling)**:
   ```bash
   .venv/bin/python3 /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/challenger_m1_2/test_2bpp_decoding.py
   ```
2. **Verify Robustness (Graceful Crashes)**:
   ```bash
   .venv/bin/python3 /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/challenger_m1_2/test_robustness.py
   ```
3. **Verify Silent Comment Corruption**:
   ```bash
   .venv/bin/python3 /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/challenger_m1_2/test_silent_corruption.py
   ```
All test scripts are located in `.agents/challenger_m1_2/`.
Detailed results and explanations are in `.agents/challenger_m1_2/challenge.md`.
