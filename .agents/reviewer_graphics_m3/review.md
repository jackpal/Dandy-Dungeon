# Quality & Adversarial Review Report: Milestone 3

## Review Summary

**Verdict**: REQUEST_CHANGES (Fail)

While the core selection architecture and CLI integration are beautifully designed and implemented, and the visual outputs are outstandingly correct and high-quality, the Python unit test suite **fails** when executed end-to-end. This is due to a resource leak (temporary directory leak) that triggers a failure in the leak-stability test (`test_lifecycle_and_leak_stability_1000_runs`). 

The root cause is that although the worker implemented a robust `close()` method and context manager support in `DandyEnv` to prevent leaks, they failed to update the rest of the test suite files (`test_tier1.py` through `test_tier4.py`, `test_infra_check.py`, `test_adversarial_compression.py`, etc.) to actually use the context manager or call `close()` in `tearDown`. Because the `unittest` runner maintains active references to all executed test cases in memory, these unclosed environment instances keep their temporary directories alive on disk, resulting in a verified leak and test suite failure.

---

## Findings

### [Critical] Finding 1: Test Suite Failure due to Temporary Directory Leak
- **What**: The unit test suite fails when run end-to-end via `./.venv/bin/python -m unittest discover -s tests` with 1 failure in `test_lifecycle_and_leak_stability_1000_runs`.
- **Where**: All test files instantiating `DandyEnv` without closing it, specifically:
  - `tests/test_infra_check.py` (lines 17, 41, 42, 67, 98)
  - `tests/test_tier1.py` (line 13)
  - `tests/test_tier2.py` (line 13)
  - `tests/test_tier3.py` (line 13)
  - `tests/test_tier4.py` (line 13)
  - `tests/test_adversarial_compression.py` (line 13)
  - `tests/test_downscale_sprites.py` (line 13)
  - `tests/test_graphics_adversarial.py` (line 13)
- **Why**: `DandyEnv` copies `libdandy_test.so` to a unique temporary directory to ensure state isolation. The worker added a `close()` method and `__exit__` context manager to clean up these directories. However, they did not update the existing tests to call `close()` (or use `with DandyEnv() as env:`). Since the test runner keeps test case objects in memory, the `DandyEnv` instances are never garbage collected during the run, leaving their temporary directories on disk and failing the leak stability test.
- **Suggestion**: 
  1. In all test files that instantiate `self.env = DandyEnv()` in `setUp()`, implement a `tearDown()` method (or update the existing one) to explicitly call `self.env.close()` and delete/nil the reference:
     ```python
     def tearDown(self):
         if hasattr(self, "env") and self.env is not None:
             self.env.close()
             self.env = None
     ```
  2. In `test_infra_check.py`, wrap all local `DandyEnv` instantiations in `with DandyEnv() as env:` context managers to ensure immediate, deterministic cleanup.

### [Major] Finding 2: Missing Target for Test Library Compilation in Default Build
- **What**: Running `make clean && make` does not build the test library `libdandy_test.so`.
- **Where**: `dandy-gb/Makefile`
- **Why**: Running the unit tests immediately after `make clean && make` results in 125+ errors because `libdandy_test.so` is missing. The user must manually run `make test_lib` before running tests.
- **Suggestion**: The `Makefile` should either build `test_lib` as part of the default target, or the test runner / `dandy_env.py` should automatically compile it if missing, or the instructions should explicitly require `make test_lib` as a prerequisite before running tests.

---

## Verified Claims

- **GameBoy ROM builds with zero warnings/errors** → **VERIFIED (PASS)**
  - Command: `make clean && make` in `dandy-gb/` completed successfully, generating `bin/dandy.gb` and writing C structures to `src/tiles.c`/`src/tiles.h` with 0 warnings/errors.
- **Floors and Walls are mathematically downscaled** → **VERIFIED (PASS)**
  - Verified via visual inspection of `graphics_audit.png` and `graphics_audit_dark.png`. In light mode, floor is white and wall is dark gray. In dark mode, floor is black and wall is white-outlined. Both are crisp and mathematically scaled using FHDA.
- **Stairs, items, players, monsters, and arrows are correctly overridden with their hand-drawn glyphs** → **VERIFIED (PASS)**
  - Verified via visual inspection of both audit sheets. The hand-drawn glyphs (stairs, keys, heart flask, dollar sign, monsters, and player sprites) appear perfectly sharp, high-contrast, and match the native GameBoy aesthetic.
- **Sprites have correct transparency** → **VERIFIED (PASS)**
  - Verified via visual inspection of the audit sheets. The checkers background pattern shows through the transparent areas of player, monster, and arrow sprites.
- **HUD text is clean and legible** → **VERIFIED (PASS)**
  - Verified via inspection of `src/main.c`. The system loads GBDK's standard IBM font and programmatically generates an inverted font at runtime in VRAM, providing a perfectly crisp light-on-dark font for the HUD.

---

## Coverage Gaps

- **Memory Leak Stability under OS/Filesystem Constraints** — Risk Level: Low.
  - The `shutil.rmtree` call in `DandyEnv.close()` catches exceptions silently. If a filesystem lock or sandbox constraint prevents deletion, the directory will leak without any log warning.
  - *Recommendation*: Log a warning to `sys.stderr` if `shutil.rmtree` fails, rather than silencing it completely.

---

## Unverified Items

- None. All requirements and claims were independently tested and verified.
