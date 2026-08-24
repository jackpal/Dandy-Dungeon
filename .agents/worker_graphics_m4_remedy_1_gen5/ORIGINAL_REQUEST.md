## 2026-06-21T01:43:21Z

You are the teamwork_preview_worker for Milestone 4 Remediation.
Your working directory is: `/usr/local/google/force/jackpal/Developer/Dandy-Dungeon/.agents/worker_graphics_m4_remedy_1_gen5/`
Your task is to fix critical build system defects in `dandy-gb/Makefile`:

1. Pristine Checkout Build Failure (Critical):
   - The `sprites` target currently invokes `.venv/bin/python`, but on a fresh checkout, the `.venv` directory does not exist yet. This causes immediate compilation failure.
   - Design: Define a `.venv` target that bootstraps the virtual environment if it is missing:
     ```makefile
     .venv:
     	@if [ ! -d ".venv" ]; then \
     		echo "Creating virtual environment..."; \
     		/usr/local/google/home/jackpal/.local/bin/uv venv && \
     		/usr/local/google/home/jackpal/.local/bin/uv pip install --index-url https://pypi.org/simple --python .venv/bin/python numpy pillow pyboy; \
     	fi
     ```
   - Make the `sprites` target depend on `.venv` using an order-only dependency `| .venv` to ensure the virtual environment exists but without triggering a rebuild of sprites when the `.venv` directory's timestamp changes.

2. Broken Incremental Compilation (Major):
   - The physical generated files `src/levels.c`, `src/levels.h`, `src/tiles.c`, and `src/tiles.h` were mapped directly to the phony targets `levels` and `sprites`. Since phony targets are always considered out-of-date by GNU Make, running `make` triggers full level conversions and sprite compiles on every single run, even when no files have changed.
   - Design: Map these physical generated files directly to their physical source files instead of phony targets, completely restoring incremental compilation:
     - `src/levels.c src/levels.h` should depend on `$(TOOLS_DIR)/convert_levels.py` and `../dandy-js/levels.js`.
     - `src/tiles.c src/tiles.h` should depend on `$(TOOLS_DIR)/downscale_sprites.py`, `teamwork_graphics/strike_original.png`, and `| .venv`.
   - Clean up any unused phony target mappings or ensure they are correctly decoupled so that physical files don't depend on phony targets.

Verification steps you must perform:
- Run `make clean` (from `dandy-gb/` directory).
- Run `make all` and `make dark` to verify everything compiles cleanly without any errors or warnings.
- Run `make again` (incremental compile) and verify that it does NOT re-run `convert_levels.py` or `downscale_sprites.py`. It should say "Nothing to be done for 'all'" (or equivalent).
- Run `make test` and `make test_emu` to ensure that all unit tests and emulator E2E tests pass.
- Write a detailed `handoff.md` in your working directory `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/worker_graphics_m4_remedy_1_gen5/` summarizing:
  - The changes made to `Makefile`.
  - The output of the incremental compilation check.
  - The test execution results (number of tests passed).
  - Verify that the output files align with the code layout in `PROJECT.md` (which is at `.agents/orchestrator_graphics/plan.md`).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Please load the software-engineering skill located at:
`/google/src/files/head/depot/google3/learning/gemini/agents/skills/software_engineering/SKILL.md`
