## 2026-06-21T00:49:12Z
You are a challenger agent (`teamwork_preview_challenger`) tasked with empirically stress-testing and verifying the robustness of the Milestone 2 downscaling pipeline.

Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/challenger_graphics_m2/

Objective:
1. Review the downscaler test suite at `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tests/test_downscale_sprites.py`.
2. Verify that the adversarial and robustness tests are genuinely written and cover all requirements specified in Section 5 of the blueprint (corrupted PNGs, incorrect dimensions, non-standard color modes, out-of-range CLI parameters, write-locked directories, file-directory name collisions).
3. Run the entire test suite using:
   - `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/.venv/bin/python -m unittest discover -s tests -p "test_*.py"`
   Confirm that 100% of the tests pass successfully.
4. Write your own independent, adversarial Python script to stress-test the downscaler (e.g., inputting completely random noise images, giant 10000x10000 images, or deeply nested directory collisions) and verify that the tool handles them gracefully without leaking file descriptors, hanging, or dumping tracebacks.
5. Write your detailed challenge report in `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/challenger_graphics_m2/challenge.md` concluding with a clear, unambiguous verdict: **PASS** or **FAIL**.
