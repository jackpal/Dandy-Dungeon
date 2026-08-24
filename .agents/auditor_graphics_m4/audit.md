# Forensic Audit Report: Milestone 4 (Palette & Sprite Integration)

**Work Product**: Milestone 4 Implementation (C source, Python graphics compiler, Makefile, and E2E Tests)
**Profile**: General Project
**Verdict**: CLEAN

---

### Phase Results

#### Phase 1: Source Code Analysis
1.  **Hardcoded Output Detection**: **PASS**
    *   No hardcoded test results, expected outputs, or fake verification strings were found in the codebase or test files.
    *   Unit tests in `tests/test_graphics_pipeline.py`, `tests/test_graphics_selector.py`, `tests/test_downscale_sprites.py`, and `tests/test_graphics_adversarial.py` are fully dynamic, asserting correctness via independent decoders and verifying edge cases (including expected failures).
    *   The E2E emulator test harness (`tests/verify_emulator.py`) parses WRAM symbols dynamically from the `.map` file, boots a real ROM inside PyBoy, and asserts initial state and simulated movement changes directly in the emulated GameBoy RAM.
2.  **Facade Detection**: **PASS**
    *   The GameBoy hardware palette setup in `src/main.c` is fully genuine, writing authentic register values to `BGP_REG`, `OBP0_REG`, and `OBP1_REG` for both Classic DMG (`0xE4`, `0xD8`) and Atmospheric Dark (`0x1B`, `0xE0`) modes.
    *   The light-on-dark font for the scoreboard is programmatically generated at boot-time in VRAM by reading the standard font, inverting each byte using bitwise NOT (`~`), and writing it back to index 160.
    *   The sprite compilation tool (`tools/downscale_sprites.py` and `downscale/compiler.py`) genuinely downscales PNG graphics and packs them into GameBoy 2bpp planar bytes, writing the `#ifdef USE_BLACK_FLOOR` blocks into `src/tiles.c` automatically.
3.  **Pre-populated Artifact Detection**: **PASS**
    *   Visual audit sheets (`teamwork_graphics/graphics_audit.png` and `teamwork_graphics/graphics_audit_dark.png`) are dynamically created/recreated by `tools/verify_graphics.py` by decoding the 2bpp bytes from `src/tiles.c` and upscaling them using nearest-neighbor scaling.
    *   Unit tests explicitly delete pre-existing audit sheets before running and assert that they are cleanly regenerated.

#### Phase 2: Behavioral Verification
4.  **Build and Run**: **PASS**
    *   Executing `make test` successfully compiles the mock HAL testing library and executes 176 unit/integration tests with 0 unexpected failures (`OK (expected failures=3)`).
    *   Executing `make clean && make test_emu` successfully compiles both ROM targets (`bin/dandy.gb` and `bin/dandy_dark.gb`) and executes the PyBoy automated E2E tests for both targets, confirming valid GameBoy ROMs with correct state initialization and player physics.
5.  **Output Verification**: **PASS**
    *   The generated visual audit sheets perfectly represent the decoded tiles under both Light and Dark backgrounds, with correct transparency handling (using checkerboard backgrounds for sprites).
6.  **Dependency Audit**: **PASS**
    *   Standard library usage only; PyBoy and Pillow are used strictly for E2E emulator testing and image generation, which are auxiliary tools. All core compilers, downscalers, and GameBoy engine code are written entirely from scratch.

---

### Adversarial Review & Findings

While the codebase is 100% clean of integrity violations, our adversarial stress-testing surfaced one significant build-system vulnerability:

#### [Medium] Makefile Concurrency Race Condition under Parallel Builds
*   **Vulnerability**: The object files compilation rule does not have a dependency on the directory creation target (`setup`).
    ```makefile
    $(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
    	$(LCC) -Wf--opt-code-size $(CFLAGS_MODE) -c -o $@ $<
    ```
*   **Attack Scenario**: Running parallel make (e.g., `make -j` or in environments where parallel execution is defaulted) causes the compiler to start compiling `.c` files before the `setup` target's `@mkdir -p $(OBJ_DIR)` has finished executing. If this happens, `obj_dark/` does not exist yet, causing the GBDK compiler to fail with:
    `Failed to open output file 'obj_dark/dandy_core.asm' (No such file or directory)`
*   **Blast Radius**: Build failures on clean checkouts when compiled with parallel make flags.
*   **Mitigation**: Add an order-only dependency on the `setup` target for all object files, ensuring the directories are guaranteed to exist before any compilation begins:
    ```makefile
    $(OBJS): | setup
    ```

---

### Evidence

#### 1. Unit & Integration Test Run Output
```
Ran 176 tests in 6.814s

OK (expected failures=3)
```

#### 2. Emulator E2E Verification Output
```
Running PyBoy automated emulator E2E tests: Classic DMG...
[Emulator Test] Initial State: Level=0, P1_Joined=1, Health=100, Pos=(33, 16)
[Emulator Test] Player adjacent tiles: UP=0, DOWN=3, LEFT=0, RIGHT=0
[Emulator Test] Simulating movement: 'right' from (33, 16) to (34, 16)
[Emulator Test] Moved State: Pos=(34, 16)
Ran 2 tests in 0.163s
OK

Running PyBoy automated emulator E2E tests: Atmospheric Dark...
[Emulator Test] Initial State: Level=0, P1_Joined=1, Health=100, Pos=(33, 16)
[Emulator Test] Player adjacent tiles: UP=0, DOWN=3, LEFT=0, RIGHT=0
[Emulator Test] Simulating movement: 'right' from (33, 16) to (34, 16)
[Emulator Test] Moved State: Pos=(34, 16)
Ran 2 tests in 0.190s
OK
```
