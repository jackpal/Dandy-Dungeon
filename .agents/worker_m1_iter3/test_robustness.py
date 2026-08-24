import os
import sys
import tempfile
import unittest

# Add tools directory to sys.path so we can import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../dandy-gb/tools")))

from extract_sprites import extract_base64_from_js
from verify_graphics import parse_tiles_c

class TestParserRobustness(unittest.TestCase):
    def test_js_commented_out_assignment(self):
        # JS content with a commented-out strike.src assignment preceding the active one
        js_content = """
        // strike.src = "data:image/png;base64,COMMENTED_OUT_BASE64";
        /* strike.src = "data:image/png;base64,BLOCK_COMMENTED_OUT"; */
        const tileWidth = 16;
        const strike = new Image();
        strike.src = "data:image/png;base64," +
        "ACTIVE_BASE64_PART1" +
        "ACTIVE_BASE64_PART2";
        """
        base64_str = extract_base64_from_js(js_content)
        self.assertEqual(base64_str, "ACTIVE_BASE64_PART1ACTIVE_BASE64_PART2")

    def test_c_nested_comment_robustness(self):
        # C content with a single-line comment containing block-comment start characters
        # followed by the dandy_tiles array definition
        # We need to provide 512 values in the array to satisfy the length check of 512.
        values_str = ", ".join(["0x00"] * 512)
        c_content = f"""
        // This is a single-line comment with a nested block comment start /*
        // And another // nested single-line comment
        /* Normal block comment */
        const unsigned char dandy_tiles[] = {{
            {values_str}
        }};
        """
        # Write to a temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as tmp:
            tmp.write(c_content)
            tmp_path = tmp.name

        try:
            tiles_bytes = parse_tiles_c(tmp_path)
            self.assertEqual(len(tiles_bytes), 512)
            self.assertEqual(tiles_bytes, bytes([0] * 512))
        finally:
            os.remove(tmp_path)

if __name__ == "__main__":
    unittest.main()
