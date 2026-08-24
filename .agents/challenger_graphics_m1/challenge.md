# Milestone 1 Graphics Conversion Pipeline Challenge Report

**Overall Risk Assessment**: **MEDIUM** (The core graphics compilation, decoding, and runtime representation are **100% correct** and mathematically sound, but the pipeline tools are **highly fragile** and the visual audit tool has a **fundamental layout mismatch**).

---

## 1. Visual Audit Tool Layout Mismatch (Critical Logical Finding)

While investigating the worker's `verify_graphics.py` tool, we uncovered a **major layout alignment mismatch** in how it generates the visual audit comparison grid (`graphics_audit.png`).

### The Flaw
The script naively iterates `for i in range(32):` and compares:
- **Left (Original)**: The sprite at index `i` in the original sprite sheet (`strike_original.png`), sliced using a 16-column layout.
- **Right (Game Boy)**: The decoded tile at index `i` in the Game Boy tileset (`tiles.c`).

However, **the Game Boy tileset layout does not align 1-to-1 with the original JS sprite sheet layout!** The Game Boy version is a demake that redesigned several assets to fit the 8x8 grid and optimized their indices for the Game Boy engine. 

As a result, the generated audit sheet compares completely mismatched assets side-by-side:
* **Cell 4 (i=4)**: Compares the original **Red Key** (JS index 4) side-by-side with Game Boy **Stairs Down** (GB index 4).
* **Cell 5 (i=5)**: Compares the original **Stairs Down** (JS index 5) side-by-side with Game Boy **Key** (GB index 5).
* **Cell 6 (i=6)**: Compares the original **Dollar Sign ($)** (JS index 6) side-by-side with Game Boy **Leg of Meat** (GB index 6).
* **Cell 7 (i=7)**: Compares the original **Potion Flask** (JS index 7) side-by-side with Game Boy **Dollar Sign ($)** (GB index 7).
* **Cell 8 (i=8)**: Compares the original **Player Robot** (JS index 8) side-by-side with Game Boy **Bomb** (GB index 8).
* **Cell 16-19 (i=16..19)**: Compares diagonal JS arrows to orthogonal Game Boy arrows, or matches completely incorrect directions (e.g. JS Arrow Left is matched to GB Arrow Up).
* **Cell 25-27 (i=25..27)**: Compares player characters with numbers (Player 2, 3, 4) to directional knight sprites (Player Up, Left, Right).

### Impact
This makes the visual comparison grid **highly misleading** and confusing for developers or reviewers. Instead of showing how the JS assets were adapted to the Game Boy, it displays mismatched assets side-by-side, rendering it ineffective as a visual verification tool.

---

## 2. Stress-Testing the Sprite Extractor (`extract_sprites.py`)

We wrote a rigorous stress-testing harness (`stress_test_extractor.py`) that mocked various syntax and formatting deviations in `dandy-js/strike.js` and executed the real `extract_sprites.py` script.

### Confirmed Vulnerabilities
1. **Fragility to Single Quotes (High Risk)**:
   * **Attack Scenario**: JavaScript allows single quotes (e.g., `strike.src = 'data:image/png;base64,' + '...';`). However, the extractor's regex only matches double quotes.
   * **Result**: **FAILED** (Script crashed with `ValueError: Could not find strike.src assignment...`).
2. **Fragility to Comments containing Quotes (High Risk)**:
   * **Attack Scenario**: If a developer adds a comment with quotes inside the assignment block (e.g. `// This is a "cool" sprite`), the extractor's simple string finder `re.findall(r'"([^"]*)"', assignment)` extracts the comment text as part of the base64 payload.
   * **Result**: **FAILED** (The image was corrupted, crashing the PNG verifier with `ValueError: Failed to verify image`).
3. **Fragility to Missing Semicolons & ASI (Medium Risk)**:
   * **Attack Scenario**: In JavaScript, semicolons are optional due to Automatic Semicolon Insertion (ASI). If a developer omits the semicolon at the end of the `strike.src` assignment, and subsequent lines define double-quoted strings (e.g., `const gameName = "Dandy=Dungeon";`), the non-greedy regex over-matches up to the next semicolon. It extracts the unrelated string, inserts the `=` padding character in the middle of the base64 string, and tries to decode it.
   * **Result**: **FAILED** (Crashed with `binascii.Error: Incorrect padding`).
4. **Formatting Robustness (Low Risk)**:
   * **Attack Scenario**: Spaces around `=` or `+` removed (e.g. `strike.src="data:image/png;base64,"+...+...`).
   * **Result**: **PASSED** (Successfully extracted and verified, as the regex uses `\s*` correctly).

---

## 3. Stress-Testing the Graphics Verifier (`verify_graphics.py`)

