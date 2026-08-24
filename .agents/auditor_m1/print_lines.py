import os
import re

def print_matching_lines(directory):
    patterns = [r'subprocess', r'os\.system', r'rm ', r'clean', r'make']
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r') as f:
                        lines = f.readlines()
                    for line_num, line in enumerate(lines, 1):
                        for pattern in patterns:
                            if re.search(pattern, line):
                                print(f"{path}:{line_num}: {line.strip()}")
                                break
                except Exception as e:
                    print(f"Error reading {path}: {e}")

print_matching_lines('/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tests')
