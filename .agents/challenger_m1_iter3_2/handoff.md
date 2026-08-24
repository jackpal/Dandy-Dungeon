# Verification and Stress-Test Report (Milestone 1 Graphics Pipeline)

## 1. Observation
During empirical verification and stress-testing of `verify_graphics.py` and `extract_sprites.py` in `dandy-gb/tools/`, we executed the expanded test suite `tests/test_graphics_adversarial.py` using the project's virtual environment:
```bash
.venv/bin/python3 -m unittest tests/test_graphics_adversarial.py
```
This execution produced the following verbatim failures:

```
FAIL: test_parse_tiles_c_invalid_hex_characters (tests.test_graphics_adversarial.TestGraphicsAdversarial.test_parse_tiles_c_invalid_hex_characters)
Test how the parser behaves with invalid hex characters.
----------------------------------------------------------------------
Traceback (most recent call last):
  ...
AssertionError: Parser silently accepted '0xGG' instead of raising ValueError

======================================================================
FAIL: test_parse_tiles_c_invalid_hex_more_cases (tests.test_graphics_adversarial.TestGraphicsAdversarial.test_parse_tiles_c_invalid_hex_more_cases)
Additional checks for invalid hex characters in verify_graphics.
----------------------------------------------------------------------
Traceback (most recent call last):
  ...
AssertionError: Parser silently accepted '0x12G' instead of raising ValueError
```

We also observed the output for the backslash line continuation test:
```
DEBUG: Backslash continuation extracted: 
```
The extractor returned an empty string instead of extracting the string contents.

## 2. Logic Chain
1. **Silent Hex Parsing Bug in C Parser (`verify_graphics.py`):**
   - **Code Reference**: `verify_graphics.py` (line 76):
     ```python
     num_strings = re.findall(r"0[xX][0-9a-fA-F]+|\d+", array_content)
     ```
   - **Reasoning**: The regex extracts numbers by matching either standard hex patterns or decimal digits. When it processes a malformed hex token like `0xGG`:
     - The hex pattern `0[xX][0-9a-fA-F]+` fails to match because `G` is not a valid hex character.
     - The fallback pattern `\d+` matches the leading `0` in `0xGG`.
     - Consequently, the token `0xGG` is parsed as `0` instead of raising a syntax error.
     - For `0x12G`, the hex pattern matches `0x12` (which is `18`), leaving `G` unmatched and completely ignored.
   - **Conclusion**: The parser silently accepts malformed hex inputs as valid numbers, which can lead to silent graphics corruption in the Game Boy build without raising any validation error.

2. **Newline/Line Continuation Bug in JS Extractor (`extract_sprites.py`):**
   - **Code Reference**: `extract_sprites.py` (line 48):
     ```python
     strings = re.findall(r"([\"\'])(.*?)\1", assignment_block)
     ```
   - **Reasoning**: The `re.findall` call does not pass the `re.DOTALL` flag.
     - In JavaScript, string literals can span multiple lines using backslash line continuation (e.g., `"abc\\\ndef"`).
     - Because `re.DOTALL` is absent, the `.` in `.*?` does not match the literal newline character.
     - The pattern fails to match the string literal entirely, returning an empty list of strings.
   - **Conclusion**: Any multi-line base64 string using backslash line continuation results in silent extraction failure, yielding an empty string which then causes decoding errors or corrupt sprite sheet creation.

## 3. Caveats
- **Automatic Semicolon Insertion (ASI)**: We verified that if a developer omits the semicolon at the end of `strike.src` in `strike.js`, the regex will fail to match the block entirely, raising a `ValueError`. This is a known format constraint that requires the semicolon to be present.
- **Valid C/JS Syntax Assumption**: We assume the files under test are syntactically valid C and JS (i.e., they compile or run). The comment-stripping logic behaves correctly for all standard valid C and JS comment structures, including nested block/line comments and trailing comments.

## 4. Conclusion
While the comment-stripping logic itself is robust against complex comment layouts, the core parsing and extraction regexes contain two critical vulnerabilities:
1. **High Risk**: Silent acceptance of corrupted hex values in `verify_graphics.py`.
2. **Medium Risk**: Silent failure to extract base64 strings containing line-continuation newlines in `extract_sprites.py`.

Despite these tool-level bugs, the actual Game Boy compiled assets are correct: the pristine assets compile successfully, and the GBDK build (`make clean && make`) completes with exit code `0`, generating a correct binary `bin/dandy.gb`.

## 5. Verification Method
To independently reproduce these findings and verify the stress tests:
1. Navigate to the Game Boy directory:
   ```bash
   cd /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb
   ```
2. Execute the adversarial test suite using the local virtual environment:
   ```bash
   .venv/bin/python3 -m unittest tests/test_graphics_adversarial.py
   ```
3. Observe that the two tests `test_parse_tiles_c_invalid_hex_characters` and `test_parse_tiles_c_invalid_hex_more_cases` fail, illustrating the silent parsing vulnerabilities.

---

# Adversarial Review / Challenge Report

## Challenge Summary
- **Overall risk assessment**: **HIGH** (due to silent corruption of asset verification and extraction tools)

## Challenges

### [High] Challenge 1: Silent Hex Parsing Vulnerability
- **Assumption challenged**: The C parser correctly validates that all parsed tokens in `dandy_tiles` are valid hex/decimal bytes.
- **Attack scenario**: A developer typo or automated tool corruption changes a tile byte from `0x1A` to `0x1G` or `0xGG`. The parser silently interprets `0x1G` as `1` and `0xGG` as `0`, successfully generating the audit sheet and claiming the graphics are correct, while they are actually visually corrupted.
- **Blast radius**: Visual mismatches go completely undetected by programmatic verification, defeating the purpose of `verify_graphics.py`.
- **Mitigation**: Before extracting digits, validate each token in the array content against a strict regex (e.g., matching only valid hex `0[xX][0-9a-fA-F]+` or decimal `\d+` separated by commas/comments/whitespace). Any token not matching should raise a `ValueError`.

### [Medium] Challenge 2: Line-Continuation Extraction Failure
- **Assumption challenged**: The JS base64 extractor matches any valid JS string literal layout.
- **Attack scenario**: A code formatter or developer formats the base64 string in `strike.js` with backslash line continuations to keep line lengths under a limit. The extractor silently returns an empty string, causing the build/extract tool to fail or generate a 0-byte sprite sheet.
- **Blast radius**: The graphics extraction pipeline breaks completely on standard JS formatted source code.
- **Mitigation**: Add `re.DOTALL` to `re.findall(r"([\"\'])(.*?)\1", assignment_block, re.DOTALL)` to allow matching across newlines.

## Stress Test Results
- **C comment-stripping with nested blocks** → Strip comments successfully and parse array → **PASS**
- **C array with trailing commas and empty lines** → Parse array successfully → **PASS**
- **C array containing `0xGG`** → Raise ValueError → **FAIL** (silently parsed as `0`)
- **C array containing `0x12G`** → Raise ValueError → **FAIL** (silently parsed as `18`)
- **JS comment-stripping with nested/commented-out comments** → Strip comments and extract base64 → **PASS**
- **JS string concatenation with interspersed comments** → Extract base64 successfully → **PASS**
- **JS assignment without semicolon (ASI)** → Raise ValueError → **PASS** (fails to parse as expected)
- **JS assignment with backslash line continuation** → Extract base64 successfully → **FAIL** (returns empty string)

## Unchallenged Areas
- **Pillow Image Decoding / Upscaling** — Not challenged as Pillow is a standard, robust library and we verified the decoded pixels match the exact expected palette colors under both DMG and Atmospheric palettes.
