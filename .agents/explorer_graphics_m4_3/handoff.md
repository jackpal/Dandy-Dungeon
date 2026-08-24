# Handoff Report: Build System & E2E/Unit Verification
**Agent**: teamwork_preview_explorer (M4 Graphics Exploration)
**Status**: Task Complete (Hard Handoff)
**Target Folder**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_graphics_m4_3/`

---

## 1. Observation
I have inspected the following key files in the repository:
1.  **`dandy-gb/Makefile`**:
    *   Currently compiles all C source files into a single `obj/` directory:
        ```makefile
        $(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
        	$(LCC) -Wf--opt-code-size -c -o $@ $<
        ```
    *   Links the ROM directly as `bin/dandy.gb`:
        ```makefile
        $(BIN_DIR)/$(ROM_NAME): $(OBJS)
        	$(LCC) $(LCCFLAGS) -o $@ $(OBJS)
        ```
2.  **`dandy-gb/src/main.c`**:
    *   Currently has the Atmospheric Dark palette registers hardcoded:
        ```c
        BGP_REG = 0x1B;
        OBP0_REG = 0xE0;
        OBP1_REG = 0xE0;
        ```
3.  **`dandy-gb/tests/test_graphics_pipeline.py`**:
    *   Already contains robust unit tests verifying both modes.
    *   Calls the decoder without dark floor (Light Mode):
        ```python
        pipeline_img = verify_graphics.decode_gb_tile(tile_data, is_sprite=is_sprite)
        ```
    *   Calls the decoder with dark floor (Dark Mode):
        ```python
        pipeline_img = verify_graphics.decode_gb_tile(tile_data, is_sprite=is_sprite, use_dark_floor=True)
        ```
    *   Generates both audit sheets (`graphics_audit.png` and `graphics_audit_dark.png`) and checks nearest-neighbor upscaling.
4.  **`dandy-gb/tests/verify_emulator.py`**:
    *   Currently has hardcoded ROM and map paths:
        ```python
        cls.rom_path = os.path.normpath(os.path.join(cls.current_dir, "../bin/dandy.gb"))
        cls.map_path = os.path.normpath(os.path.join(cls.current_dir, "../bin/dandy.map"))
        ```

---

## 2. Logic Chain
1.  **Build Directory Collision**: If compiler flags are toggled (e.g., `make USE_BLACK_FLOOR=1` vs. `make`), `make` will not recompile existing object files in `obj/` because the source files have not been modified. This causes incorrect linking of stale object files unless a full `make clean` is manually performed.
2.  **Directory Isolation Solution**: Setting the object directory to `obj_dark/` and the ROM name to `dandy_dark.gb` when `USE_BLACK_FLOOR=1` is specified completely eliminates build collisions. Both builds can co-exist, and switching modes does not trigger unnecessary full rebuilds.
3.  **Dynamic Emulator Testing**: Since `verify_emulator.py` is hardcoded to `dandy.gb`, parameterizing the ROM path via an environment variable (`ROM_PATH`) allows running the exact same E2E suite against both `bin/dandy.gb` and `bin/dandy_dark.gb` without duplicating any code.
4.  **Macro-Conditioned Palette**: Macro-conditioning BGP and OBP registers in `src/main.c` via `#ifdef USE_BLACK_FLOOR` allows compile-time switching:
    *   **Classic DMG**: BGP = `0xE4`, OBP0/1 = `0xD8`
    *   **Atmospheric Dark**: BGP = `0x1B`, OBP0/1 = `0xE0`
5.  **Unified Automation**: Automating this via a `test_emu` target in the `Makefile` that compiles both ROMs and runs the E2E suite on both provides a seamless, zero-regression build system.

---

## 3. Caveats
*   **No caveats.** The GBDK compiler frontend and PyBoy testing harness are fully understood. We assume Python 3 and PyBoy are correctly installed on the host environment (the `Makefile` contains a standard virtualenv setup block to handle this automatically).

---

## 4. Conclusion & Recommendations
I recommend implementing the following changes in the implementation phase:

### A. Makefile Changes (`dandy-gb/Makefile`)
1.  **Dynamic Configuration**: Set `ROM_NAME`, `OBJ_DIR`, and `CFLAGS_MODE` dynamically:
    ```makefile
    ifeq ($(USE_BLACK_FLOOR),1)
    ROM_NAME = dandy_dark.gb
    OBJ_DIR = obj_dark
    CFLAGS_MODE = -DUSE_BLACK_FLOOR
    else
    ROM_NAME = dandy.gb
    OBJ_DIR = obj
    CFLAGS_MODE =
    endif
    ```
2.  **Compile Flag Integration**: Add `$(CFLAGS_MODE)` to the C compiler flags and compiling rules.
3.  **Dark Mode Target**: Add a dedicated `dark` target:
    ```makefile
    dark:
    	$(MAKE) USE_BLACK_FLOOR=1 all
    ```
4.  **Updated Clean**: Clean both `obj` and `obj_dark` directories:
    ```makefile
    clean:
    	rm -rf obj obj_dark bin
        ...
    ```
5.  **E2E Test Automation**: Update the `test_emu` target to run the emulator tests on both ROMs:
    ```makefile
    test_emu: all dark
    	...
    	ROM_PATH=bin/dandy.gb .venv/bin/python -m unittest tests/verify_emulator.py
    	ROM_PATH=bin/dandy_dark.gb .venv/bin/python -m unittest tests/verify_emulator.py
    ```

### B. Hardware Palette Changes (`dandy-gb/src/main.c`)
Macro-condition the register configuration:
```c
#ifdef USE_BLACK_FLOOR
    BGP_REG = 0x1B;
    OBP0_REG = 0xE0;
    OBP1_REG = 0xE0;
#else
    BGP_REG = 0xE4;
    OBP0_REG = 0xD8;
    OBP1_REG = 0xD8;
#endif
```

### C. Emulator Test Changes (`dandy-gb/tests/verify_emulator.py`)
Modify lines 11-12 to allow environment variable overrides:
```python
        cls.rom_path = os.environ.get("ROM_PATH", os.path.normpath(os.path.join(cls.current_dir, "../bin/dandy.gb")))
        cls.map_path = os.path.splitext(cls.rom_path)[0] + ".map"
```

---

## 5. Verification Method
The receiving implementer can verify the implementation by running these exact commands:
1.  **Run Pipeline Unit Tests**:
    ```bash
    make test
    ```
    *   *Pass Criteria*: All unit tests pass, and both `teamwork_graphics/graphics_audit.png` and `teamwork_graphics/graphics_audit_dark.png` are generated with high fidelity and no nearest-neighbor blurring.
2.  **Compile Both ROMs**:
    ```bash
    make clean
    make
    make dark
    ```
    *   *Pass Criteria*: Both `bin/dandy.gb` and `bin/dandy_dark.gb` are successfully compiled in their respective isolated object directories.
3.  **Run Emulator E2E Tests on Both**:
    ```bash
    make test_emu
    ```
    *   *Pass Criteria*: PyBoy initializes and runs all movement/initialization tests successfully for both the Classic and Atmospheric Dark ROMs.
