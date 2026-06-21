import unittest
import sys
import os

class TestDebugImports(unittest.TestCase):
    def test_print_paths(self):
        print("\n=== DEBUG IMPORTS ===")
        print("CWD:", os.getcwd())
        print("sys.path:", sys.path)
        try:
            import downscale
            print("downscale package path:", downscale.__file__)
            import downscale.compiler
            print("downscale.compiler path:", downscale.compiler.__file__)
        except Exception as e:
            print("Import failed with error:", e)
        print("=====================\n")
