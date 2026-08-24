# Adversarial Challenge Report: Milestone 1 Iteration 2 Graphics Tools

## Challenge Summary

**Overall risk assessment**: MEDIUM

While the core functionality (2bpp decoding, upscaling, and basic format support) is correct and robust, the parsing and extraction tools suffer from critical lexical fragility. They easily break or extract incorrect data when faced with common development practices, such as nesting comment tokens, commenting out old code, or writing log messages containing assignment-like strings.

---

## Challenges & Vulnerabilities Found

### [High] Challenge 1: C Comment Stripping Fragility (Nested Comment Bug)
- **Assumption challenged**: Sequential regex-based comment stripping (first block comments, then line comments) is sufficient for parsing.
- **Attack scenario**: A developer comments out a line or writes a single-line comment containing the start of a block comment `/*` (e.g. `// comment with /*`).
- **Blast radius**: Because the parser runs the block comment stripper `re.sub(r"/\*.*?\*/", ...)` first, it matches the `/*` inside the line comment and swallows everything up to the next `*/` (even if it's on a later line or in a different comment block). This strips active array elements, leading to a parser crash with a `ValueError` because the number of values falls below 512.
- **Empirical proof**: Confirmed by our test case `Single-line comment containing /* (nested comment bug)` which failed with:
  `ValueError: Expected exactly 512 values (32 tiles * 16 bytes), but found 410`
- **Mitigation**: Use a single unified regex that matches either a block comment OR a line comment in a single pass (mimicking a lexical analyzer):
  ```python
  content = re.sub(r'/\*.*?\*/|//[^\n]*', '', content, flags=re.DOTALL)
  ```

### [High] Challenge 2: Commented-out Code Matching in JS Extractor
- **Assumption challenged**: The first occurrence of `strike.src` in `strike.js` is always the active, valid assignment.
- **Attack scenario**: A developer comments out an old sprite sheet assignment (e.g. `// strike.src = "data:image/png;base64,..."`) or keeps a block comment with a reference assignment before the actual active assignment.
- **Blast radius**: `re.search` matches the commented-out assignment first, extracting incorrect or incomplete base64 data and causing the sprite extraction tool to fail or extract corrupted images.
- **Empirical proof**: Confirmed by test scenarios `Commented-out strike.src assignment before active one` and `Block commented-out strike.src assignment before active one`, both of which extracted wrong base64 data.
- **Mitigation**: Strip all JS comments from the entire file content *before* running `re.search` to locate the `strike.src` assignment block.

### [High] Challenge 3: String Literal Matching in JS Extractor
- **Assumption challenged**: `strike.src` assignment patterns only appear as active JS statements.
- **Attack scenario**: A string literal containing the text `strike.src = "data:image/png;base64,..."` appears in the file before the active assignment (e.g., inside a log message: `console.log('strike.src = "..."')`).
- **Blast radius**: The extractor matches the string literal, extracting the incorrect dummy base64 data.
- **Empirical proof**: Confirmed by test scenario `strike.src inside a string before active assignment`, which extracted wrong base64 data.
- **Mitigation**: Either parse the JS file using a proper lexer/AST, or strip all string literals/comments from the file before searching, or ensure the match is not preceded by quotes or other string delimiters.

### [Low] Challenge 4: Resource Leak in verify_graphics.py
- **Assumption challenged**: PIL images do not need explicit closing.
- **Attack scenario**: Running the script repeatedly in long-lived sessions.
- **Blast radius**: File handles remain open until garbage collection occurs.
- **Mitigation**: Use a context manager for opening `original_sheet` in `verify_graphics.py`:
  ```python
  with Image.open(strike_png_path) as original_sheet:
      # ... crop and process ...
  ```

---

## Stress Test Results

| Test Scenario / Case | Target Component | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|---|
| `test_gb_tile_decoding_math` | `decode_gb_tile` | Decode 2bpp bytes to correct RGB/RGBA colors | Decoded pixels match expected palettes perfectly | **PASS** |
| C comments: Standard single/multi-line | `parse_tiles_c` | Comments stripped without affecting data | Bytes parsed successfully, matched original | **PASS** |
| C comments: Quotes and symbols | `parse_tiles_c` | Comments containing quotes stripped cleanly | Bytes parsed successfully, matched original | **PASS** |
| C comments: Single-line containing `/*` | `parse_tiles_c` | Strip single-line comment without swallowing code | Swallowed active hex values, found only 410/512 | **FAIL** |
| C comments: Closing brace `}` inside comment | `parse_tiles_c` | Stripped before regex matching, no crash | Bytes parsed successfully, matched original | **PASS** |
| JS extraction: Unrelated strings/comments | `extract_base64_from_js` | Extractor ignores unrelated code/comments | Extracted base64 successfully, matched original | **PASS** |
| JS extraction: Comments inside assignment | `extract_base64_from_js` | Extractor strips comments inside block | Extracted base64 successfully, matched original | **PASS** |
| JS extraction: Commented line before active | `extract_base64_from_js` | Extractor ignores commented-out assignment | Matched commented line, extracted wrong base64 | **FAIL** |
| JS extraction: Block comment before active | `extract_base64_from_js` | Extractor ignores commented-out assignment | Matched block comment, extracted wrong base64 | **FAIL** |
| JS extraction: Assignment in string literal | `extract_base64_from_js` | Extractor ignores assignment text in string | Matched string literal, extracted wrong base64 | **FAIL** |
| `check_for_resource_leaks` | Both scripts | No unclosed file descriptors | No files left open after execution | **PASS** |

---

## Unchallenged Areas

- **GBDK Build and Rom Integration**: Out of scope for graphics-only verification.
- **Image upscaling quality / anti-aliasing**: Checked visually and programmatically using nearest-neighbor check, verified 100% sharp pixel duplication without blur.

---

## Final Verdict

**VERDICT: REJECT (Requires Fixes)**

While the core GameBoy 2bpp decoding math and visual auditing features are excellent and completely correct, the comment stripping and JS extraction parsers are fragile and will fail or corrupt outputs under standard development scenarios (such as commenting out code, writing log messages, or using nested comment symbols). The worker must implement robust lexical stripping before this milestone can be signed off.
