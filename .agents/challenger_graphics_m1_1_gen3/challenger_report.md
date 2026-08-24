# Adversarial Challenge Report: Graphics Verification Script & Test Suite

**Overall Risk Assessment**: **CRITICAL**

The graphics verification tool `verify_graphics.py` is highly fragile and contains multiple **critical vulnerabilities**, including **silent data corruption**, **unhandled exceptions/crashes**, and **extreme fragility to standard C syntax variations**. The existing test suite `test_graphics_pipeline.py` is inadequate because it only tests the happy path and does not verify any error handling, bounds checking, or syntax robustness.

---

## 1. Executive Summary of Vulnerabilities

We ran a comprehensive adversarial stress test suite (`adversarial_harness.py`) against `verify_graphics.py` and uncovered the following critical issues:

| Vulnerability Type | Description | Severity | Impact |
| :--- | :--- | :--- | :--- |
| **Silent Data Corruption (Invalid Hex)** | Invalid hex characters (e.g., `0xGG`) are silently parsed as `0` instead of triggering a validation error. | **HIGH** | The tool generates incorrect audit sheets without warning the developer, masking export errors. |
| **Silent Data Corruption (Negative Values)** | Negative values (e.g., `-1`) are silently parsed as positive integers (`1`) because the minus sign is stripped. | **HIGH** | Silently corrupts the graphics data during verification. |
| **Fragility to C Declarations** | Standard C array declaration variants (e.g., `uint8_t`, `unsigned char` without `const`) cause the parser to fail. | **HIGH** | Any minor style change in `tiles.c` breaks the entire verification pipeline. |
| **Raw Python Tracebacks (No Graceful Exit)** | Almost all validation errors (truncated array, oversized array, out-of-bounds numbers, missing files) throw raw Python tracebacks. | **MEDIUM** | Poor user experience, lacks professional CLI robustness. |

---

## 2. Detailed Challenges & Findings

### [Critical/High] Challenge 1: Silent Parsing of Invalid Hex Data (Silent Corruption)
- **Assumption Challenged**: The regex parser and value converter correctly validate hex format.
- **Attack Scenario**: A compiler or exporter bug outputs an invalid hex sequence (e.g., `0xGG`) in `tiles.c`.
- **Failure Mode**: The parser regex `0[xX][0-9a-fA-F]+|\d+` fails to match `0xGG` as hex, but its fallback `\d+` matches the leading `0`. The remaining `GG` is ignored. The value is recorded as `0`, the total array size remains 512, and the tool exits with `0` (success).
- **Blast Radius**: Extremely high. Silent corruption of tile bytes goes completely unnoticed by the developer.
- **Mitigation**: Use a more precise parser. Instead of using a loose regex to find values, split the array content by commas, strip whitespaces/comments, and strictly validate that each token is a valid hex (matching `^0[xX][0-9a-fA-F]+$`) or a valid decimal (`^\d+$`) within the range 0–255.

### [Critical/High] Challenge 2: Silent Parsing of Negative Numbers (Silent Corruption)
- **Assumption Challenged**: Out-of-bounds or negative values in the C array are rejected.
- **Attack Scenario**: A negative value like `-1` is present in the `tiles.c` array.
- **Failure Mode**: The regex matches `1` and ignores the `-` sign. The value is silently treated as `1`, and the tool succeeds.
- **Blast Radius**: High. Invalid data is silently accepted as valid, leading to incorrect visual representation on Game Boy or mismatch with original sprites.
- **Mitigation**: Enforce strict token validation (no negative signs allowed, or reject any token containing `-`).

### [Critical/High] Challenge 3: Parsing Fragility to Standard C Declarations
- **Assumption Challenged**: The GBDK tiles will always be defined with the exact signature `const unsigned char dandy_tiles[]`.
- **Attack Scenario**: A developer changes the signature to use `uint8_t` (standard C99), `static const`, or omits `const` (e.g. `unsigned char dandy_tiles[]`).
- **Failure Mode**: The hardcoded regex `const\s+unsigned\s+char\s+dandy_tiles` fails to match. The tool crashes with `ValueError: Could not find 'dandy_tiles' array in tiles.c`.
- **Blast Radius**: High. Completely breaks the verification pipeline for standard, valid C refactorings.
- **Mitigation**: Make the regex flexible enough to support optional modifiers like `static`, type aliases like `uint8_t`, and variable spacing:
  `r"(?:static\s+)?(?:const\s+)?(?:unsigned\s+char|uint8_t)\s+dandy_tiles\s*(?:\[[^\]]*\])?\s*=\s*\{([^}]+)\}"`

### [Medium] Challenge 4: Raw Unhandled Python Tracebacks
- **Assumption Challenged**: The script fails gracefully with helpful exit codes and clean error messages.
- **Attack Scenario**: The script is run with:
  - An empty `tiles.c` file.
  - A truncated/oversized tile array (e.g. 511 or 513 bytes).
  - Out-of-bounds values (e.g. `256` or `0x100`).
  - Missing `strike_original.png` sheet.
