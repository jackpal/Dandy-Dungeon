import os
import sys
import re
import base64
import unittest
import shutil

# Add tools directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
dandy_gb_dir = os.path.normpath(os.path.join(current_dir, "../../dandy-gb"))
sys.path.append(os.path.join(dandy_gb_dir, "tools"))

import verify_graphics
import extract_sprites

class TestCommentStrippingC(unittest.TestCase):
    def setUp(self):
        self.temp_file = os.path.join(current_dir, "temp_tiles.c")

    def tearDown(self):
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)

    def write_tiles_c(self, array_content_inner):
        content = f"""
/* Header comment */
#include "tiles.h"

const unsigned char dandy_tiles[] = {{
{array_content_inner}
}};
"""
        with open(self.temp_file, "w") as f:
            f.write(content)

    def test_pristine_comments(self):
        # Generate 512 bytes of tiles (32 tiles * 16 bytes)
        expected_bytes = bytes(i % 256 for i in range(512))
        hex_strings = [f"0x{b:02X}" for b in expected_bytes]
        
        # Inject standard comments
        inner_content = ""
        for i in range(32):
            inner_content += f"    /* Tile {i} */\n"
            tile_hex = hex_strings[i*16 : (i+1)*16]
            inner_content += "    " + ", ".join(tile_hex[:8]) + ",\n"
            inner_content += "    " + ", ".join(tile_hex[8:]) + ",\n"
        
        self.write_tiles_c(inner_content)
        parsed_bytes = verify_graphics.parse_tiles_c(self.temp_file)
        self.assertEqual(parsed_bytes, expected_bytes)

    def test_single_line_comments_with_hex(self):
        expected_bytes = bytes(i % 256 for i in range(512))
        hex_strings = [f"0x{b:02X}" for b in expected_bytes]
        
        # Inject single-line comments containing hex values
        inner_content = "    // 0xFF, 0xAA, 0x00 commented out hex values\n"
        for i in range(32):
            inner_content += f"    /* Tile {i} */\n"
            tile_hex = hex_strings[i*16 : (i+1)*16]
            inner_content += "    " + ", ".join(tile_hex[:8]) + ", // 0x11 inside comment\n"
            inner_content += "    " + ", ".join(tile_hex[8:]) + ",\n"
        inner_content += "    // Final comment 0x99\n"
        
        self.write_tiles_c(inner_content)
        parsed_bytes = verify_graphics.parse_tiles_c(self.temp_file)
        self.assertEqual(parsed_bytes, expected_bytes)

    def test_block_comments_with_hex(self):
        expected_bytes = bytes(i % 256 for i in range(512))
        hex_strings = [f"0x{b:02X}" for b in expected_bytes]
        
        # Inject block comments containing hex values
        inner_content = "    /* 0xFF, 0xAA, 0x00 commented out */\n"
        for i in range(32):
            tile_hex = hex_strings[i*16 : (i+1)*16]
            inner_content += "    " + ", ".join(tile_hex[:8]) + ", /* 0x12 */\n"
            inner_content += "    " + ", ".join(tile_hex[8:]) + ",\n"
            
        self.write_tiles_c(inner_content)
        parsed_bytes = verify_graphics.parse_tiles_c(self.temp_file)
        self.assertEqual(parsed_bytes, expected_bytes)

    def test_inline_block_comments(self):
        expected_bytes = bytes(i % 256 for i in range(512))
        hex_strings = [f"0x{b:02X}" for b in expected_bytes]
        
        # Inject inline block comments
        inner_content = ""
        for i in range(32):
            tile_hex = hex_strings[i*16 : (i+1)*16]
            # Put comment inside the hex list
            line1 = tile_hex[:4] + ["/* mid-line */"] + tile_hex[4:8]
            inner_content += "    " + ", ".join(line1) + ",\n"
            inner_content += "    " + ", ".join(tile_hex[8:]) + ",\n"
            
        self.write_tiles_c(inner_content)
        parsed_bytes = verify_graphics.parse_tiles_c(self.temp_file)
        self.assertEqual(parsed_bytes, expected_bytes)

    def test_backslash_newline_continuation(self):
        """Adversarial test: backslash-newline continuation in C comments."""
        # In C, a backslash at the end of a single-line comment line continues the comment to the next line.
        # So the next line's content is treated as commented out.
        # But a naive regex parser might not handle this, leading to a discrepancy.
        # Let's see if verify_graphics handles this.
        expected_bytes = bytes(i % 256 for i in range(512))
        hex_strings = [f"0x{b:02X}" for b in expected_bytes]
        
        # If we comment out one active hex byte using backslash-newline:
        # In C, the compilation would fail or the array would have 511 bytes.
        # Here, we inject a backslash-newline comment that comments out a line of active hex bytes.
        # We want to see if the parser correctly ignores it or if it incorrectly parses it.
        # Note: If the parser incorrectly parses it, it will include the commented-out bytes.
        inner_content = ""
        for i in range(32):
            tile_hex = hex_strings[i*16 : (i+1)*16]
            if i == 5:
                # We comment out the second half of tile 5 using backslash-newline
                inner_content += "    " + ", ".join(tile_hex[:8]) + ", // comment continuation \\\n"
                inner_content += "    " + ", ".join(tile_hex[8:]) + ", // this should be commented out in C!\n"
            else:
                inner_content += "    " + ", ".join(tile_hex[:8]) + ",\n"
                inner_content += "    " + ", ".join(tile_hex[8:]) + ",\n"

        self.write_tiles_c(inner_content)
        
        # In actual C, tile_hex[8:] of tile 5 is commented out.
        # If verify_graphics.parse_tiles_c is robust and behaves like a C preprocessor,
        # it should NOT extract the commented-out bytes. If it does extract them, it means
        # there is a parsing discrepancy.
        # Let's run it and see.
        try:
            parsed_bytes = verify_graphics.parse_tiles_c(self.temp_file)
            print(f"[C-Parser] Backslash-newline test: Parsed {len(parsed_bytes)} bytes.")
            # If it parsed 512 bytes, it means it DID extract the commented-out bytes (since 8 bytes were commented out).
            # This is a finding!
        except Exception as e:
            print(f"[C-Parser] Backslash-newline test raised exception: {e}")


