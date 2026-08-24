# Handoff Report: Graphics Verification Pipeline Stress Test

## 1. Observation

We performed a comprehensive stress test on the graphics verification script and test suite. We observed the following:

- **Target Files**:
  1. `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/verify_graphics.py`
  2. `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tests/test_graphics_pipeline.py`

- **Verbatim Failures & Output**:
  Running our adversarial test suite via `.venv/bin/python -m unittest tests/test_graphics_adversarial.py` resulted in a test failure:
  ```
  ======================================================================
  FAIL: test_parse_tiles_c_invalid_hex_characters (tests.test_graphics_adversarial.TestGraphicsAdversarial.test_parse_tiles_c_invalid_hex_characters)
  Test how the parser behaves with invalid hex characters.
  ----------------------------------------------------------------------
  Traceback (most recent call last):
    File "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tests/test_graphics_adversarial.py", line 139, in test_parse_tiles_c_invalid_hex_characters
      self.fail("Parser silently accepted '0xGG' instead of raising ValueError")
  AssertionError: Parser silently accepted '0xGG' instead of raising ValueError
  ```
  The debug logs confirmed that `0xGG` was parsed as `0`:
  ```
  DEBUG: 0xGG was parsed as: 0
  ```

- **CLI Exception Handing Observation**:
  When running the script with `tiles.c` temporarily renamed, it exited with a non-zero code but printed a raw, unhandled Python traceback:
  ```
  Traceback (most recent call last):
    File "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/verify_graphics.py", line 282, in <module>
      main()
    File "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/verify_graphics.py", line 198, in main
      tiles_bytes = parse_tiles_c(tiles_c_path)
    File "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/verify_graphics.py", line 61, in parse_tiles_c
      with open(tiles_c_path, "r") as f:
           ~~~~^^^^^^^^^^^^^^^^
  FileNotFoundError: [Errno 2] No such file or directory: '/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/tiles.c'
  ```

---

## 2. Logic Chain

1. **Silent Data Corruption**:
   - In `verify_graphics.py`, the function `parse_tiles_c` uses `re.findall(r"0[xX][0-9a-fA-F]+|\d+", array_content)` to match numbers.
   - When given the token `0xGG`, the regex engine parses it using the `\d+` branch. The digit `0` matches `\d+`, and the suffix `xGG` is ignored.
   - The token is parsed as the integer `0`. Since exactly one token is matched for `0xGG`, the total count remains 512.
   - The function returns the byte array successfully with `0` in place of `0xGG`. This bypasses validation and silently corrupts the graphics data.

2. **Ungraceful CLI Failures**:
   - The script lacks a top-level `try...except` block in `main()`.
   - Any missing file (`tiles.c`, `strike_original.png`) or formatting issue throws a raw Python exception which bubbles up, printing an unhandled traceback.

3. **Fragile Test Parser**:
   - In `test_graphics_pipeline.py`, the test `test_independent_tile_decoding` parses the array using a strict regex: `re.findall(r"0x[0-9a-fA-F]{2}", array_content)`.
   - If `tiles.c` uses a decimal (e.g. `0`) or a single-digit hex (e.g. `0x0`), the test's regex fails to match it. The test will fail even though the format is perfectly valid in C and parsed correctly by the tool.

---

## 3. Caveats

- **No Code Modification**: In accordance with the Challenger role guidelines, we did not modify any source code or fix any bugs. We only wrote and executed tests to identify and verify the defects.
- **Verification Environment**: Tests were executed using the Python virtual environment (`.venv`) located in the `dandy-gb` directory on a Linux host.

---

## 4. Conclusion

The graphics verification script (`verify_graphics.py`) is functionally correct for pristine inputs (perfectly decoding standard 2bpp planar graphics), but is **brittle** and **unreliable** under adversarial or malformed inputs:
1. It silently accepts malformed hex data (e.g. `0xGG` becomes `0`), leading to silent graphic corruption in the output.
2. It crashes ungracefully with raw Python tracebacks on missing or invalid files/dimensions.
3. The existing test suite is fragile and could cause false positives if standard C byte formatting changes in `tiles.c`.

---

## 5. Verification Method

To independently verify our findings:
1. Navigate to the `dandy-gb` directory:
   ```bash
   cd /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb
   ```
2. Run the newly added adversarial test suite:
   ```bash
   .venv/bin/python -m unittest tests/test_graphics_adversarial.py
   ```
3. Observe that the test suite fails on `test_parse_tiles_c_invalid_hex_characters` due to the parser silently accepting `0xGG` as `0`, and successfully demonstrates the ungraceful traceback crash in `test_cli_graceful_failure_missing_file`.
