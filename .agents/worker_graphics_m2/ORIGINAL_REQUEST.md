## 2026-06-21T00:45:35Z
You are a worker agent (`teamwork_preview_worker`) tasked with implementing and verifying Milestone 2: Mathematical Downscaling Pipeline of the Dandy Dungeon graphics conversion pipeline.

Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/worker_graphics_m2/

Objectives:
1. Read the comprehensive architectural and algorithmic blueprint at `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/orchestrator_graphics/m2_downscaler_blueprint.md`.
2. Implement the modular Python downscaler tool at `dandy-gb/tools/downscale_sprites.py` and the library packages inside `dandy-gb/downscale/` exactly as specified in the blueprint.
3. Implement the custom Font-Hinted Downscaling Algorithm (FHDA) in `dandy-gb/downscale/algorithms/custom.py` following the exact 6 steps described.
4. Implement the GBDK 2bpp planar packing and C compilation code in `dandy-gb/downscale/compiler.py`.
5. Implement the comprehensive unit and adversarial test suite in `dandy-gb/tests/test_downscale_sprites.py` verifying all unit, edge-case, and robust error handling behaviors specified in Section 5 of the blueprint.
6. Run the test suite using the virtual environment's python (`dandy-gb/.venv/bin/python -m unittest discover -s tests -p "test_*.py"`) and ensure 100% of the tests pass.
7. Run the downscaler on `dandy-gb/teamwork_graphics/strike_original.png` using the `font-hinting` algorithm to compile the new assets to `dandy-gb/src/tiles.c` and `dandy-gb/src/tiles.h`:
   - `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/.venv/bin/python tools/downscale_sprites.py --input teamwork_graphics/strike_original.png --output-c src/tiles.c --output-h src/tiles.h --output-preview teamwork_graphics/downscale_preview.png`
8. Compile the GameBoy C codebase by running `make clean && make` inside `dandy-gb/` and ensure that it builds cleanly with zero compiler/linker warnings and zero errors, outputting `bin/dandy.gb`.
9. Run the visual verification tool to regenerate the audit sheets:
   - `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/.venv/bin/python tools/verify_graphics.py`
   - `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/.venv/bin/python tools/verify_graphics.py --dark-floor`
   Verify that both `graphics_audit.png` and `graphics_audit_dark.png` are successfully generated.
10. Write a detailed handoff report `handoff.md` in your working directory summarizing your implementation, the mathematical correctness of your FHDA downscaler, and all command execution/test logs.

Domain Skill:
You should load and follow the software engineering methodology skill at:
`/google/src/files/head/depot/google3/research/omega/teamwork/playbooks/software_engineering/SKILL.md`

Integrity Warning:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## 2026-06-21T00:55:50Z
You are a worker tasked with implementing critical code-quality and robustness fixes to the mathematical downscaling pipeline in the `dandy-gb` project.

### Target Files:
1. `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/downscale/manager.py`
2. `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/downscale/algorithms/standard.py`
3. `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/downscale/algorithms/custom.py`

### Required Fixes:
1. **Pillow Image Resource Leak in `manager.py`**:
   - In `SpriteSheetManager.load_and_slice` (around line 22), `Image.open(image_path)` is called, but the image is never closed. Wrap it in a `with` block (e.g., `with Image.open(image_path) as img:`) or use an explicit `try...finally: img.close()` block. Ensure that all downstream slicing operations happen within the context or after the data is fully copied, so that no file handles are leaked.
2. **Pillow Image Resource Leak in `standard.py`**:
   - In `StandardDownscaler.downscale_tile` (around line 73), `Image.fromarray` and `img.resize` are called. While these are in-memory operations, we want to ensure any internal resources are cleaned up. Wrap them in `with` blocks or explicitly close them to guarantee that no heap memory accumulates over long execution runs.
3. **Alpha Safety Check in `custom.py`**:
   - In `FontHintingDownscaler._flood_fill_segmentation` (around line 158), the classification of `CH_BLACK` pixels checks only RGB: `if r == 0 and g == 0 and b == 0:`.
   - To prevent false positives where transparent pixels with a black RGB signature (e.g., RGBA `(0,0,0,0)`) are misclassified as outline/black pixels, add an explicit alpha channel check to ensure it is fully opaque: `if r == 0 and g == 0 and b == 0 and tile[y, x][3] == 255:`.

### Verification Steps:
After making the changes, you MUST verify your work by running the following commands from the `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb` directory:
1. Run the test suite using the virtualenv Python:
   `./.venv/bin/python -m unittest discover -s tests`
2. Run the stress test to verify that no memory/resource leaks occur and all 172+ tests pass perfectly:
   `./.venv/bin/python tools/stress_test_downscaler.py`
3. Verify local GBDK build by running:
   `make clean && make` (or check if there is a Makefile in `dandy-gb/` and run the appropriate compile commands to ensure a clean build).

### MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Please write a detailed report of your changes in `changes.md` in your own agent folder, and report your findings and build/test logs in your handoff.