class TestBase64ExtractionJS(unittest.TestCase):
    def setUp(self):
        self.original_png_bytes = bytes(i % 256 for i in range(100))
        self.base64_data = base64.b64encode(self.original_png_bytes).decode('utf-8')

    def test_unrelated_assignment_before(self):
        """Adversarial test: Unrelated assignment in comment or string before the real one."""
        content = f"""
// Some old code:
// strike.src = "data:image/png;base64,b2xkX2RhdGE=";
// Or maybe:
const comment = "strike.src = \\"data:image/png;base64,c3RyaW5nX2RhdGE=\\";";

// Real assignment:
strike.src = "data:image/png;base64,{self.base64_data}";
"""
        try:
            extracted = extract_sprites.extract_base64_from_js(content)
            decoded = base64.b64decode(extracted)
            self.assertEqual(decoded, self.original_png_bytes, "Matched the wrong (commented/string) assignment!")
            print("[JS-Extractor] Unrelated assignment test: Passed.")
        except AssertionError as e:
            print(f"[JS-Extractor] Unrelated assignment test: FAILED (Assertion): {e}")
        except Exception as e:
            print(f"[JS-Extractor] Unrelated assignment test: FAILED (Exception): {e}")

    def test_comment_with_semicolon_inside_assignment(self):
        """Adversarial test: Comment containing a semicolon inside the strike.src assignment."""
        content = f"""
strike.src = "data:image/png;base64," + 
    // This is a comment; it contains a semicolon!
    "{self.base64_data}";
"""
        try:
            extracted = extract_sprites.extract_base64_from_js(content)
            decoded = base64.b64decode(extracted)
            self.assertEqual(decoded, self.original_png_bytes, "Semicolon in comment truncated the extraction!")
            print("[JS-Extractor] Semicolon in comment test: Passed.")
        except AssertionError as e:
            print(f"[JS-Extractor] Semicolon in comment test: FAILED (Assertion): {e}")
        except Exception as e:
            print(f"[JS-Extractor] Semicolon in comment test: FAILED (Exception): {e}")

    def test_block_comment_with_semicolon_inside_assignment(self):
        """Adversarial test: Block comment containing a semicolon inside the strike.src assignment."""
        content = f"""
strike.src = "data:image/png;base64," + /* comment; with semicolon */ "{self.base64_data}";
"""
        try:
            extracted = extract_sprites.extract_base64_from_js(content)
            decoded = base64.b64decode(extracted)
            self.assertEqual(decoded, self.original_png_bytes, "Semicolon in block comment truncated the extraction!")
            print("[JS-Extractor] Semicolon in block comment test: Passed.")
        except AssertionError as e:
            print(f"[JS-Extractor] Semicolon in block comment test: FAILED (Assertion): {e}")
        except Exception as e:
            print(f"[JS-Extractor] Semicolon in block comment test: FAILED (Exception): {e}")

    def test_unmatched_quote_in_comment(self):
        """Adversarial test: Unmatched single quote in a single-line comment."""
        content = f"""
strike.src = "data:image/png;base64," + 
    // don't break on unmatched ' quote
    "{self.base64_data}";
"""
        try:
            extracted = extract_sprites.extract_base64_from_js(content)
            decoded = base64.b64decode(extracted)
            self.assertEqual(decoded, self.original_png_bytes, "Unmatched quote in comment broke extraction!")
            print("[JS-Extractor] Unmatched quote in comment test: Passed.")
        except AssertionError as e:
            print(f"[JS-Extractor] Unmatched quote in comment test: FAILED (Assertion): {e}")
        except Exception as e:
            print(f"[JS-Extractor] Unmatched quote in comment test: FAILED (Exception): {e}")


if __name__ == "__main__":
    print("--- Running C Comment Stripping Robustness Tests ---")
    suite_c = unittest.TestLoader().loadTestsFromTestCase(TestCommentStrippingC)
    unittest.TextTestRunner(verbosity=2).run(suite_c)
    
    print("\n--- Running JS Base64 Extraction Robustness Tests ---")
    suite_js = unittest.TestLoader().loadTestsFromTestCase(TestBase64ExtractionJS)
    unittest.TextTestRunner(verbosity=2).run(suite_js)
