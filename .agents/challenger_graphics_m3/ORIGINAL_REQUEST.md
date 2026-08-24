## 2026-06-21T01:11:01Z

Stress-test and empirically verify the correctness of the Milestone 3 Comparative Selection and Packing pipeline.
The worker's code is in:
- `dandy-gb/downscale/overrides.py`
- `dandy-gb/downscale/selector.py`
- `dandy-gb/tools/downscale_sprites.py`
- `dandy-gb/tests/test_graphics_selector.py`

Your tasks:
1. Execute the entire test suite `./.venv/bin/python -m unittest discover -s tests` and verify that all tests pass.
2. Write an independent stress test or extend the existing stress test harness (like `tools/stress_test_downscaler.py` or a new script) to test the robustness of the `TileSelector` and `overrides.py`:
   - Test edge cases like invalid tile indices (negative or >31) in `get_override_tile` or `select_tile`.
   - Test what happens if the `TILE_SELECTION` configuration contains invalid sources or is missing keys.
   - Test performance: measure the time and memory overhead of performing selection and overrides over 1000 iterations to ensure there are no memory/resource leaks or performance degradations.
   - Verify that the `--no-overrides` CLI flag works perfectly under all conditions and forces all tiles to be mathematically downscaled.
3. Run your stress tests and verify the results.

Provide a detailed stress-test report and a clear PASS/FAIL verdict in your handoff.
