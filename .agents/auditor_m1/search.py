import os

def search_files(directory, keyword):
    for root, dirs, files in os.walk(directory):
        # Skip some directories
        if '.git' in dirs:
            dirs.remove('.git')
        if '.agents' in dirs:
            dirs.remove('.agents')
            
        for file in files:
            path = os.path.join(root, file)
            try:
                with open(path, 'r', errors='ignore') as f:
                    content = f.read()
                    if keyword in content:
                        print(f"Found keyword '{keyword}' in {path}")
            except Exception as e:
                print(f"Error reading {path}: {e}")

search_files('/usr/local/google/home/jackpal/Developer/Dandy-Dungeon', 'libdandy_test.so')
