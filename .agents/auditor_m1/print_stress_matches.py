import re

path = '/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tests/test_infra_stress.py'
patterns = [r'subprocess', r'os\.system', r'rm ', r'clean', r'make']

try:
    with open(path, 'r') as f:
        lines = f.readlines()
    for line_num, line in enumerate(lines, 1):
        for pattern in patterns:
            if re.search(pattern, line):
                print(f"{line_num}: {line.strip()}")
                break
except Exception as e:
    print(f"Error reading {path}: {e}")
