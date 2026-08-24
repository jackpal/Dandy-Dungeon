# Milestone 1 Remediation Report

## Summary of Changes

### 1. Robustness and Graceful Failures in `verify_graphics.py`
- **Scrambled Mappings Fixed**: Corrected the scrambled sprite index mapping in `GB_TO_JS_MAPPING` to match tiles side-by-side correctly:
  - Stairs Down (4: 4)
  - Key (5: 5)
  - Food (6: 6)
  - Money/Gold (7: 7)
- **Robust C99 Token Parser**: Upgraded the tiles definition parser to use a strict token-based approach. The parser:
  - Extracts the array contents using a flexible regex that supports standard C99/C declarations.
  - Robustly strips comments (using block comment stripping first, then splitting by commas, then splitting by whitespace). This avoids swallowing commas placed after single-line comments on the same line.
  - Strictly validates that each token is a valid decimal or hex number in the range 0-255, raising a `ValueError` for any invalid token.
- **Graceful CLI Exit**: Wrapped the main execution in `main()` with a `try...except` block catching `FileNotFoundError` and `ValueError`, printing clean error messages to `sys.stderr` and exiting with code 1 without raw Python tracebacks.
- **Robust JS Sprite Extractor**: Improved `extract_sprites.py` to support JavaScript template literals and regex literals in its comment-stripping logic, preventing commented-out assignments from being matched.

### 2. Leak-Free Test Environment (`dandy_env.py`)
- **Resource Cleanup Management**:
  - Implemented the context manager interface (`__enter__` and `__exit__`) in `DandyEnv` to support clean `with` blocks.
  - Added an explicit `close(self)` method that safely unloads the shared library using `_ctypes.dlclose` and deletes the temporary copy directory.
  - Configured `__del__(self)` to invoke `self.close()` as a fallback.

### 3. Leak-Free Stress Tests (`test_infra_stress.py`)
- Updated `test_lifecycle_and_leak_stability_1000_runs` and other environment instantiation points to use `with DandyEnv() as env:` blocks or explicitly call `env.close()`. This ensures that all temporary directories and library handles are cleaned up immediately, completely resolving the directory leak.

---

## Build and Test Verification

### 1. Build Compilation
Executed a clean build compilation:
```bash
make clean && make
```
**Outcome**: Build compiled successfully with zero warnings and zero errors. Produced `bin/dandy.gb` and `libdandy_test.so`.

### 2. Test Suite Outcomes
Executed the full Python test suite:
```bash
make test
```
**Outcome**: All **144 tests** ran and passed successfully (100% pass rate). This includes the adversarial graphics tests and the lifecycle/leak stability tests.
```
Ran 144 tests in 5.708s

OK
```

### 3. Audit Sheets Regeneration
Regenerated the visual audit sheets:
```bash
.venv/bin/python tools/verify_graphics.py
.venv/bin/python tools/verify_graphics.py --dark-floor
```
**Outcome**: Successfully generated `graphics_audit.png` and `graphics_audit_dark.png` with corrected side-by-side tile comparisons.
