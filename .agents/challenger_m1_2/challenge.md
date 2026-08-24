# Challenge Report — Milestone 1 Graphics Extraction and Verification

This report documents the empirical correctness testing, stress-testing, and security/robustness analysis of the graphics verification tool `dandy-gb/tools/verify_graphics.py`.

## Challenge Summary

**Overall risk assessment**: **HIGH**

While the core GBDK 2bpp decoding math and nearest-neighbor upscaling logic are implemented with 100% mathematical correctness, the script's input parsing logic suffers from a **critical vulnerability (Silent Comment-Based Corruption)** and a **medium vulnerability (Fragile Base64 Extraction)**. These flaws allow a broken or incomplete Game Boy tile array to pass verification silently, or cause the verification script to crash due to unrelated comments or code changes.

---

## Challenges

### [Critical] Challenge 1: Silent Comment-Based Corruption in `tiles.c` Parsing

- **Assumption challenged**: The script assumes that any hex-like substring (`0xXX`) located within the curly braces of the `dandy_tiles` array declaration is an active, compiled byte of tile data.
- **Attack scenario**: A developer comments out a tile or a portion of a tile within the array using C-style block comments `/* ... */` or line comments `// ...`, but leaves the hex values inside the comments. For example:
  ```c
  const unsigned char dandy_tiles[] = {
      // ... 31 active tiles (496 bytes) ...
      /* Commented out 32nd tile:
      0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0x00
      */
  };
  ```
- **Blast radius**: 
  1. The Game Boy compiler will compile only 31 tiles (496 bytes) into the ROM because the 32nd tile is commented out.
  2. The verification script `verify_graphics.py` will parse the commented-out hex values, find exactly 512 bytes, and complete with exit code `0`.
  3. The generated `graphics_audit.png` will show the commented-out tile decoded correctly, masking the bug.
  4. In the game, attempting to load 32 tiles will cause an out-of-bounds memory read (reading 16 bytes of garbage/next variable past the end of the array), leading to visual glitches or memory corruption on the Game Boy.
- **Mitigation**: Strip C-style comments from the file content before executing the regex search for the array and hex values:
  ```python
  # Strip block and line comments
  clean_content = re.sub(r'/\*.*?\*/|//.*?\n', '', content, flags=re.DOTALL)
  ```

### [Medium] Challenge 2: Fragile Base64 Extraction in `strike.js`

- **Assumption challenged**: The script assumes that all double-quoted strings in `dandy-js/strike.js` are segments of the base64-encoded sprite sheet.
- **Attack scenario**: A developer adds an unrelated double-quoted string (e.g., a string variable like `const name = "strike";`, or a double-quoted string inside a comment) anywhere in `strike.js`.
- **Blast radius**: The regex `re.findall(r'"([^"]*)"', content)` matches the unrelated string and appends its contents to the base64 string. This corrupts the base64 padding or data, causing the script to crash with `binascii.Error: Incorrect padding` or `PIL.UnidentifiedImageError` and blocking the verification pipeline.
- **Mitigation**: Target the extraction specifically to the assignment of `strike.src`. For example:
  ```python
  # Match only the strings concatenated after strike.src assignment
  src_match = re.search(r'strike\.src\s*=\s*("data:image/png;base64,"(?:\s*\+\s*"[^"]*")*);', content)
  # Then extract and join only the strings within that specific match.
  ```

### [Low] Challenge 3: Resource Leak via Unclosed PIL Image

- **Assumption challenged**: The script assumes that resources like open file handles are automatically cleaned up when the script exits.
- **Attack scenario**: While not a bug in short-lived CLI tools, `ref_img = Image.open(ref_path)` is called without closing the image handle or using a context manager.
- **Blast radius**: On some operating systems or PIL versions, or if this script is integrated into a long-running test runner/daemon, this could lead to file descriptor leaks.
- **Mitigation**: Use a context manager to ensure the image file is closed:
  ```python
  with Image.open(ref_path) as ref_img:
      # Perform image slicing and upscaling here
  ```

---

## Stress Test Results

The script was empirically tested using a custom automated robustness test suite. Below are the results of each scenario:

| Scenario | Description | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|---|
| **1. Missing `strike.js`** | File `strike.js` is deleted or renamed. | Fail with clear error / exit code 1. | Failed with `FileNotFoundError` (exit code 1). | **PASS** |
| **2. Missing `tiles.c`** | File `tiles.c` is deleted or renamed. | Fail with clear error / exit code 1. | Failed with `FileNotFoundError` (exit code 1). | **PASS** |
| **3. Corrupt base64** | Base64 string in `strike.js` is corrupted. | Fail with image decoding error. | Failed with `PIL.UnidentifiedImageError` (exit code 1). | **PASS** |
| **4. Extra double quotes** | Unrelated double-quoted string added to `strike.js`. | Fail with base64/decoding error. | Failed with `binascii.Error: Incorrect padding` (exit code 1). | **PASS** (Fragility confirmed) |
| **5. Comments with hex (extra)** | Comments containing extra hex values added to `tiles.c`. | Fail due to total byte count mismatch (> 512). | Failed with `ValueError: Expected 512 bytes, but found 514 bytes` (exit code 1). | **PASS** |
| **6. Syntax change** | `const` removed from `dandy_tiles` declaration. | Fail due to array match failure. | Failed with `ValueError: Could not find dandy_tiles array in tiles.c` (exit code 1). | **PASS** |
| **7. Incorrect tile count** | Truncate `dandy_tiles` to 16 bytes (1 tile). | Fail due to total byte count mismatch (< 512). | Failed with `ValueError: Expected 512 bytes, but found 16 bytes` (exit code 1). | **PASS** |
| **8. Silent Comment Corruption** | 31 active tiles + 1 commented-out tile (16 bytes of hex in comment) in `tiles.c`. | **Fail** due to only 31 active compiled tiles. | **Passed with exit code 0**; generated audit sheet displaying commented-out tile. | 🔴 **FAIL** (Vulnerability confirmed!) |

---

## Unchallenged Areas

- **Visual layout aesthetics**: The exact background color of the audit sheet and spacing of borders were not challenged, as they do not affect the correctness of the verification.
- **ROM-level compilation checks**: We did not run a full GBDK compile of the resulting ROM, as we simulated the compiler's behavior on the array length directly.

---

## Final Verdict

The graphics verification tool `verify_graphics.py` is **mathematically correct** in its core decoding and scaling algorithms, but **critically fragile** in its file parsing logic. It is vulnerable to silent corruption where commented-out code is mistaken for active asset data, which can lead to undetected ROM bugs. 

**Recommendation**: The tool should be updated to strip comments before parsing `tiles.c` and target the `strike.src` assignment specifically in `strike.js` before it is marked as production-ready.
