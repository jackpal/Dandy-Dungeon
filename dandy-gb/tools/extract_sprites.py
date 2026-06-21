import os
import re
import base64
from PIL import Image

def extract_base64_from_js(content):
    # Strip all comments from the JS content before running the extractor
    # Pattern matching:
    # 1. Double quoted string literals: "(?:[^"\\]|\\.)*"
    # 2. Single quoted string literals: '(?:[^'\\]|\\.)*'
    # 3. Backtick template literals: `(?:[^`\\]|\\.)*`
    # 4. Regex literals: /(?![*/])(?:[^/\\\n]|\\.)+/
    # 5. Block comments: /*...*/
    # 6. Single-line comments: //[^\n]*
    comment_pattern = re.compile(
        r'('
        r'"(?:[^"\\]|\\.)*"'
        r'|\'(?:[^\'\\]|\\.)*\''
        r'|`(?:[^`\\]|\\.)*`'
        r'|/(?![*/])(?:[^/\\\n]|\\.)+/'
        r'|/\*.*?\*/'
        r'|//[^\n]*'
        r')',
        re.DOTALL
    )
    def replacer(m):
        s = m.group(0)
        if s.startswith('/*') or s.startswith('//'):
            return ''  # Strip comments
        if 'strike.src' in s:
            return ''  # Strip mock/commented-out assignments inside string/template literals
        return s
    content = comment_pattern.sub(replacer, content)

    # Match the assignment to strike.src.
    # It must start with strike.src = followed by the data URL prefix and either:
    # A. A single string literal (single, double, or backtick quoted)
    # B. A concatenated list of string literals
    # We find the assignment block up to the ending semicolon.
    match = re.search(r"strike\.src\s*=\s*([\"\'`])data:image/png;base64,(.*?)\1\s*(?:\+\s*(.+?))?;", content, re.DOTALL)
    if not match:
        # Check if first part is empty base64 prefix, e.g., strike.src = "data:image/png;base64," + "part1" + ...
        match = re.search(r"strike\.src\s*=\s*([\"\'`])data:image/png;base64,\1\s*\+\s*(.+?);", content, re.DOTALL)
        if not match:
            raise ValueError("Could not find strike.src assignment with base64 data URL prefix in strike.js")
        assignment_block = match.group(2)
    else:
        g2 = match.group(2)
        g3 = match.group(3)
        if g3 is None:
            # Single string!
            assignment_block = f'"{g2}"'
        else:
            # Concatenated, first part has some base64
            assignment_block = f'"{g2}" + ' + g3

    # Strip any comments safely from the assignment block
    assignment_block = comment_pattern.sub(replacer, assignment_block)

    # Now find all string literals (single, double quoted, or backtick)
    strings = re.findall(r"([\"\'`])(.*?)\1", assignment_block, re.DOTALL)
    raw_base64 = "".join(s[1] for s in strings)
    # Remove backslash line continuations (backslash followed by newline)
    clean_base64 = re.sub(r'\\\r?\n', '', raw_base64)
    return clean_base64

def extract():
    # Paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    js_path = os.path.normpath(os.path.join(current_dir, "../../dandy-js/strike.js"))
    output_dir = os.path.normpath(os.path.join(current_dir, "../teamwork_graphics"))
    output_path = os.path.join(output_dir, "strike_original.png")

    os.makedirs(output_dir, exist_ok=True)

    print(f"Reading sprite sheet from {js_path}...")
    with open(js_path, "r") as f:
        content = f.read()

    base64_str = extract_base64_from_js(content)

    print(f"Decoding base64 string of length {len(base64_str)}...")
    img_data = base64.b64decode(base64_str)

    print(f"Saving to {output_path}...")
    with open(output_path, "wb") as f:
        f.write(img_data)

    # Verify the image is valid and has dimensions exactly 256x32
    try:
        with Image.open(output_path) as img:
            width, height = img.size
            print(f"Verified image size: {width}x{height}")
            if width != 256 or height != 32:
                raise ValueError(f"Expected image dimensions 256x32, but got {width}x{height}")
    except Exception as e:
        raise ValueError(f"Failed to verify image: {e}")

    print("Extraction and verification successful!")

if __name__ == "__main__":
    extract()