We wrote a second stress-testing harness (`stress_test_verifier.py`) targeting the C parsing logic in `verify_graphics.py` when reading `dandy-gb/src/tiles.c`.

### Confirmed Vulnerabilities
1. **Explicit Array Size Declaration (High Risk)**:
   * **Attack Scenario**: Declaring the array with an explicit size or macro (e.g., `const unsigned char dandy_tiles[512] = { ... };` or `dandy_tiles[DANDY_NUM_TILES * DANDY_TILE_SIZE]`), which is standard and recommended C practice.
   * **Result**: **FAILED** (The regex `dandy_tiles\[\]` only matches empty brackets, causing the script to crash with `ValueError: Could not find dandy_tiles array in tiles.c`).
2. **Uppercase Hex Prefix (Medium Risk)**:
   * **Attack Scenario**: Writing hex values in uppercase, which is common depending on formatting tools (e.g., `0XAA` or `0X2B`).
   * **Result**: **FAILED** (The regex `0x[0-9a-fA-F]{2}` only matches lowercase `0x`, causing the parser to find 0 hex values and crash with `ValueError: Expected 512 hex values`).
3. **Hex Values inside Comments (High Risk)**:
   * **Attack Scenario**: Comments inside the C array containing hex-like text (e.g. `/* offset 0xAA */` or `/* Tile 0x00 */`).
   * **Result**: **FAILED** (The regex blindly matches hex patterns inside comments, resulting in a count of 513 hex values instead of 512, crashing the parser with `ValueError`).
4. **Missing Files (Low Risk)**:
   * **Attack Scenario**: Missing `strike_original.png` or `tiles.c`.
   * **Result**: **PASSED** (Handled gracefully with `FileNotFoundError` or standard file exceptions).

---

## 4. Programmatic Decoder Verification (100% Correctness)

To verify the mathematical and logical correctness of the worker's Game Boy 2bpp decoding implementation, we wrote `verify_decoder.py`:
1. It implemented an **independent, comment-aware C parser** that strips comments before parsing, ensuring no false matches.
2. It re-implemented the **planar 2bpp decoding logic** independently from scratch.
3. It imported the worker's `decode_gb_tile` function, decoded all 32 tiles using both decoders, and programmatically compared the resulting 8x8 pixel grids for both backgrounds and sprites.

### Results
* **Pixel-Perfect Match**: **100% SUCCESS**.
* **Off-by-one or bit-shifting errors**: **NONE**.
* **Palette mapping errors**: **NONE**.
* The worker's decoding logic is mathematically perfect and completely accurate to the Game Boy hardware specifications.

---

## 5. Correctness of GBDK Compiled Representation (`tiles.c` & `main.c`)

We verified the correctness of the compiled representation in `src/tiles.c`:
1. We wrote `verify_compiled_representation.py`, which imported the source `GLYPHS` definitions from `compile_bmp_sprites.py`, compiled them to 2bpp bytes in memory, and compared them byte-for-byte against the actual content of `src/tiles.c`.
   * **Result**: **100% Match**. Every byte in `tiles.c` exactly represents the intended pristine pixel art.
2. We analyzed the Game Boy palette register configurations in `dandy-gb/src/main.c`:
   * `BGP_REG = 0x1B` (binary `00 01 10 11`) correctly maps Color Index 0 to Black, 1 to Dark Gray, 2 to Light Gray, and 3 to White.
   * `OBP0_REG = 0xE0` (binary `11 10 00 00`) correctly maps Color Index 0 to Transparent, 1 to White, 2 to Dark Gray, and 3 to Black.
   * This is 100% consistent with both the compiler's bit-packing design and the verifier's color mapping.

---

## Final Verdict

The core implementation of Milestone 1 (the actual pixel art compilation, the Game Boy 2bpp byte representation in `tiles.c`, the decoding logic, and the Game Boy runtime integration) is **100% CORRECT and of extremely high quality**.

However, the pipeline tools and validation scripts suffer from **poor robustness**:
1. **`verify_graphics.py`** visual comparison is logically broken due to a layout mismatch, comparing unrelated sprites.
2. Both **`extract_sprites.py`** and **`verify_graphics.py`** parsers use fragile, naive regular expressions that crash on standard formatting variations (single quotes, explicit C array sizes, uppercase hex) or comment lines.

### Actionable Recommendations
1. **Fix `verify_graphics.py` Layout Mapping**: Update the visual comparison generator to map JS sprite indices to their corresponding redesigned GB tile indices (e.g. map JS Key at index 4 to GB Key at index 5).
2. **Harden the JS Parser**: Update `extract_sprites.py` to strip comments and handle both single and double quotes when extracting the base64 data.
3. **Harden the C Parser**: Update `verify_graphics.py` to strip comments and support optional array sizes and uppercase hex prefixes (`0[xX]`) in `tiles.c`.
