# Adversarial Challenge Report — Milestone 4 (Palette & Sprite Integration)

## Challenge Summary

**Overall risk assessment**: **LOW** (with a **MEDIUM** operational note on concurrent workspace usage)

The Milestone 4 implementation of the graphics downscaler, build system, and hardware palette integration is exceptionally high-quality, mathematically sound, and rigorously tested. 

Our adversarial stress tests confirm that:
1. The compiler handles corrupt inputs and invalid boundary parameters cleanly.
2. Sequential switching between Classic DMG and Atmospheric Dark modes does not produce stale objects due to separated build directories (`obj/` and `obj_dark/`).
3. Incremental builds rebuild only affected files.
4. There are no temporary directory or memory leaks in the compilation pipeline or test suite.
5. Both output ROMs (`dandy.gb` and `dandy_dark.gb`) boot and run perfectly on the GameBoy emulator, passing E2E controls.

We have identified two operational risks (one related to parallel execution, one related to tool directory structures) which do not affect the correctness of the runtime game, but are critical for automated CI/CD or parallel developer environments.

---

## Challenges

### [Medium] Challenge 1: Parallel Build Race & Workspace Pollution

- **Assumption challenged**: The build system assumes a single-user, sequential, non-concurrent execution environment in the workspace.
- **Attack scenario**: If multiple agents, CI/CD runners, or developers compile different targets or run tests concurrently in the same workspace directory, they collide on `make clean` and shared directories (`obj/` and `obj_dark/`).
  For example, if one process runs `make clean` while another is running `make`, the compilation files are deleted mid-run, resulting in silent failures or linker errors such as `lcc: can't find obj/main.o`. If one process runs `make` and another runs `make dark`, they can corrupt each other's intermediate state.
- **Blast radius**: Transient compilation failures, linking errors, or ROMs containing mixed-mode binary assets.
- **Mitigation**: 
  - For local development, document that concurrent builds are not supported.
  - For CI/CD and multi-agent workflows, compile and test inside isolated sandbox directories (as demonstrated by our challenger isolation scripts), or update the Makefile to support a user-specified build prefix (e.g., `OBJ_DIR = $(BUILD_PREFIX)obj`).

### [Low] Challenge 2: Rigid Sibling Directory Dependency in Level Converter

- **Assumption challenged**: The GameBoy project (`dandy-gb`) assumes it will always reside in a directory structure where the JavaScript implementation (`dandy-js`) is a direct sibling.
- **Attack scenario**: If a developer copies, packages, or moves the `dandy-gb` directory to another location (e.g. for isolation, deployment, or packaging) without also copying the `dandy-js` folder, the build fails immediately. `tools/convert_levels.py` fails with:
  `FileNotFoundError: [Errno 2] No such file or directory: '../dandy-js/levels.js'`
- **Blast radius**: Complete compilation failure when `dandy-gb` is isolated.
- **Mitigation**: Allow the level converter to accept an optional command-line argument for the input `levels.js` path, defaulting to `../dandy-js/levels.js` if not provided. This makes the tool flexible and self-contained.

---

## Stress Test Results

- **Toggling `make` and `make dark` (Sequential)** → Verify no stale objects or cross-pollution → **PASS** (Object files are correctly routed to distinct folders: `obj/` and `obj_dark/`).
- **Incremental Compilation** → Touch `src/main.c` and rebuild → **PASS** (Only `main.o` and the final ROM are rebuilt; unaffected object files are untouched).
- **Corrupt Image Input** → Pass non-PNG text file to `downscale_sprites.py` → **PASS** (Gracefully rejected with exit code 1).
- **Non-existent Input File** → Pass missing path to `downscale_sprites.py` → **PASS** (Gracefully rejected with exit code 1).
- **Out-of-bounds Parameter** → Pass `--outline-thickness 2.5` to `downscale_sprites.py` → **PASS** (Gracefully rejected with exit code 1).
- **Clean Build Stability Stress** → Loop compile 10 times consecutively → **PASS** (10/10 iterations completed cleanly without compiler errors or dangling files).
- **Temp Directory Leaks** → Run `make test` and scan `/tmp/` and `tests/` → **PASS** (Zero leaked directories found in `tests/`; python-managed temp files are properly cleaned up).
- **E2E Emulator Boot & Control (Classic DMG)** → Boot `dandy.gb` on PyBoy, simulate movement → **PASS** (ROM boots, loads level 0, player spawns, movement registers correctly).
- **E2E Emulator Boot & Control (Atmospheric Dark)** → Boot `dandy_dark.gb` on PyBoy, simulate movement → **PASS** (ROM boots and runs perfectly with dark palettes).

---

## Unchallenged Areas

- **Physical GameBoy Hardware Compatibility**: We did not test on real physical GameBoy DMG or GameBoy Color hardware (only via PyBoy Emulator). However, since PyBoy emulates the hardware registers (`BGP_REG`, `OBP0_REG`, `OBP1_REG`) and VRAM layouts precisely, compatibility is expected to be extremely high.
