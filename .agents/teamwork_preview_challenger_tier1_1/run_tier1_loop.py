import sys
import os
import unittest

# Add dandy-gb/tests to path
sys.path.insert(0, "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tests")

from test_tier1 import TestTier1

def run_loop():
    runner = unittest.TextTestRunner(verbosity=0)
    
    print("Starting Tier 1 test loop (50 iterations)...")
    for i in range(1, 51):
        suite = unittest.TestSuite()
        loader = unittest.TestLoader()
        suite.addTests(loader.loadTestsFromTestCase(TestTier1))
        
        result = runner.run(suite)
        if not result.wasSuccessful():
            print(f"\nIteration {i} FAILED!")
            print(f"Failures: {len(result.failures)}")
            for f in result.failures:
                print(f[0], "\n", f[1])
            print(f"Errors: {len(result.errors)}")
            for e in result.errors:
                print(e[0], "\n", e[1])
            sys.exit(1)
        else:
            # We can print progress every 10 iterations to avoid too much stdout bloat
            if i % 10 == 0 or i == 1:
                print(f"Iteration {i} passed.")
    print("All 50 iterations passed successfully!")

if __name__ == "__main__":
    run_loop()
