# Verification & Stress-Test Handoff Report (Milestone 1)

## 1. Observation

We empirically verified and stress-tested the graphics extraction and verification tools in `dandy-gb/tools/`. Below are the direct observations, commands, and results:

### A. Adversarial Test Suite Execution
We ran the existing adversarial tests and confirmed that all 25 tests pass successfully. Running the test suite directly as a script yields:

```
dandy-gb/.venv/bin/python dandy-gb/tests/test_graphics_adversarial.py
...
Ran 25 tests in 0.244s

OK
```

### B. Discovery of Vulnerabilities via Stress-Testing
By designing additional adversarial inputs, we discovered three distinct bugs/vulnerabilities in the comment-stripping and validation logic. We added these as new tests to the test suite, decorated with `@unittest.expectedFailure` to preserve passing status while permanently documenting them:

1. **JS Division/Regex Ambiguity (`test_js_extraction_division_ambiguity`)**:
   Input JS:
   ```javascript
   const x = 1 / 2; // strike.src = "data:image/png;base64,BAD";
   strike.src = "data:image/png;base64,GOOD";
   ```
   *Expected Behavior*: Extract the active assignment `"GOOD"`.
   *Actual Behavior*: Raises `ValueError: Could not find strike.src assignment with base64 data URL prefix in strike.js`.
   *Intermediate Stripped Content*:
   ```
   const x = 1 / 2; /png;base64,BADdata:image/png;base64,GOOD";
   ```

2. **Swallowed Commas in C (`test_parse_tiles_c_swallowed_comma`)**:
   Input C: An array containing `0x00 0x00` (space-separated, missing comma) instead of `0x00, 0x00`.
   *Expected Behavior*: Raise `ValueError` due to malformed C syntax (missing comma).
   *Actual Behavior*: Silently succeeds and parses all 512 elements as valid, leniently treating the space-separated elements as separate tokens.

3. **C Comment Backslash line-continuation (`test_parse_tiles_c_comment_backslash_escape`)**:
   Input C:
   ```c
   const unsigned char dandy_tiles[] = {
       0x00, // comment ending in backslash \
       0x00, ...
   };
   ```
   *Expected Behavior*: Standard C parser treats the backslash at the end of a `//` comment as a line continuation, commenting out the next line (so only 511 values should be parsed).
   *Actual Behavior*: The python comment-stripper ignores the backslash line-continuation, parsing the second `0x00` and yielding 512 values.

### C. Updated Test Suite Execution
After appending these 3 expected-failure tests, the test suite output is:

```
dandy-gb/.venv/bin/python dandy-gb/tests/test_graphics_adversarial.py
...
Ran 28 tests in 0.253s

OK (expected failures=3)
```

### D. GBDK Build Verification
We ran the full GBDK compilation clean build:
```
make clean && make
```
*Result*:
```
rm -rf obj bin
rm -f web/*.js web/*.wasm
...
Converting levels from JS to C header...
Compiling pristine BMP sprite assets...
Compiling 32 native 8x8 pixel-art glyphs into GBDK 2bpp format...
/usr/local/google/home/jackpal/Developer/gbdk/bin/lcc -Wf--opt-code-size -c -o obj/main.o src/main.c
...
----------------------------------------
Build successful: bin/dandy.gb
----------------------------------------
```

---

## 2. Logic Chain

### A. JS Division/Regex Ambiguity Bug
1. The regex pattern in `extract_sprites.py` includes a pattern to match JS regex literals: `r'/(?![*/])(?:[^/\\\n]|\\.)+/'`.
2. When parsing `const x = 1 / 2; // strike.src = "data:image/png;base64,BAD";`, the parser encounters the division slash `/`. Because it is not followed by `*` or `/`, it matches it as the start of a regex literal.
3. The regex match scans forward and finds the first slash of the single-line comment `//` as the ending slash of the regex literal. Thus, `/ 2; /` is matched as a regex literal and returned as-is (not stripped).
4. The second slash of `//` is then matched as the start of a *new* regex literal. It matches `/ strike.src = "data:image/` (ending at the slash in `image/png`).
5. Because this matched substring contains the characters `strike.src`, the `replacer` function strips it completely (`return ''`).
6. The next match starts at the quote `"` after `BAD`. The parser matches `";\n    strike.src = "` as a double-quoted string literal. Since this substring also contains `strike.src`, it is also stripped!
7. This completely mangles the JS code, leading to: `const x = 1 / 2; /png;base64,BADdata:image/png;base64,GOOD";`.
8. Consequently, the parser fails to find a valid `strike.src` assignment block, raising a `ValueError`.

### B. Swallowed Commas Leniency
1. `verify_graphics.py` parses the array content by first splitting the content by commas: `array_content.split(',')`.
2. For a segment like `0x00 0x00` (which resulted from a missing comma), `split(',')` produces a single part: `"0x00 0x00"`.
3. The parser then does `part.split()`, which splits by whitespace, producing `['0x00', '0x00']`.
4. These are both appended to the flat token list. Since both tokens are valid hex strings, they pass the validation check.
5. The total token count remains 512, so the length check passes.
6. Thus, a C syntax error (missing comma) is silently and leniently accepted instead of raising a `ValueError`.

### C. C Comment Backslash Escape
1. In C, single-line comments ending in a backslash `\` escape the newline character, causing the next line to be treated as part of the comment.
2. The python comment-stripper in `verify_graphics.py` uses `//[^\n]*` to match single-line comments.
3. This regex stops at the newline character and does not check for a trailing backslash.
4. Consequently, the next line is treated as active code instead of being stripped, violating standard C parsing rules.

---

## 3. Caveats

* **Lenient Parsing**: The swallowed comma and backslash line continuation issues are edge cases that are typically caught by the C compiler during GBDK compilation (`make`). However, they represent gaps between the Python verification tool's model of C and the actual C language specification.
* **No Code Modifications**: As per the "Review-only" constraint, we have documented these findings and added them to the test suite as expected failures, but did not modify the implementation files (`verify_graphics.py` and `extract_sprites.py`).

---

## 4. Conclusion

The graphics verification and extraction tools (`verify_graphics.py` and `extract_sprites.py`) are highly functional and correct for standard inputs. The GBDK build is robust and compiles successfully. However, the Python parsing tools contain three comment-stripping and syntax-validation vulnerabilities under adversarial inputs.

### Actionable Mitigations:
1. **JS Division/Regex Ambiguity**: Avoid using a naive regex to strip comments and regexes. Instead, use a lightweight state machine (lexer) that tracks whether the parser is inside a string, comment, or regex, or use a robust JS parsing library. Alternatively, ensure the regex literal pattern in the comment stripper is more constrained.
2. **Strict Comma Validation**: In `verify_graphics.py`, after splitting by commas, verify that each non-empty segment contains exactly one token. If a segment contains multiple tokens (e.g. `len(part.split()) > 1`), raise a `ValueError` for missing/swallowed commas.
3. **Handle Backslash line-continuation**: Update `strip_c_comments` to check if a single-line comment ends with a backslash (possibly followed by whitespace) and, if so, consume the next line as part of the comment.

---

## 5. Verification Method

To verify the test suite and confirm the 25 passing tests alongside the 3 documented expected failures, run:

```bash
cd /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb
.venv/bin/python tests/test_graphics_adversarial.py
```

*Expected Output*:
```
Ran 28 tests in <duration>s
OK (expected failures=3)
```
