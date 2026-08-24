# plan.md

## Step-by-Step Plan for Milestone 4 Remediation

### 1. Verify Current Behavior & Failure Modes
- Verify that a clean build works but incremental compilation is broken (runs level conversion and sprite compile every time).
- Verify that if `.venv` is missing, the build fails immediately on `sprites` target.
  - To test this, we can temporarily rename `.venv` to `.venv_backup` and run `make`. It should fail on `sprites` target because `.venv/bin/python` is missing.

### 2. Implement the `.venv` Target
- Define the `.venv` target in `dandy-gb/Makefile` to bootstrap the virtual environment using `/usr/local/google/home/jackpal/.local/bin/uv` if `.venv` is not present.
- The recipe should be:
  ```makefile
  .venv:
  	@if [ ! -d ".venv" ]; then \
  		echo "Creating virtual environment..."; \
  		/usr/local/google/home/jackpal/.local/bin/uv venv && \
  		/usr/local/google/home/jackpal/.local/bin/uv pip install --index-url https://pypi.org/simple --python .venv/bin/python numpy pillow pyboy; \
  	fi
  ```

### 3. Restructure Target Dependencies
- Modify `src/levels.c src/levels.h` rule:
  - Remove dependency on the phony `levels` target.
  - Add dependencies on `$(TOOLS_DIR)/convert_levels.py` and `../dandy-js/levels.js`.
  - Place the conversion recipe directly under this rule.
- Modify `src/tiles.c src/tiles.h` rule:
  - Remove dependency on the phony `sprites` target.
  - Add dependencies on `$(TOOLS_DIR)/downscale_sprites.py`, `teamwork_graphics/strike_original.png`, and order-only dependency `| .venv`.
  - Place the downscaling recipe directly under this rule.
- Redefine phony targets:
  - `levels: src/levels.c src/levels.h` (no recipe).
  - `sprites: src/tiles.c src/tiles.h` (no recipe).
- Update `test` and `test_emu` targets to use `| .venv` dependency instead of having duplicate inline checks or running without virtualenv check.

### 4. Verify Correctness & Incremental Compilation
- Restore `.venv` (or delete it to test pristine checkout).
- Run `make clean`.
- Run `make all` and `make dark` to verify clean compilation.
- Run `make` again and verify that `convert_levels.py` and `downscale_sprites.py` are NOT executed. Verify it output "Nothing to be done for 'all'".
- Run `make test` and `make test_emu` to ensure all tests pass.

### 5. Document and Handoff
- Update `BRIEFING.md` and write `handoff.md`.
