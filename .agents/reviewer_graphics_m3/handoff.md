# Handoff Report: Milestone 3 - Comparative Selection & Packing (Review & Audit)

This report documents the independent review and audit findings for Milestone 3 (Comparative Selection & Packing) of the GameBoy graphics pipeline.

---

## 1. Observation

We directly observed and verified the following:

### A. GBDK ROM Build Success
Running `make clean && make` in `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb` completed successfully with zero warnings/errors. Key compiler output:
```
/usr/local/google/home/jackpal/Developer/gbdk/bin/lcc -Wf--opt-code-size -c -o obj/tiles.o src/tiles.c
/usr/local/google/home/jackpal/Developer/gbdk/bin/lcc -Wa-l -Wl-m -Wl-yo2 -o bin/dandy.gb obj/main.o obj/dandy_core.o obj/gameboy_hal.o obj/levels.o obj/tiles.o
----------------------------------------
Build successful: bin/dandy.gb
----------------------------------------
```

### B. Unit Test Suite Failure (Temp Directory Leak)
Running `./.venv/bin/python -m unittest discover -s tests` in `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb` failed with a test failure in `test_infra_stress.py`:
```
======================================================================
FAIL: test_lifecycle_and_leak_stability_1000_runs (test_infra_stress.TestInfraStress.test_lifecycle_and_leak_stability_1000_runs)
Instantiate and delete DandyEnv 1000 times to verify no FD, library, temp dir, or memory leaks.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tests/test_infra_stress.py", line 112, in test_lifecycle_and_leak_stability_1000_runs
    self.assertLessEqual(end_temp_dirs, stable_temp_dirs, f"Temp directory leak detected! Leftover: {get_temp_env_dirs()}")
AssertionError: 1 not less than or equal to 0 : Temp directory leak detected! Leftover: ['/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tests/.temp_envs/dandy_env_25_64c9s']

----------------------------------------------------------------------
Ran 176 tests in 7.042s

FAILED (failures=1, expected failures=3)
```

### C. Missing Test Library Error on First Run
Running the tests immediately after `make clean` without recompiling `libdandy_test.so` resulted in:
```
[DandyEnv] ERROR: Temp lib file at /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tests/.temp_envs/dandy_env_qxu2bg_5/libdandy_test.so is 0 bytes! Source was /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/libdandy_test.so (0 bytes)
[DandyEnv] CDLL load failed. Temp lib size: 0 bytes.
...
OSError: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tests/.temp_envs/dandy_env_qxu2bg_5/libdandy_test.so: file too short
```
This is because `make clean` deletes `libdandy_test.so` and `make` does not build it; only `make test_lib` compiles it.

### D. Missing Environment Cleanup in Test Suite
A scan of all unit test files revealed that most tests instantiate `self.env = DandyEnv()` in `setUp()` but do not close it in `tearDown()`:
- `tests/test_tier1.py`, `test_tier2.py`, `test_tier3.py`, `test_tier4.py`, `test_adversarial_compression.py`, `test_downscale_sprites.py`, and `test_graphics_adversarial.py` have `setUp` but do not call `close()`.
- `tests/test_graphics_pipeline.py` has `setUp` but no `tearDown` at all.
- `tests/test_infra_check.py` instantiates local variables `env = DandyEnv()` inside several test methods without context managers.

### E. Visual Audit Sheet Correctness
We generated and inspected both audit sheets:
- `teamwork_graphics/graphics_audit.png`
- `teamwork_graphics/graphics_audit_dark.png`
Visual inspection confirmed:
1. Floors and Walls are mathematically downscaled using the custom Font-Hinted Downscaling Algorithm (FHDA).
2. Stairs, items, players, monsters, and arrows are correctly overridden with their hand-drawn glyphs.
3. Sprites (players, monsters, and arrows) have correct transparency, with the checkers background showing through transparent areas.
4. HUD text is rendered crisp and legible by programmatically inverting GBDK's standard IBM font in VRAM.

---

## 2. Logic Chain

1. **Observation A & E**: The GameBoy ROM builds with zero warnings/errors, and the visual audit sheets are 100% correct, displaying high contrast, correct sprite transparency, clean HUD text, and high-fidelity hand-drawn overrides.
2. **Observation B & D**: The unit test suite fails due to a temporary directory leak when run end-to-end. The leak-stability test (`test_lifecycle_and_leak_stability_1000_runs`) checks for any active temporary directories under `tests/.temp_envs/`. Since other test suites (like `test_tier1.py` through `test_tier4.py`, `test_infra_check.py`, etc.) instantiate `DandyEnv` without calling `close()` or using context managers, their directories remain active.
3. **Inference 1**: The python `unittest` runner keeps test case objects in memory to report results. Because these test case objects hold active references to `self.env`, Python's garbage collector cannot reclaim them, so their `__del__` methods are never called, and their temporary directories leak on disk during the test suite run.
4. **Inference 2**: Therefore, the worker's implementation of `close()` in `DandyEnv` is a "facade" or incomplete fix in practice, because they did not update the rest of the test files to use it. This causes the test suite to fail end-to-end.
5. **Observation C**: The default `make` command does not build the test library `libdandy_test.so`, causing test failures if run immediately after `make clean`.
6. **Conclusion**: While the graphics selection and compiler pipeline itself is excellent and visually perfect, the work product cannot be approved because the test suite is broken. A verdict of `REQUEST_CHANGES` is required to fix the test environment leaks.

---

## 3. Caveats

- **PyBoy Emulator E2E Tests**: Milestone 3 does not include the PyBoy emulator E2E tests (`verify_emulator.py`), which are scheduled for Milestone 5.
- **Arrow Flight Orientation Bug**: As noted by previous reviewers, the arrow sprite orientations (flying Up/Left pointing incorrectly or being invisible) are core engine rendering issues in `dandy_core.c`/`gameboy_hal.c`, not downscaler issues. This is deferred to Milestone 4.

---

## 4. Conclusion

The Milestone 3 implementation is **rejected (FAIL)** with a verdict of **REQUEST_CHANGES**. 

**Actionable fixes required**:
1. Update all test suites that instantiate `self.env = DandyEnv()` in `setUp()` to implement a `tearDown()` method that calls `self.env.close()` and sets `self.env = None`.
2. Update `test_infra_check.py` to wrap all local `DandyEnv` instantiations in `with DandyEnv() as env:` blocks.
3. (Optional but highly recommended) Update the `Makefile` to include `test_lib` as part of the default build target or document that `make test_lib` must be run before tests.

---

## 5. Verification Method

To verify the fixes independently:

### A. Run GBDK Compile
Run `make clean && make` in `dandy-gb/`.
*Expected result*: Build succeeds with 0 warnings/errors.

### B. Run Unit Test Suite
Run `make test_lib` to build the shared library, then run the tests:
```bash
./.venv/bin/python -m unittest discover -s tests
```
*Expected result*: All 176 tests pass successfully (`OK (expected failures=3)`), with no temporary directory leaks.
