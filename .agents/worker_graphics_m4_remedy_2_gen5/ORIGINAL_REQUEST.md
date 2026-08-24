## 2026-06-21T01:56:16Z

You are the teamwork_preview_worker for Milestone 4 Remediation (Round 2).
Your working directory is: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/worker_graphics_m4_remedy_2_gen5/`
Your task is to implement build system fixes in `dandy-gb/Makefile` to resolve a parallel build race condition and clean up generated workspace files:

1. Fix Parallel Build Race Condition:
   - Modify the `dark` target to depend on the `all` target sequentially. This ensures that when a user or script runs a parallel build like `make -j8 all dark` or `make -j8 dark`, the standard configuration (`all`) is fully built and all shared generated source files (`src/levels.c`, `src/levels.h`, `src/tiles.c`, `src/tiles.h`) are completely generated and written *before* the Atmospheric Dark Mode sub-make starts compiling.
   - Design:
     ```makefile
     # Dedicated target for Atmospheric Dark Mode
     dark: all
     	$(MAKE) USE_BLACK_FLOOR=1 all
     ```

2. Clean Up Workspace Pollution:
   - Update the `clean` target to explicitly delete the three generated PNG files in `teamwork_graphics/` to return the git tree to a pristine state:
     - `teamwork_graphics/downscale_preview.png`
     - `teamwork_graphics/graphics_audit.png`
     - `teamwork_graphics/graphics_audit_dark.png`
   - Design:
     ```makefile
     clean:
     	rm -rf obj obj_dark bin
     	rm -f src/levels.c src/levels.h src/tiles.c src/tiles.h
     	rm -f *.lst *.map *.sym
     	rm -rf tests/mock_gb tests/.temp_envs
     	rm -f libdandy_test.so
     	rm -f teamwork_graphics/downscale_preview.png
     	rm -f teamwork_graphics/graphics_audit.png teamwork_graphics/graphics_audit_dark.png
     	@echo "Clean complete."
     ```

Verification steps you must perform:
- Run `make clean`. Verify that `teamwork_graphics/downscale_preview.png`, `teamwork_graphics/graphics_audit.png`, and `teamwork_graphics/graphics_audit_dark.png` are deleted if they existed.
- Run `make -j8 all dark` to verify that highly concurrent parallel builds of both modes now run to completion with 100% success, without any compiler errors, undefined identifiers, or file truncation issues.
- Run `make test` and `make test_emu` to verify that all 176 unit tests and 4 emulator E2E tests continue to pass perfectly.
- Write a detailed `handoff.md` in your working directory summarizing:
  - The changes made to `Makefile`.
  - The successful output of the concurrent parallel build test (`make -j8 all dark`).
  - The clean target verification.
  - Test results.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Please load the software-engineering skill located at:
`/google/src/files/head/depot/google3/learning/gemini/agents/skills/software_engineering/SKILL.md`
