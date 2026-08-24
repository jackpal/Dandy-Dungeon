# Challenge Report: Graphics Verification Pipeline Stress Test

## Challenge Summary

**Overall risk assessment**: **MEDIUM**

While the graphics verification tool (`verify_graphics.py`) correctly decodes the 2bpp planar Game Boy tile format when given pristine inputs, it suffers from critical robustness defects. Specifically, it is vulnerable to **silent data corruption/validation bypass** when encountering malformed hex data, and it **fails ungracefully** by exposing raw Python tracebacks to the user when encountering missing files or malformed arrays. Furthermore, the existing test suite contains a **fragile parser** that is more restrictive than the tool itself, creating a high risk of false-positive test failures.

---

## Challenges

### [High] Challenge 1: Silent Data Corruption on Malformed Hex Data

- **Assumption challenged**: The parser assumes that using a loose regex token finder (`0[xX][0-9a-fA-F]+|\d+`) is sufficient to extract valid integers, expecting that any syntax errors will either cause a mismatch in the total count of 512 elements or be caught by the C compiler.
- **Attack scenario**: An invalid hex value such as `0xGG` is introduced in `tiles.c`. 
  - The regex matches `0` (via `\d+`) and ignores the trailing `xGG`.
  - The token is parsed as integer `0`.
  - Because exactly one token is matched, the total token count remains exactly 512.
  - The parser silently returns a valid byte array where the malformed tile byte is replaced by `0`.
  - The script generates a comparison audit sheet containing corrupted graphics, but exits with status `0` (success) without warning the developer of the syntax error.
- **Blast radius**: Silent corruption of compiled game assets. A developer could check in corrupted graphics that appear broken in-game, without the verification tool raising any alerts.
- **Mitigation**: 
  - The parser should first split the array content by commas `,`.
  - Each individual token should be stripped of whitespace and comments, and then validated against strict patterns: `^0[xX][0-9a-fA-F]+$` for hex, or `^\d+$` for decimal.
  - If any token fails to match these patterns, the parser must raise a clear, descriptive `ValueError` (e.g., `Malformed token '0xGG' found in tiles.c`).

### [Medium] Challenge 2: Ungraceful CLI Failures (Raw Python Tracebacks)

- **Assumption challenged**: The script assumes that it is acceptable to let standard Python exceptions (`FileNotFoundError`, `ValueError`) bubble up to the console, resulting in raw interpreter tracebacks.
- **Attack scenario**: 
  - If `tiles.c` is missing, the script throws an unhandled `FileNotFoundError` traceback.
  - If the original sprite sheet `strike_original.png` is missing, the script throws an unhandled `FileNotFoundError` traceback.
  - If the original sprite sheet has incorrect dimensions, it throws an unhandled `ValueError` traceback.
  - If the array has the wrong number of elements, it throws an unhandled `ValueError` traceback.
- **Blast radius**: Brittle developer experience and poor CI/CD integration. Raw tracebacks make it hard for developers to quickly understand what went wrong, and can pollute build logs.
- **Mitigation**: 
  - Wrap the core execution block in `main()` with a `try...except` block.
  - Catch known exceptions such as `FileNotFoundError` and `ValueError`.
  - Print a clean, user-friendly error message to `sys.stderr` (e.g., `Error: Original sprite sheet not found at...`) and exit via `sys.exit(1)`.

### [Low] Challenge 3: Fragile Independent Parser in Test Suite

- **Assumption challenged**: The existing test suite in `test_graphics_pipeline.py` (`test_independent_tile_decoding`) assumes that `tiles.c` will always format hex numbers exactly as `0x[0-9a-fA-F]{2}` (lowercase/uppercase two-digit hex).
- **Attack scenario**: A developer or a code generator formats a byte as a decimal (e.g., `0`), a single-digit hex (e.g., `0x0`), or an uppercase prefix (e.g., `0X1F`).
  - This is perfectly valid C code.
  - `verify_graphics.py` parses it correctly.
  - The game builds and runs correctly.
  - However, the test's independent regex parser fails to match these formats, resulting in fewer than 512 matched values, and causing the test suite to fail with a false positive.
- **Blast radius**: Blocked PRs/CLs and developer frustration due to a fragile test suite.
- **Mitigation**: Update the test's independent parser to be as robust as the tool's parser, or ideally, import and reuse the tool's `parse_tiles_c` function to avoid duplicating parsing logic.

---

## Stress Test Results

We implemented a temporary adversarial test suite in `dandy-gb/tests/test_graphics_adversarial.py` to empirically verify these hypotheses. Running this suite yielded the following results:

| Test Case / Scenario | Expected Behavior | Actual Behavior | Verdict |
| --- | --- | --- | --- |
| **Truncated array** (511 elements) | Raise `ValueError` | Raised `ValueError` | **PASS** |
| **Excessive array** (513 elements) | Raise `ValueError` | Raised `ValueError` | **PASS** |
| **Empty array** (`{}`) | Raise `ValueError` | Raised `ValueError` | **PASS** |
| **Missing array** (wrong variable name) | Raise `ValueError` | Raised `ValueError` | **PASS** |
| **Comments & Whitespaces** (mixed comments inside array, tabs, newlines, decimal/hex mix) | Parse exactly 512 bytes correctly | Parsed exactly 512 bytes correctly | **PASS** |
| **Invalid Hex character** (`0xGG` in array) | Raise `ValueError` | Silently parsed as `0` and succeeded | **FAIL** (Confirmed Vulnerability) |
| **Out-of-range value** (`0x123` in array) | Raise `ValueError` | Raised `ValueError` (caught by `bytes()`) | **PASS** |
| **2bpp planar decoder fidelity** (Light, Dark, Sprite palettes) | Exact pixel-for-pixel match | Exact pixel-for-pixel match | **PASS** |
| **Graceful CLI failure on missing file** | Clean error message & exit code `1` (no traceback) | Exited with `1` but printed raw `FileNotFoundError` traceback | **FAIL** (Confirmed Vulnerability) |

### Verbatim Test Execution Output

```
.venv/bin/python -m unittest tests/test_graphics_adversarial.py
..Reading tiles definition from /tmp/tmpc8ihfstp/tiles.c...
.Reading tiles definition from /tmp/tmpmog9rhdn/tiles.c...
.Reading tiles definition from /tmp/tmpre426lst/tiles.c...
.Reading tiles definition from /tmp/tmp3mk0t_5t/tiles.c...
DEBUG: 0xGG was parsed as: 0
FReading tiles definition from /tmp/tmpqertt5mj/tiles.c...
.Reading tiles definition from /tmp/tmps49rqyb5/tiles.c...
.Reading tiles definition from /tmp/tmpzrt216nw/tiles.c...
.
======================================================================
FAIL: test_parse_tiles_c_invalid_hex_characters (tests.test_graphics_adversarial.TestGraphicsAdversarial.test_parse_tiles_c_invalid_hex_characters)
Test how the parser behaves with invalid hex characters.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tests/test_graphics_adversarial.py", line 139, in test_parse_tiles_c_invalid_hex_characters
    self.fail("Parser silently accepted '0xGG' instead of raising ValueError")
AssertionError: Parser silently accepted '0xGG' instead of raising ValueError
...
FAILED (failures=1)
```

---

## Unchallenged Areas

- **PNG Image Compression / Color Space**: We did not challenge PIL's internal png saving/loading mechanisms beyond asserting correctness of image sizes and pixel values.
- **Command Line Flag Combination Matrix**: We verified the main flags (`--dark-floor`, `--output`) but did not exhaustively fuzz combinations of invalid flags, as `argparse` standard library handles that robustly.
