# Milestone 1 Graphics Verification Challenge Report

## Challenge Summary

**Overall risk assessment**: MEDIUM

While the core 2bpp decoding math and nearest-neighbor upscaling logic are 100% correct and conform to GBDK/Game Boy specifications, the tool's input parsing logic is highly fragile and vulnerable to failure when confronted with minor, valid changes to the source files (`strike.js` and `tiles.c`).

---

## Attack Surface

### Hypotheses Tested
1. **Hypothesis**: The 2bpp decoding math matches GBDK specifications.
   - *Result*: **Verified**. The LSB/MSB bit-shifting and merging logic matches the Game Boy tile format perfectly.
2. **Hypothesis**: Nearest-neighbor upscaling maps pixels correctly without distortion or off-by-one shifts.
   - *Result*: **Verified**. Checked pixel mapping mathematically; PIL's `Image.NEAREST` scales precisely by the specified factors.
3. **Hypothesis**: The JS base64 parser is fragile to additional strings in `strike.js`.
   - *Result*: **Confirmed Vuln**. The parser blindly concatenates all double-quoted strings in the JS file.
4. **Hypothesis**: The C array parser is fragile to valid syntax variations (sized arrays, omitted `unsigned` qualifier, decimal values).
   - *Result*: **Confirmed Vuln**. Sized declarations, missing qualifiers, or decimal notation cause immediate parsing failures.
5. **Hypothesis**: The tool leaks file descriptors during its execution.
   - *Result*: **No Leak**. File descriptors are properly managed via context managers or garbage-collected upon function exit.

### Vulnerabilities Found

#### 1. [High] Fragile Regex-based Base64 Parser in `strike.js`
- **Assumption challenged**: The script assumes that the only double-quoted strings in `strike.js` contain the base64-encoded image data.
- **Attack scenario**: Adding any unrelated double-quoted string (e.g., `const name = "strike";`) before or after the image assignment.
- **Blast radius**: The script concatenates the unrelated string into the base64 stream, producing a corrupted PNG file on disk that causes PIL to throw `UnidentifiedImageError`, crashing the entire tool.
- **Mitigation**: Match the base64 string specifically by parsing only the RHS of `strike.src` assignment, or target the `data:image/png;base64` pattern directly and only extract adjacent concatenated strings.

#### 2. [Medium] Fragile C Array Parser in `tiles.c`
- **Assumption challenged**: The script assumes `tiles.c` uses the exact signature `const unsigned char dandy_tiles[]` and formats all bytes in hex (`0xXX`).
- **Attack scenario**:
  1. Specifying array size: `const unsigned char dandy_tiles[512]`
  2. Omitting `unsigned` qualifier: `const char dandy_tiles[]` or `uint8_t dandy_tiles[]`
  3. Using decimal notation: `119` instead of `0x77`
- **Blast radius**: The parser crashes with `ValueError` (either "Could not find dandy_tiles array" or "Expected 512 bytes, but found X bytes").
- **Mitigation**: Make the regex flexible to qualifiers (`(?:const\s+)?(?:unsigned\s+)?char\s+dandy_tiles\s*\[\s*\d*\s*\]`) and match both hex (`0x[0-9a-fA-F]+`) and decimal (`\b\d+\b`) integers inside the array body.

---

## Stress Test Results

| Test Scenario | Expected Behavior | Actual Behavior | Pass / Fail |
|---|---|---|---|
| **Test 1: Missing `strike.js`** | Graceful fail / FileNotFoundError | Raised `FileNotFoundError` | **PASS** (Expected Fail) |
| **Test 2: Missing `tiles.c`** | Graceful fail / FileNotFoundError | Raised `FileNotFoundError` | **PASS** (Expected Fail) |
| **Test 3: Corrupt base64 in `strike.js`** | Fail during decode / load | Raised base64 decode / PIL error | **PASS** (Expected Fail) |
| **Test 4: Extra quotes in `strike.js`** | Fail due to image corruption | Raised PIL `UnidentifiedImageError` | **PASS** (Detected Fragility) |
| **Test 5a: Decimal values in `tiles.c`** | Flexible parsing OR clear fail | Failed with `ValueError` (found 0 bytes) | **PASS** (Detected Fragility) |
| **Test 5b: Sized array in `tiles.c`** | Flexible parsing OR clear fail | Failed with `ValueError` (array not found) | **PASS** (Detected Fragility) |
| **Test 5c: Missing `unsigned` in `tiles.c`** | Flexible parsing OR clear fail | Failed with `ValueError` (array not found) | **PASS** (Detected Fragility) |
| **Test 5d: Spaces & comments in `tiles.c`** | Parsing succeeds | Successfully parsed all 32 tiles | **PASS** (Robust to comments) |
| **Test 6: Resource leaks** | No leaked file descriptors | 0 file descriptor leaks detected | **PASS** |
| **Test 7: Clean End-to-End run** | Successfully generate audit files | Generated correct 4130x262 audit sheet | **PASS** |

---

## Loaded Skills
*None loaded.* (Executed using standard teamwork collaboration protocol).

---

## Unchallenged Areas
- **Tile Count Scaling**: The tool hardcodes 32 tiles. We did not test how it behaves if the game grows to 64 or 128 tiles (though this is outside the current Milestone 1 scope of 32 sprites). If the game grows, `verify_graphics.py` will fail because of the hardcoded `len(bytes_data) != 512` check.

---

## Final Verdict

The Milestone 1 graphics verification tool is **empirically correct** in its mathematical calculations:
1. The **2bpp decoding math** is perfectly correct and conforms to the GBDK/Game Boy specifications.
2. The **nearest-neighbor upscaling math** is correct and creates pixel-perfect visual representations.
3. The **resource management** is clean, with zero persistent file descriptor leaks.

However, the tool is **highly fragile** and will easily break under normal developer activities like formatting `tiles.c` (e.g. using decimal numbers or sizing the array) or adding metadata strings to `strike.js`. We recommend merging the tool but prioritizing a small PR to make the JS and C regex parsers robust.