- **Failure Mode**: The script crashes and prints raw Python tracebacks (e.g., `ValueError: bytes must be in range(0, 256)`, `ValueError: Expected exactly 512 values`, `FileNotFoundError`).
- **Blast Radius**: Medium. Unprofessional CLI behavior; complicates automation and integration in CI/CD pipelines.
- **Mitigation**: Wrap the main logic of `verify_graphics.py` in a `try...except` block within `main()`. Catch specific exceptions, print clean, user-friendly error messages to `sys.stderr`, and exit with code `1`.

---

## 3. Empirical Stress Test Results

The temporary adversarial harness `adversarial_harness.py` was executed using the project's virtual environment python. Out of 13 stress-test scenarios, **9 failed** (meaning they either crashed with a raw traceback or silently succeeded when they should have failed):

| Test Case | Scenario Description | Expected Behavior | Actual Behavior | Result |
| :--- | :--- | :--- | :--- | :--- |
| `test_01` | Valid baseline `tiles.c` | Exit code 0, success | Exit code 0, success | **PASS** |
| `test_02` | Empty `tiles.c` | Exit code 1, clean error | Crash (Unhandled `ValueError: Could not find...`) | **FAIL** |
| `test_03` | Truncated array (3 bytes) | Exit code 1, clean error | Crash (Unhandled `ValueError: Expected 512...`) | **FAIL** |
| `test_04` | Oversized array (513 bytes) | Exit code 1, clean error | Crash (Unhandled `ValueError: Expected 512...`) | **FAIL** |
| `test_05` | Valid comments interspersed | Exit code 0, success | Exit code 0, success | **PASS** |
| `test_06` | Comment with `}` inside array | Exit code 0, success | Exit code 0, success | **PASS** |
| `test_07` | Invalid hex characters (`0xGG`) | Exit code 1, clean error | **Silent Success (Exit code 0, parsed as 0)** | **FAIL** |
| `test_08` | Out-of-range decimal (`256`) | Exit code 1, clean error | Crash (Unhandled `ValueError: bytes must be...`) | **FAIL** |
| `test_09` | Out-of-range hex (`0x100`) | Exit code 1, clean error | Crash (Unhandled `ValueError: bytes must be...`) | **FAIL** |
| `test_10` | Negative value (`-1`) | Exit code 1, clean error | **Silent Success (Exit code 0, parsed as 1)** | **FAIL** |
| `test_11` | Missing `strike_original.png` | Exit code 1, clean error | Crash (Unhandled `FileNotFoundError`) | **FAIL** |
| `test_12` | Invalid CLI arguments | Exit code 2, clean error | Exit code 2, standard argparse error | **PASS** |
| `test_13` | Alternative C declarations | Exit code 0, success | Crash (Unhandled `ValueError` for uint8_t/unsigned char) | **FAIL** |

---

## 4. 2bpp Planar Decoder Verification
We carefully inspected the 2bpp planar decoder logic in `verify_graphics.py` (`decode_gb_tile` function):
- It correctly reads two bytes per 8-pixel row (low byte and high byte).
- It extracts the bits for each pixel from MSB to LSB (`7 - x`).
- It correctly combines the high bit and low bit using `(high_bit << 1) | low_bit` to obtain the 2-bit color index.
- It maps the index to the respective palette (DMG Classic, Atmospheric, or transparent sprite).

This logic is mathematically and programmatically **100% correct** and conforms exactly to the Game Boy hardware specifications.

---

## 5. Recommendations for Remediation

1. **Implement Robust Main Exception Handling**:
   Modify `main()` in `verify_graphics.py` to wrap the execution in a `try...except` block:
   ```python
   def main(argv=None):
       try:
           # ... existing logic ...
       except FileNotFoundError as e:
           print(f"Error: {e}", file=sys.stderr)
           sys.exit(1)
       except ValueError as e:
           print(f"Validation Error: {e}", file=sys.stderr)
           sys.exit(1)
       except Exception as e:
           print(f"Unexpected Error: {e}", file=sys.stderr)
           sys.exit(1)
   ```

2. **Refactor C Array Parsing to be Safe and Strict**:
   Replace the loose regex findall with a robust parser that:
   - Finds the array contents using a flexible declaration regex.
   - Strips comments and splits by commas.
   - Strictly validates every token to be a valid 8-bit integer (decimal or hex).
   - Rejects negative signs or invalid character suffixes.

3. **Incorporate Adversarial Test Cases into the Test Suite**:
   The existing `test_graphics_pipeline.py` should be expanded to include validation test cases (e.g., testing that invalid files, missing assets, or bad hex data are correctly rejected with proper error messages and exit codes), using a test harness similar to the one we built.
