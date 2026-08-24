import os
import re

def search_patterns(directory):
    patterns = [r'subprocess', r'os\.system', r'rm ', r'clean', r'make']
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r') as f:
                        content = f.read()
                    for pattern in patterns:
                        if re.search(pattern, content):
                            print(f"Found pattern '{pattern}' in {path}")
                except Exception as e:
                    print(f"Error reading {path}: {e}")

search_patterns('/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tests')
