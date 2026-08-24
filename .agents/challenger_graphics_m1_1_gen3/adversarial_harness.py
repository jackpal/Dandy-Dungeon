#!/usr/bin/env python3
import os
import shutil
import subprocess
import tempfile
import unittest

# Paths
VENV_PYTHON = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/.venv/bin/python"
SRC_VERIFY_GRAPHICS = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/verify_graphics.py"
SRC_TILES_C = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/tiles.c"
SRC_STRIKE_PNG = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/strike_original.png"

class AdversarialStressTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a temporary environment to run the tool safely
        cls.temp_dir = tempfile.mkdtemp(prefix="verify_graphics_stress_")
        cls.tools_dir = os.path.join(cls.temp_dir, "tools")
        cls.src_dir = os.path.join(cls.temp_dir, "src")
        cls.graphics_dir = os.path.join(cls.temp_dir, "teamwork_graphics")
        
        os.makedirs(cls.tools_dir)
        os.makedirs(cls.src_dir)
        os.makedirs(cls.graphics_dir)
        
        # Copy verify_graphics.py and strike_original.png
        cls.dest_verify_graphics = os.path.join(cls.tools_dir, "verify_graphics.py")
        shutil.copy(SRC_VERIFY_GRAPHICS, cls.dest_verify_graphics)
        os.chmod(cls.dest_verify_graphics, 0o755)
        
        cls.dest_strike_png = os.path.join(cls.graphics_dir, "strike_original.png")
        shutil.copy(SRC_STRIKE_PNG, cls.dest_strike_png)
        
        # Keep track of original tiles.c content to use as a baseline
        with open(SRC_TILES_C, "r") as f:
            cls.original_tiles_c_content = f.read()

    @classmethod
    def tearDownClass(cls):
        # Clean up temp directory
        shutil.rmtree(cls.temp_dir)

    def write_tiles_c(self, content):
        path = os.path.join(self.src_dir, "tiles.c")
        with open(path, "w") as f:
            f.write(content)
        return path

    def run_tool(self, args=None, expect_success=True):
        if args is None:
            args = []
        cmd = [VENV_PYTHON, self.dest_verify_graphics] + args
        # Run from the tools directory to mimic standard execution context
        result = subprocess.run(
            cmd,
            cwd=self.tools_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Check for unhandled Python exceptions / tracebacks
        has_traceback = "Traceback" in result.stderr or "Traceback" in result.stdout
        
        if has_traceback:
            print(f"\n--- TRACEBACK DETECTED ---")
            print(f"Cmd: {' '.join(cmd)}")
            print(f"Stdout:\n{result.stdout}")
            print(f"Stderr:\n{result.stderr}")
            print(f"--------------------------")
            
        self.assertFalse(
            has_traceback,
            f"Unhandled Python exception/traceback detected!\nStderr:\n{result.stderr}\nStdout:\n{result.stdout}"
        )
        
        if expect_success:
            self.assertEqual(
                result.returncode, 0,
                f"Expected success (exit code 0), but got {result.returncode}.\nStdout:\n{result.stdout}\nStderr:\n{result.stderr}"
            )
        else:
            self.assertNotEqual(
                result.returncode, 0,
                f"Expected failure (exit code != 0), but got {result.returncode}.\nStdout:\n{result.stdout}\nStderr:\n{result.stderr}"
            )
            
        return result

    # --- TEST CASES ---

    def test_01_valid_baseline(self):
        """Test that the baseline valid tiles.c runs successfully."""
        self.write_tiles_c(self.original_tiles_c_content)
        self.run_tool(expect_success=True)

    def test_02_empty_file(self):
        """Test that an empty tiles.c fails gracefully."""
        self.write_tiles_c("")
        result = self.run_tool(expect_success=False)
        self.assertIn("Could not find 'dandy_tiles' array", result.stderr or result.stdout)

    def test_03_truncated_array(self):
        """Test that a truncated dandy_tiles array fails gracefully."""
        content = "const unsigned char dandy_tiles[] = { 0x00, 0x01, 0x02 };"
        self.write_tiles_c(content)
        result = self.run_tool(expect_success=False)
        self.assertIn("Expected exactly 512 values", result.stderr or result.stdout)

    def test_04_oversized_array(self):
        """Test that an oversized dandy_tiles array fails gracefully."""
        # Generate 513 values
        vals = ", ".join(["0x00"] * 513)
        content = f"const unsigned char dandy_tiles[] = {{ {vals} }};"
        self.write_tiles_c(content)
        result = self.run_tool(expect_success=False)
        self.assertIn("Expected exactly 512 values", result.stderr or result.stdout)

    def test_05_valid_comments(self):
        """Test that various valid comments are stripped successfully and don't block parsing."""
        # Take original content, add comments inside the array
        modified = self.original_tiles_c_content
        # Insert a single line comment
        modified = modified.replace("0x00,", "0x00, // this is a comment\n")
        # Insert a multi-line comment
        modified = modified.replace("0x1F,", "0x1F, /* multi-line comment */")
        
        self.write_tiles_c(modified)
        self.run_tool(expect_success=True)

    def test_06_comment_with_curly_brace(self):
        """Test how the script handles a closing curly brace inside a comment in the array."""
        # This is a classic regex trap: a comment containing '}' might prematurely end the match.
        modified = self.original_tiles_c_content
        modified = modified.replace("0x00,", "0x00, /* } comment with brace */")
        
        self.write_tiles_c(modified)
        # Let's see if this succeeds or fails!
        result = self.run_tool(expect_success=True)

    def test_07_invalid_hex_characters(self):
        """Test that invalid hex characters are detected as errors instead of silently accepted or crashing."""
        # We replace one of the values with '0xGG'.
        # Standard valid array has 512 values. We change one to 0xGG.
        modified = self.original_tiles_c_content
        # Let's replace the first occurrence of 0x00 with 0xGG
        modified = modified.replace("0x00,", "0xGG,", 1)
        
        self.write_tiles_c(modified)
        
        # If the tool silently accepts it, it will succeed (which is a BUG!).
        # If it fails gracefully, it's good.
        # If it throws a traceback, it's a crash.
        result = self.run_tool(expect_success=False)

    def test_08_out_of_range_decimal(self):
        """Test that decimal values out of 0-255 range fail gracefully."""
        modified = self.original_tiles_c_content
        # Replace first 0x00 with 256
        modified = modified.replace("0x00,", "256,", 1)
        self.write_tiles_c(modified)
        
        result = self.run_tool(expect_success=False)

    def test_09_out_of_range_hex(self):
        """Test that hex values out of 0-255 range (e.g., 0x100) fail gracefully."""
        modified = self.original_tiles_c_content
        # Replace first 0x00 with 0x100
        modified = modified.replace("0x00,", "0x100,", 1)
        self.write_tiles_c(modified)
        
        result = self.run_tool(expect_success=False)

    def test_10_negative_values(self):
        """Test that negative values fail gracefully instead of being silently converted to positive or crashing."""
        modified = self.original_tiles_c_content
        # Replace first 0x00 with -1
        modified = modified.replace("0x00,", "-1,", 1)
        self.write_tiles_c(modified)
        
        result = self.run_tool(expect_success=False)

    def test_11_missing_sprite_sheet(self):
        """Test that missing strike_original.png fails gracefully."""
        self.write_tiles_c(self.original_tiles_c_content)
        # Temporarily move strike_original.png away
        temp_png_path = os.path.join(self.temp_dir, "temp_strike.png")
        shutil.move(self.dest_strike_png, temp_png_path)
        
        try:
            result = self.run_tool(expect_success=False)
            self.assertIn("Original sprite sheet not found", result.stderr or result.stdout)
        finally:
            # Restore strike_original.png
            shutil.move(temp_png_path, self.dest_strike_png)

    def test_12_invalid_cli_arguments(self):
        """Test that invalid CLI arguments fail gracefully."""
        self.write_tiles_c(self.original_tiles_c_content)
        result = self.run_tool(args=["--non-existent-flag"], expect_success=False)
        self.assertIn("unrecognized arguments", result.stderr or result.stdout)

    def test_13_alternative_array_declarations(self):
        """Test if the script can parse alternative valid C array declarations."""
        # 1. 'static const unsigned char dandy_tiles[]'
        content_static = self.original_tiles_c_content.replace("const unsigned char dandy_tiles", "static const unsigned char dandy_tiles")
        self.write_tiles_c(content_static)
        self.run_tool(expect_success=True)

        # 2. 'unsigned char dandy_tiles[]' (without const)
        content_no_const = self.original_tiles_c_content.replace("const unsigned char dandy_tiles", "unsigned char dandy_tiles")
        self.write_tiles_c(content_no_const)
        self.run_tool(expect_success=True)

        # 3. 'const unsigned char dandy_tiles[512]' (explicit size)
        content_explicit_size = self.original_tiles_c_content.replace("const unsigned char dandy_tiles[]", "const unsigned char dandy_tiles[512]")
        self.write_tiles_c(content_explicit_size)
        self.run_tool(expect_success=True)

        # 4. 'uint8_t dandy_tiles[]' (typedef style)
        content_uint8 = self.original_tiles_c_content.replace("const unsigned char dandy_tiles", "const uint8_t dandy_tiles")
        self.write_tiles_c(content_uint8)
        self.run_tool(expect_success=True)

if __name__ == "__main__":
    unittest.main()
