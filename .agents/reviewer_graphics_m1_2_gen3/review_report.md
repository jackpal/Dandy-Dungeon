# Milestone 1 Code & Visual Review Report

**Verdict**: **REQUEST_CHANGES** (FAIL)

---

## Review Summary
While the graphics assets themselves are compiled successfully into the GameBoy ROM, and the rendering/decoding logic correctly handles the 2bpp planar GameBoy format (with excellent visual quality that satisfies the C1-C5 rubrics), the implementation contains **one critical test failure** and **one major verification tool bug** that must be resolved before approval:
1. **Unit Test Failure**: The test suite fails on `test_lifecycle_and_leak_stability_1000_runs` in `test_infra_stress.py` due to a temporary directory leak.
2. **Incorrect Sprite Mapping**: The programmatic verification tool `verify_graphics.py` has multiple scrambled and incorrect index mappings in `GB_TO_JS_MAPPING`. This causes the generated side-by-side visual audit sheets (`graphics_audit.png` and `graphics_audit_dark.png`) to compare entirely different assets (e.g., comparing the Key to the Stairs Down cross, and the Money/Gold to the Key), which invalidates the visual audit's trustworthiness.

---

## Findings

### [Critical] Finding 1: Test Suite Failure (Temp Directory Leak)
- **What**: The unit test `test_lifecycle_and_leak_stability_1000_runs` fails with an `AssertionError`.
- **Where**: `tests/test_infra_stress.py`, line 114.
- **Why**: The test instantiates `DandyEnv` 1000 times to verify leak stability. It detects that a temporary directory under `tests/.temp_envs/` (e.g., `dandy_env_alrfbsr7`) was leaked and not cleaned up, causing the assertion `self.assertLessEqual(end_temp_dirs, stable_temp_dirs)` to fail.
- **Suggestion**: Ensure that the `DandyEnv` class or its test harness robustly cleans up all temporary directories in its `__del__` or `close()` method, or that the stress test correctly disposes of the environments.

### [Major] Finding 2: Scrambled Sprite Mapping in `verify_graphics.py`
- **What**: Multiple indices in `GB_TO_JS_MAPPING` are incorrect and scrambled.
- **Where**: `tools/verify_graphics.py`, lines 17–50.
- **Why**: The mapping is supposed to align GBDK C tile indices with the corresponding original JS tile indices for side-by-side comparison. However, the following mappings are incorrect:
  - **Stairs Down**: GB index 4 (Stairs Down) is mapped to JS index 5 (Red Key). Should map to **JS index 4** (Stairs Down / Blue Cross / "D" symbol).
  - **Key**: GB index 5 (Key) is mapped to JS index 4 (Stairs Down / Blue Cross / "D" symbol). Should map to **JS index 5** (Red Key).
  - **Food**: GB index 6 (Food) is mapped to JS index 7 (Money/Gold). Should map to **JS index 6** (Food Flask).
  - **Money/Gold**: GB index 7 (Money/Gold) is mapped to JS index 6 (Food Flask). Should map to **JS index 7** (Money/Gold / "$").
  - **Arrow Down**: GB index 16 is mapped to JS index 23 (Player Up). Should map to **JS index 21** (Arrow Down).
  - **Arrow Up**: GB index 17 is mapped to JS index 19 (Arrow Right). Should map to **JS index 18** (Arrow Up).
  - **Arrow Right**: GB index 19 is mapped to JS index 21 (Arrow Down). Should map to **JS index 19** (Arrow Right).
  This causes the generated visual audit sheet to display complete mismatches (e.g., comparing a key shape to a cross shape), making the audit sheet misleading and incorrect.
- **Suggestion**: Update the `GB_TO_JS_MAPPING` dictionary in `tools/verify_graphics.py` with the correct indices.

### [Minor] Finding 3: Inaccurate/Confusing Comments in `verify_graphics.py`
- **What**: The comments inside `GB_TO_JS_MAPPING` contain confusing and incorrect explanations of the indices.
- **Where**: `tools/verify_graphics.py`, lines 29–30:
  ```python
  11: 11,  # Monster 3 (Golem maps to JS index 11 Heart monster)
  12: 12,  # Heart (Flask maps to JS index 12 Skull monster)
  ```
- **Why**: In the original sprite sheet, JS index 11 is the **Heart** and JS index 12 is the **Flask/Skull**. The comments claim that Golem maps to JS 11 Heart and Flask maps to JS 12 Skull, which is highly confusing.
- **Suggestion**: Update the comments to reflect the actual semantic meanings (JS 11 is Heart, JS 12 is Flask/Skull).

