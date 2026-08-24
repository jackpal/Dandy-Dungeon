import os
import re

def print_clean_make_lines():
    files_to_check = [
        '/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tests/test_tier1.py',
        '/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tests/test_tier2.py',
        '/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tests/test_tier3.py'
    ]
    patterns = [r'subprocess', r'os\.system', r'rm ', r'clean', r'make']
    for path in files_to_check:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    lines = f.readlines()
                for line_num, line in enumerate(lines, 1):
                    for pattern in patterns:
                        # exclude common helper functions that have 'clean' in their name
                        if 'helper_setup_clean_map' in line or 'clear_mock_buffers' in line:
                            continue
                        if re.search(pattern, line):
                            print(f"{path}:{line_num}: {line.strip()}")
                            break
            except Exception as e:
                print(f"Error reading {path}: {e}")

print_clean_make_lines()
