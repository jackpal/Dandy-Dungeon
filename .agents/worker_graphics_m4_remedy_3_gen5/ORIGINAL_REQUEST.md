## 2026-06-21T02:10:39Z

You are the teamwork_preview_worker for Milestone 4 Remediation (Round 3).
Your working directory is: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/worker_graphics_m4_remedy_3_gen5/`
Your task is to implement advanced build system fixes in `dandy-gb/Makefile` to resolve:
1. Concurrent build race conditions between independent top-level make processes.
2. Clean target integrity violations (deleting git-tracked mock headers).
3. Missing test dependencies causing test crashes on clean checkouts.

Here is the exact design you must implement in `dandy-gb/Makefile`:

1. Concurrent Build Protection (flock):
   - Wrap the python generator script executions in `flock` to serialize concurrent writes to the shared generated files.
   - Use lockfiles `.levels.lock` and `.sprites.lock`.
   - Recipe for levels:
     ```makefile
     src/levels.c src/levels.h: $(TOOLS_DIR)/convert_levels.py ../dandy-js/levels.js
     	@echo "Converting levels from JS to C header..."
     	@flock .levels.lock python3 $(TOOLS_DIR)/convert_levels.py
     ```
   - Recipe for sprites:
     ```makefile
     src/tiles.c src/tiles.h: $(TOOLS_DIR)/downscale_sprites.py teamwork_graphics/strike_original.png | .venv
     	@echo "Compiling downscaled sprite assets using FHDA..."
     	@flock .sprites.lock .venv/bin/python $(TOOLS_DIR)/downscale_sprites.py --input teamwork_graphics/strike_original.png --output-c src/tiles.c --output-h src/tiles.h --output-preview teamwork_graphics/downscale_preview.png
     ```

2. De-couple `dark` from `all` to enable parallel ROM compilation:
   - Remove the `all` dependency from the `dark` target. The sub-make is already fully isolated and safe when run in parallel, thanks to the `flock` locks on shared assets.
   - Design:
     ```makefile
     # Dedicated target for Atmospheric Dark Mode
     dark:
     	$(MAKE) USE_BLACK_FLOOR=1 all
     ```

3. Fix Clean Target (No git-tracked deletion):
   - Remove `rm -rf tests/mock_gb` from the `clean` recipe. We must never delete checked-in mock directories.
   - Keep `rm -rf tests/.temp_envs`.
   - Add the lock files `.levels.lock` and `.sprites.lock` to the files deleted by `clean`.
   - Design:
     ```makefile
     clean:
     	rm -rf obj obj_dark bin
     	rm -f src/levels.c src/levels.h src/tiles.c src/tiles.h
     	rm -f *.lst *.map *.sym
     	rm -rf tests/.temp_envs
     	rm -f libdandy_test.so
     	rm -f teamwork_graphics/downscale_preview.png
     	rm -f teamwork_graphics/graphics_audit.png teamwork_graphics/graphics_audit_dark.png
     	rm -f .levels.lock .sprites.lock
     	@echo "Clean complete."
     ```

4. Fix Test Target Dependencies & Mock Generation:
   - Remove the dynamic echo/write of `tests/mock_gb/gb/gb.h` from `test_lib` (since it is a checked-in file, we should use the checked-in version directly).
   - Add `sprites` to `test_lib`'s dependencies to ensure `src/tiles.c` and `src/tiles.h` are generated before running tests.
   - Design:
     ```makefile
     test_lib: levels sprites
     	gcc -fPIC -shared -O2 -Isrc -Itests/mock_gb -o libdandy_test.so \
     		src/dandy_core.c \
     		src/levels.c \
     		tests/mock_hal.c
     ```

Verification steps you must perform:
- Run `make clean`. Verify that `tests/mock_gb/gb/gb.h` remains intact and is NOT deleted. Verify that the lock files and generated PNG files are deleted.
- Run `make test` immediately after `make clean` and verify it successfully compiles the test library, generates sprites and levels, and passes all 176 unit tests.
- Run `make test_emu` and verify all 4 emulator E2E tests pass.
- Stress-test concurrent builds: run `make clean` and then run `make -j8 all & make -j8 dark; wait` in a loop of 5 iterations. Verify that all 5 iterations succeed with 100% pass rate, with absolutely zero compiler errors or collisions.
- Write a detailed `handoff.md` in your working directory summarizing:
  - The changes made to `Makefile`.
  - The concurrent stress-testing results (with logs/output).
  - The clean target and test dependency verification.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Please load the software-engineering skill located at:
`/google/src/files/head/depot/google3/learning/gemini/agents/skills/software_engineering/SKILL.md`
