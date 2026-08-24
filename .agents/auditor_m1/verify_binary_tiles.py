import os

ROM_PATH = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/bin/dandy.gb"
TILES_C_PATH = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/tiles.c"

def main():
    if not os.path.exists(ROM_PATH):
        print(f"ROM file {ROM_PATH} does not exist!")
        return
    if not os.path.exists(TILES_C_PATH):
        print(f"tiles.c file {TILES_C_PATH} does not exist!")
        return

    # Extract bytes from tiles.c
    import re
    print(f"Reading tiles.c from {TILES_C_PATH}...")
    with open(TILES_C_PATH, 'r') as f:
        content = f.read()

    array_match = re.search(r'const\s+unsigned\s+char\s+dandy_tiles\[\]\s*=\s*\{([^}]+)\};', content)
    if not array_match:
        print("Could not find dandy_tiles array in tiles.c!")
        return

    array_str = array_match.group(1)
    hex_vals = re.findall(r'0x[0-9a-fA-F]{2}', array_str)
    expected_bytes = bytes([int(val, 16) for val in hex_vals])

    print(f"Extracted {len(expected_bytes)} bytes of tile data from tiles.c.")
    
    # Read ROM file
    with open(ROM_PATH, 'rb') as f:
        rom_bytes = f.read()

    print(f"Read ROM file of size {len(rom_bytes)} bytes.")

    # Find the tile bytes in ROM
    idx = rom_bytes.find(expected_bytes)
    if idx != -1:
        print(f"MATCH: Found the exact 512 bytes of dandy_tiles in the ROM binary!")
        print(f"Location in ROM: offset 0x{idx:X} (decimal {idx})")
    else:
        print("MISMATCH: The 512 bytes of dandy_tiles WERE NOT found in the ROM binary!")

if __name__ == "__main__":
    main()
