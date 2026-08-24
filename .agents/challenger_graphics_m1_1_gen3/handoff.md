# Handoff Report: Milestone 1 Adversarial Challenger 1

This is a **Hard Handoff** (task is complete).

---

## 1. Observation

We created a comprehensive adversarial test harness (`adversarial_harness.py`) and executed it against `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/verify_graphics.py` using the project's Python virtual environment (`dandy-gb/.venv/bin/python`). 

Of the 13 stress-test scenarios, **9 failed**. Specific observations include:

1. **Silent Data Corruption (Invalid Hex)**:
   - Command: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/.venv/bin/python dandy-gb/tools/verify_graphics.py` with one array element replaced with `0xGG` in `tiles.c`.
   - Result: Exited with status code `0` (success). The element `0xGG` was silently parsed as `0` and accepted without warnings.
   
2. **Silent Data Corruption (Negative Values)**:
   - Command: Running `verify_graphics.py` with one array element replaced with `-1` in `tiles.c`.
   - Result: Exited with status code `0` (success). The element `-1` was silently parsed as positive `1` and accepted without warnings.

3. **Fragility to C Array Declarations**:
   - Command: Running `verify_graphics.py` with `const uint8_t dandy_tiles[]` or `unsigned char dandy_tiles[]` inside `tiles.c`.
   - Result: Crashed with:
     ```
     ValueError: Could not find 'dandy_tiles' array in tiles.c
     ```

4. **Unhandled Exceptions / Raw Tracebacks**:
   - Command: Running `verify_graphics.py` with a truncated array (e.g. 3 elements) or out-of-bounds decimal value (e.g. `256`) or missing `strike_original.png`.
   - Result: Crashed and printed raw Python tracebacks:
     - Truncated: `ValueError: Expected exactly 512 values (32 tiles * 16 bytes), but found 3`
     - Out of bounds: `ValueError: bytes must be in range(0, 256)`
     - Missing PNG: `FileNotFoundError: Original sprite sheet not found at...`

---

## 2. Logic Chain

1. **From Observation 1**: The regex `0[xX][0-9a-fA-F]+|\d+` matches the leading `0` of `0xGG` under the `\d+` pattern. This leaves the `GG` unparsed and parses a value of `0` for the byte. Since the total count of parsed numbers remains exactly 512, the array passes size validation, and the tool silently outputs corrupt graphics data.
2. **From Observation 2**: The regex `0[xX][0-9a-fA-F]+|\d+` does not match the minus sign `-`. It matches `1` inside `-1`, so `-1` is parsed as `1`. The array length remains 512, and the negative value is silently accepted.
3. **From Observation 3**: The regex `const\s+unsigned\s+char\s+dandy_tiles` is hardcoded to expect exactly those keywords. Any variation (such as omitting `const` or using standard type alias `uint8_t`) fails to match, raising a ValueError.
4. **From Observation 4**: There is no top-level `try...except` block in `verify_graphics.py`'s `main()` to intercept validation errors or missing file exceptions, resulting in raw tracebacks bubbling up to the user/CI system.

---

## 3. Caveats

- We assumed that `verify_graphics.py` is intended to be used as a robust developer tool and/or integrated into a CI/CD pipeline, where raw tracebacks are undesirable and silent data corruption is highly critical.
- We did not modify the implementation code itself, per our constraints.

---

## 4. Conclusion

The graphics verification script `verify_graphics.py` is highly fragile and vulnerable to **silent data corruption** when encountering malformed hex (`0xGG`) or negative numbers (`-1`). It is also extremely fragile to standard C syntax variations (e.g. `uint8_t` or omitting `const`), and it fails to crash gracefully, instead spitting raw Python tracebacks for common errors (missing files, wrong array size, out-of-bounds bytes).

The 2bpp planar decoder logic itself, however, is mathematically correct and perfectly translates valid GBDK formatted bytes to 8x8 pixels.

---

## 5. Verification Method

To independently verify all findings, run the automated adversarial stress test harness:

```bash
/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/.venv/bin/python \
  /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/challenger_graphics_m1_1_gen3/adversarial_harness.py -v
```

This will run all 13 test cases and output the failures showing the exact tracebacks and silent successes.
