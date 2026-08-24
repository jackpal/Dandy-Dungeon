import os
import re
import sys

def parse_tiles_c(tiles_c_path):
    with open(tiles_c_path, "r") as f:
        content = f.read()

    # Strip comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    content = re.sub(r'//.*?\n', '\n', content)

    # Match dandy_tiles array
    match = re.search(r"const\s+unsigned\s+char\s+dandy_tiles\s*(?:\[[^\]]*\])?\s*=\s*\{([^}]+)\}", content, re.DOTALL)
    if not match:
        raise ValueError("Could not find dandy_tiles array in tiles.c")

    array_content = match.group(1)
    num_strings = re.findall(r"0[xX][0-9a-fA-F]+|\d+", array_content)
    if len(num_strings) != 512:
        raise ValueError(f"Expected 512 values, found {len(num_strings)}")

    bytes_list = []
    for s in num_strings:
        if s.lower().startswith('0x'):
            bytes_list.append(int(s, 16))
        else:
            bytes_list.append(int(s, 10))

    return bytes(bytes_list)

def main():
    tiles_c_path = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/tiles.c"
    rom_path = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/bin/dandy.gb"

    if not os.path.exists(tiles_c_path):
        print(f"Error: {tiles_c_path} not found", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(rom_path):
        print(f"Error: {rom_path} not found", file=sys.stderr)
        sys.exit(1)

    print("Parsing dandy_tiles from tiles.c...")
    tile_bytes = parse_tiles_c(tiles_c_path)
    print(f"Parsed {len(tile_bytes)} bytes of tiles.")

    print(f"Reading ROM from {rom_path}...")
    with open(rom_path, "rb") as f:
        rom_bytes = f.read()
    print(f"ROM size: {len(rom_bytes)} bytes.")

    # Search for tile_bytes in rom_bytes
    offset = rom_bytes.find(tile_bytes)
    if offset != -1:
        print(f"SUCCESS: Compiled tile bytes found in ROM at offset {offset} (0x{offset:X})!")
        sys.exit(0)
    else:
        print("FAILURE: Compiled tile bytes NOT found in ROM!")
        # Let's check if sub-segments are found, to give more context
        # Check first non-zero tile (Tile 1, bytes 16 to 32)
        tile1 = tile_bytes[16:32]
        t1_offset = rom_bytes.find(tile1)
        if t1_offset != -1:
            print(f"Note: Tile 1 was found at offset {t1_offset} (0x{t1_offset:X}), but the full 512-byte block was not contiguous or had modifications.")
        sys.exit(1)

if __name__ == "__main__":
    main()
