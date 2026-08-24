with open("/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-js/levels.js", "r") as f:
    for line in f:
        if "encoding" in line or "const k" in line or "const TILE" in line:
            print(line.strip())
