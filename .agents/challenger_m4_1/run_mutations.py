import os
import sys
import shutil
import tempfile
import subprocess
import unittest

# Paths
WORKSPACE = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon"
DANDY_GB = os.path.join(WORKSPACE, "dandy-gb")
SRC_DIR = os.path.join(DANDY_GB, "src")
TESTS_DIR = os.path.join(DANDY_GB, "tests")

# Add tests dir to sys.path so we can import dandy_env and test_tier4
sys.path.insert(0, TESTS_DIR)

import dandy_env
from test_tier4 import TestTier4

# Define mutations
MUTATIONS = [
    {
        "name": "Disable camera clamping (Mutation 1)",
        "file": "dandy_core.c",
        "original": """    int16_t vp_left = clamp(target_x - 10, 0, DANDY_LEVEL_WIDTH - 20);
    int16_t vp_top = clamp(target_y - 5, 0, DANDY_LEVEL_HEIGHT - 10);""",
        "mutated": """    int16_t vp_left = target_x - 10;
    int16_t vp_top = target_y - 5;""",
        "expected_fail_test": "test_scenario_a_coop_and_viewport"
    },
    {
        "name": "Mess up spectator centroid camera centering (Mutation 2)",
        "file": "dandy_core.c",
        "original": """            target_x = sum_x / alive_count;
            target_y = sum_y / alive_count;""",
        "mutated": """            target_x = sum_x;
            target_y = sum_y;""",
        "expected_fail_test": "test_scenario_b_spectator_and_game_over"
    },
    {
        "name": "Disable outer border walls reconstruction on level reload (Mutation 3)",
        "file": "dandy_core.c",
        "original": "    memset(dandy_map, TILE_WALL, MAP_SIZE);",
        "mutated": "    memset(dandy_map, TILE_SPACE, MAP_SIZE);",
        "expected_fail_test": "test_level_0_complete_walkthrough"
    },
    {
        "name": "Change LFSR generator spawn direction logic (Mutation 4)",
        "file": "dandy_core.c",
        "original": "                    uint8_t spawn_dir = (rand_seed & 3) * 2;",
        "mutated": "                    uint8_t spawn_dir = 0; // Always spawn Up",
        "expected_fail_test": "test_scenario_c_lfsr_multi_direction"
    },
    {
        "name": "Disable arrow hitting entities (Mutation 5)",
        "file": "dandy_core.c",
        "original": "            if (tile_at_new != TILE_SPACE) {",
        "mutated": "            if (false) {",
        "expected_fail_test": "test_scenario_a_generator_monster_swarm"
    },
    {
        "name": "Disable monster degradation (Mutation 6)",
        "file": "dandy_core.c",
        "original": """                    } else if (tile_at_new == TILE_MONSTER2 || tile_at_new == TILE_MONSTER3) {
                        replacement = tile_at_new - 1;""",
        "mutated": """                    } else if (tile_at_new == TILE_MONSTER2 || tile_at_new == TILE_MONSTER3) {
                        replacement = TILE_SPACE; // Destroy instantly!""",
        "expected_fail_test": "test_scenario_a_generator_monster_swarm"
    },
    {
        "name": "Smart bomb does not clear generators (Mutation 7)",
        "file": "dandy_core.c",
        "original": """            if ((tile >= TILE_MONSTER1 && tile <= TILE_MONSTER3) ||
                (tile >= TILE_GENERATOR1 && tile <= TILE_GENERATOR3)) {""",
        "mutated": """            if (tile >= TILE_MONSTER1 && tile <= TILE_MONSTER3) {""",
        "expected_fail_test": "test_scenario_b_smart_bomb_room_clear"
    }
]

def compile_lib(src_path, output_path):
    # Compile the shared library using gcc
    cmd = [
        "gcc", "-fPIC", "-shared", "-O2",
        f"-I{SRC_DIR}",
        f"-I{TESTS_DIR}/mock_gb",
        "-o", output_path,
        src_path,
        os.path.join(SRC_DIR, "levels.c"),
        os.path.join(TESTS_DIR, "mock_hal.c")
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\nStdout: {res.stdout}\nStderr: {res.stderr}")

def run_test_case(test_name, lib_path):
    # Monkey patch DandyEnv to use our mutated library
    old_init = dandy_env.DandyEnv.__init__
    def patched_init(self, custom_lib_path=None):
        # Always force our mutated library path
        old_init(self, lib_path)
        
    dandy_env.DandyEnv.__init__ = patched_init
    
    suite = unittest.TestSuite()
    suite.addTest(TestTier4(test_name))
    
    # Run the test silently
    runner = unittest.TextTestRunner(stream=open(os.devnull, 'w'), failfast=True)
    result = runner.run(suite)
    
    # Restore original init
    dandy_env.DandyEnv.__init__ = old_init
    
    return result.wasSuccessful(), result.failures, result.errors

def main():
    print("==================================================")
    print("Dandy Dungeon Tier 4 E2E Test Mutation Testing Harness")
    print("==================================================")
    
    temp_dir = tempfile.mkdtemp(prefix="dandy_mutation_")
    try:
        # Copy original dandy_core.c
        orig_core_path = os.path.join(SRC_DIR, "dandy_core.c")
        
        passed_mutations = 0
        failed_mutations = 0
        
        for idx, mut in enumerate(MUTATIONS):
            print(f"\\n[{idx+1}/{len(MUTATIONS)}] Testing: {mut['name']}")
            
            # Read original content
            with open(orig_core_path, "r") as f:
                content = f.read()
                
            # Verify original text exists
            if mut["original"] not in content:
                print(f"  ERROR: Original text not found in dandy_core.c!")
                print(f"  Looking for:\\n{mut['original']}")
                failed_mutations += 1
                continue
                
            # Apply mutation
            mutated_content = content.replace(mut["original"], mut["mutated"])
            
            # Write mutated content to temp file
            temp_core_path = os.path.join(temp_dir, f"dandy_core_mut_{idx}.c")
            with open(temp_core_path, "w") as f:
                f.write(mutated_content)
                
            # Compile mutated library
            mutated_lib_path = os.path.join(temp_dir, f"libdandy_mut_{idx}.so")
            try:
                compile_lib(temp_core_path, mutated_lib_path)
            except Exception as e:
                print(f"  Compilation failed: {e}")
                failed_mutations += 1
                continue
                
            # Run the target test
            target_test = mut["expected_fail_test"]
            print(f"  Running test: {target_test} against mutated library...")
            success, failures, errors = run_test_case(target_test, mutated_lib_path)
            
            if not success:
                print("  RESULT: SUCCESS. The test correctly caught the bug!")
                if failures:
                    print(f"    Caught via Failure: {failures[0][1].splitlines()[-1]}")
                elif errors:
                    print(f"    Caught via Error: {errors[0][1].splitlines()[-1]}")
                passed_mutations += 1
            else:
                print("  RESULT: **VULNERABILITY DETECTED!** The test PASSED despite the injected bug!")
                failed_mutations += 1
                
        print("\\n==================================================")
        print("Mutation Testing Summary:")
        print(f"  Total Mutations Tested: {len(MUTATIONS)}")
        print(f"  Mutations Caught (No False Positives): {passed_mutations}")
        print(f"  Mutations Missed (Vulnerabilities): {failed_mutations}")
        print("==================================================")
        
        if failed_mutations > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
