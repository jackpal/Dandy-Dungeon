# Handoff Report — Milestone 4 Makefile Parallel Build Remediation

## 1. Observation
- **Target File**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/Makefile`
- **Initial Error under Parallel Build (`make clean && make -j8`)**:
  ```
  src/dandy_core.c:2:10: fatal error: levels.h: No such file or directory
      2 | #include "levels.h"
        |          ^~~~~~~~~~
  compilation terminated.
  src/main.c:4:10: fatal error: tiles.h: No such file or directory
      4 | #include "tiles.h"
        |          ^~~~~~~~~
  compilation terminated.
  ```
- **Remediation changes implemented**:
  - Order-only dependency: `$(OBJS): | setup`
  - Generator targets:
    ```makefile
    src/levels.c src/levels.h: levels
    src/tiles.c src/tiles.h: sprites
    ```
  - Object file dependencies:
    ```makefile
    $(OBJ_DIR)/levels.o: src/levels.c src/levels.h
    $(OBJ_DIR)/tiles.o: src/tiles.c src/tiles.h
    $(OBJ_DIR)/main.o: src/tiles.h
    $(OBJ_DIR)/dandy_core.o: src/levels.h
    ```
  - Updated `clean` target to delete generated files:
    ```makefile
    clean:
    	rm -rf obj obj_dark bin
    	rm -f src/levels.c src/levels.h src/tiles.c src/tiles.h
    	rm -f *.lst *.map *.sym
    	rm -rf tests/mock_gb tests/.temp_envs
    	rm -f libdandy_test.so
    	@echo "Clean complete."
    ```
- **Post-Remediation Verification**:
  - `make clean && make -j8` successfully compiles standard ROM `bin/dandy.gb` (32KB).
  - `make dark -j8` successfully compiles Atmospheric Dark Mode ROM `bin/dandy_dark.gb` (32KB).
  - `make test` runs 176 unit/integration tests successfully with output `OK (expected failures=3)`.
  - `make test_emu` runs 2 emulator tests per ROM successfully with output `OK`.

## 2. Logic Chain
1. **Concurrency Scheduling**: Under parallel execution (`make -j8`), make schedules targets concurrently. Because `main.o` and `dandy_core.o` did not have explicit dependencies on the generated headers (`tiles.h` and `levels.h`), make attempted to compile them before the generator targets `sprites` and `levels` finished execution.
2. **Order-Only Dependencies**: Adding `$(OBJS): | setup` guarantees that the directory structure (`obj/`, `obj_dark/`, `bin/`) is fully created before any compiler invocation, preventing directory-creation write races.
3. **Generator Target Mappings**: Declaring `src/levels.c src/levels.h: levels` and `src/tiles.c src/tiles.h: sprites` links the physical generated files to their respective phony targets, establishing the dependency chain for make.
4. **Object File Dependency Mapping**: Adding `$(OBJ_DIR)/main.o: src/tiles.h` and `$(OBJ_DIR)/dandy_core.o: src/levels.h` guarantees that make delays compiling `main.o` until `tiles.h` is fully written, and delays compiling `dandy_core.o` until `levels.h` is fully written.
5. **Clean Target Completeness**: Updating the `clean` target to delete `src/levels.c src/levels.h src/tiles.c src/tiles.h` ensures that every clean build starts from a truly pristine state.

## 3. Caveats
- The external software-engineering skill file path `/google/src/files/head/depot/google3/learning/gemini/agents/skills/software_engineering/SKILL.md` was not found on the system. Baseline teamwork/implementer/qa/specialist instructions and common make concurrency principles were used instead.

## 4. Conclusion
The Makefile parallel build race condition is completely remediated. The build sequence is now fully deterministic and concurrent-safe, ensuring correct target compilation orders without artificial delays or compilation failures. All ROM outputs are valid, and the entire test suite passes.

## 5. Verification Method
1. Run `make clean` in `dandy-gb/`. Verify that all build directories (`obj/`, `obj_dark/`, `bin/`) and generated files (`src/levels.c`, `src/levels.h`, `src/tiles.c`, `src/tiles.h`) are deleted.
2. Run `make -j8`. Verify that compilation does not race and that `bin/dandy.gb` compiles successfully.
3. Run `make dark -j8`. Verify that `bin/dandy_dark.gb` compiles successfully.
4. Run `make test` and confirm all 176 unit tests pass.
5. Run `make test_emu` and confirm all emulator E2E tests pass on both ROMs.