---

## Verified Claims

- **ROM Build Success** &rarr; verified via `make clean && make` &rarr; **PASS**
  - Compiled and linked `bin/dandy.gb` successfully with zero compiler/linker warnings and zero errors.
- **2bpp Planar Tile Decoding** &rarr; verified via `test_independent_tile_decoding` in `test_graphics_pipeline.py` &rarr; **PASS**
  - Programmable decoding matches a pixel-for-pixel independent implementation of GameBoy 2bpp planar decoding for both Light Floor (Classic DMG) and Dark Floor (Atmospheric) modes.
- **Nearest-Neighbor Upscaling (No Anti-Aliasing/Blur)** &rarr; verified via `test_nearest_neighbor_upscaling` &rarr; **PASS**
  -プログラム checks that each 16x16 sub-block in the upscaled 128x128 tiles has perfectly uniform color, ensuring no bilinear filtering or blur was introduced during scaling.
- **Base64 Extraction Robustness** &rarr; verified via `test_base64_robustness` &rarr; **PASS**
  - The base64 extractor successfully handles unexpected newlines and whitespaces in `strike.js`.

---

## Visual Audit Rubric Assessment
Visual assets `graphics_audit.png` and `graphics_audit_dark.png` were audited against the 5-point rubric:

- **C1. Conceptual Faithfulness**: **PASS (with mapping caveat)**
  - The Wall tile matches the original style (diagonal stripes, no brick substitution).
  - The Gold tile is drawn as a recognizable `$` symbol.
  - Key, food flask, and monsters have highly recognizable and faithful shapes.
  - *Caveat*: Because of the scrambled mapping in the verification tool, the side-by-side comparison shows different concepts next to each other, but the assets themselves are conceptually faithful.
- **C2. Detail & Outline Integrity**: **PASS**
  - Outlines, borders, and silhouettes are complete and crisp with no clipping.
- **C3. Symmetry**: **PASS**
  - Symmetrical tiles (Stairs Up, Door, Key center, $) are perfectly centered and symmetric where applicable on the 8x8 grid.
- **C4. Contrast & Readability**: **PASS**
  - Classic DMG (Light Floor) successfully renders the floor as White, and the sprites as dark silhouettes.
  - Atmospheric (Dark Floor) successfully renders the floor as Black, and sprites with bright White bodies and Black outlines, making them highly legible.
- **C5. Transparency & Borders**: **PASS**
  - Sprite tiles are correctly rendered over the 8x8 checkerboard background grid, demonstrating that Color 0 is successfully treated as transparent with no solid background blocks.

---

## Adversarial Critique & Stress Testing

### 1. Assumption Stress-Testing: Trusting the Verification Tool
- **Assumption challenged**: That the programmatic verification tool's side-by-side audit sheet guarantees visual equivalence.
- **Attack scenario**: If a developer updates a GameBoy sprite incorrectly, they might look at the audit sheet and see a mismatch. However, because the audit sheet is *already* scrambled, they might dismiss the mismatch as "just another mapping bug" and push broken graphics to production. Alternatively, a real regression could be hidden because a sprite is compared with an empty or different tile.
- **Blast radius**: High. It undermines the developer's trust in the verification tool, leading them to ignore visual audit mismatches entirely.
- **Mitigation**: Fix `GB_TO_JS_MAPPING` immediately and add a unit test that validates the semantic correctness of the mapping (e.g., by checking color presence or pixel density of the mapped pairs).

### 2. Test Suite Coverage Gap
- **Assumption challenged**: That a passing test suite guarantees a correct graphics pipeline.
- **Attack scenario**: A developer could completely swap the sprite bytes for the Wall and the Key in `src/tiles.c`. The unit tests in `test_graphics_pipeline.py` would still pass perfectly because they only check that the decoding is consistent with the C source bytes, not that the C source bytes match the semantic meaning of the original tiles.
- **Blast radius**: Medium. Semantically swapped assets could easily bypass the pipeline tests.
- **Mitigation**: Add a lightweight hashing or pixel-distribution check in the unit tests to verify that `GB tile X` roughly matches the visual layout or pixel density of `JS tile Y`.

---

## Unverified Items
- **None**. All items within the scope of Milestone 1 graphics extraction, compilation, and testing have been fully investigated and verified.
