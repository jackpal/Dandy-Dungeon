# Adversarial Challenge Report (Milestone 1, Iteration 2)

This report details the empirical stress-testing and adversarial review of the GameBoy graphics extraction (`extract_sprites.py`) and verification (`verify_graphics.py`) tools in Iteration 2.

## Challenge Summary

**Overall risk assessment**: **HIGH**

While the active worker's changes successfully resolved basic comment stripping in `tiles.c` and clean JS base64 extraction under standard formats, our adversarial stress-testing revealed several **critical vulnerabilities** and **parser discrepancies** that can cause silent extraction corruption, incorrect matches, or compilation mismatches.

---

## Adversarial Findings & Challenges

### 1. [Critical] Semicolons inside JS Comments Truncate the Base64 Sprite Sheet Extraction
- **Assumption challenged**: The regex in `extract_sprites.py` assumes that the only semicolon in the `strike.src` assignment block is the terminal semicolon ending the statement.
- **Attack scenario**: A developer adds a comment containing a semicolon (e.g. `// line 1; line 2` or `/* step 1; step 2 */`) inside the `strike.src` assignment block (between the base64 prefix and the end of the assignment).
- **Failure mode**: The extraction regex `re.search(r"strike\.src\s*=\s*([\"\'])data:image/png;base64,(.*?)\1\s*(?:\+\s*(.+?))?;", content, re.DOTALL)` uses a lazy match `.+?` followed by `;`. When a semicolon is encountered in a comment, the regex engine stops matching at that semicolon, truncating the rest of the base64 payload. The extractor then fails to decode the truncated string or returns empty/corrupted bytes (returns `b''`).
- **Blast radius**: The graphics extraction completely fails or outputs a corrupted/empty `strike_original.png`, causing downstream verification and ROM compilation pipeline failures.
- **Mitigation**: Run the lexically-aware comment stripper on the **entire** JS file content *before* executing the regex search, rather than running it only on the extracted assignment block. This removes all comments and their semicolons before matching.

---

### 2. [High] Unrelated commented-out `strike.src` Assignments are Incorrectly Extracted
- **Assumption challenged**: The extraction regex assumes that the first match of `strike.src = "data:image/png;base64,...` in the JS file is the active, valid assignment.
- **Attack scenario**: A developer leaves an older, commented-out version of the `strike.src` assignment in the JS file (e.g. `// strike.src = "data:image/png;base64,OLD_DATA...";` or inside a block comment) before the active assignment.
- **Failure mode**: Because the regex search is run on the raw, un-stripped JS file content, it matches the first occurrence of the assignment pattern, which is the commented-out old data. The tool extracts the old, obsolete asset sheet instead of the new active one.
- **Blast radius**: The verification tool silently extracts and compares against the wrong (older) graphics asset sheet without raising any errors, leading to incorrect visual audit sheets and undetected mismatches.
- **Mitigation**: Perform full-file comment stripping as the very first step in `extract_sprites.py`. This ensures no commented-out code can ever be matched.

---

### 3. [Medium] C Parser Discrepancy via Backslash-Newline Escaped Comments
- **Assumption challenged**: The C comment stripping regex assumes standard line breaks demarcate the end of single-line comments.
- **Attack scenario**: A developer uses a backslash-newline continuation (`\`) at the end of a single-line comment inside the `dandy_tiles[]` array in `tiles.c`. For example:
  ```c
  0x00, // comment continuation \
  0x11, // this line is still part of the comment in C!
  ```
- **Failure mode**: The C compiler (like GCC or LCC) merges the two lines, treating `0x11` as commented out. However, the python regex `re.sub(r"//[^\n]*", "", array_content)` does not handle backslash-newline continuation, so it only strips the first line. The python parser treats `0x11` as active and extracts it.
- **Blast radius**: This creates a silent parser discrepancy: the C compiler compiles an array with fewer bytes (causing compilation warnings, errors, or offset shifts in the ROM), while the python verification tool extracts the full 512 bytes, leading to a false sense of correctness or mismatched visual validation.
- **Mitigation**: Preprocess the `tiles.c` content by replacing all backslash-newline sequences `\\\n` with empty strings before performing comment stripping.

---

### 4. [Low] Resource Leak in `verify_graphics.py` (Unclosed File Handle)
- **Assumption challenged**: Leaving file/image resource management to Python's garbage collector is sufficient.
- **Attack scenario**: The script opens the original sprite sheet image:
  ```python
  original_sheet = Image.open(strike_png_path)
  ```
  but never closes it or uses a context manager.
- **Failure mode**: The file descriptor remains open until the script exits. While minor in a short-lived script, this is a resource leak and a bad practice.
- **Mitigation**: Wrap the image loading in a `with` context manager:
  ```python
  with Image.open(strike_png_path) as original_sheet:
      # Perform cropping and processing here
  ```

---

## Empirical Stress-Test Results

We implemented and ran a comprehensive test suite (`stress_test.py`) that verified these scenarios:

| Test Case | Scenario | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|---|
| `test_pristine_comments` | Standard tile comments | Parse 512 bytes correctly | Parsed 512 bytes correctly | **PASS** |
| `test_single_line_comments_with_hex` | Hex values inside single-line comments | Strip comments, parse 512 active bytes | Parsed 512 active bytes | **PASS** |
| `test_block_comments_with_hex` | Hex values inside block comments | Strip comments, parse 512 active bytes | Parsed 512 active bytes | **PASS** |
| `test_inline_block_comments` | Block comments inline between hex values | Strip comments, parse 512 active bytes | Parsed 512 active bytes | **PASS** |
| `test_backslash_newline_continuation` | Backslash-newline continuation in C comment | Ignore continued line (discrepancy check) | Parsed 512 bytes (ignored C continuation) | **DISCREPANCY DETECTED** |
| `test_unrelated_assignment_before` | Commented-out `strike.src` before active one | Extract the active base64 payload | Extracted the commented-out base64 payload | **FAIL** |
| `test_comment_with_semicolon_inside_assignment` | Semicolon in single-line comment in assignment | Extract full base64 payload | Truncated extraction, returned `b''` | **FAIL** |
| `test_block_comment_with_semicolon_inside_assignment` | Semicolon in block comment in assignment | Extract full base64 payload | Truncated extraction, returned `b''` | **FAIL** |
| `test_unmatched_quote_in_comment` | Unmatched single quote in single-line comment | Extract full base64 payload | Extracted full base64 payload | **PASS** |

---

## Final Verdict

The Iteration 2 improvements are **not yet production-ready**. While they handle basic/well-formatted inputs, they fail under completely realistic developer behaviors, such as:
1. Commenting out old assignments in the JS file.
2. Writing comments that contain semicolons within the multi-line JS assignment.
3. Using backslash-newline line continuation in C tiles array comments.

These issues must be resolved before Milestone 1 can be considered fully complete and robust.
