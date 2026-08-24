import os
import re

def parse_tiles_c(tiles_c_path):
    print(f"Reading tiles definition from {tiles_c_path}...")
    with open(tiles_c_path, "r") as f:
        content = f.read()
    
    # Match the dandy_tiles array content
    match = re.search(r"const\s+unsigned\s+char\s+dandy_tiles\[\]\s*=\s*\{([^}]+)\};", content, re.DOTALL)
    if not match:
        raise ValueError("Could not find dandy_tiles array in tiles.c")
    
    array_content = match.group(1)
    # Strip C-style comments to avoid matching hex values inside comments (like /* offset 0xAA */)
    array_content_clean = re.sub(r"/\*.*?\*/", "", array_content, flags=re.DOTALL)
    hex_values = re.findall(r"0x[0-9a-fA-F]{2}", array_content_clean)
    print(f"DEBUG: Hex values found (after cleaning comments): {len(hex_values)}")
    for i, val in enumerate(hex_values):
        if i % 16 == 0:
            print(f"\nTile {i//16}: ", end="")
        print(val, end=", ")
    print("\n")
    if len(hex_values) != 512:
        raise ValueError(f"Expected 512 hex values in dandy_tiles, but found {len(hex_values)}")
    
    return bytes(int(val, 16) for val in hex_values)

def verify_rom():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    tiles_c_path = os.path.normpath(os.path.join(current_dir, "../../dandy-gb/src/tiles.c"))
    rom_path = os.path.normpath(os.path.join(current_dir, "../../dandy-gb/bin/dandy.gb"))

    if not os.path.exists(rom_path):
        print(f"ERROR: ROM not found at {rom_path}")
        return False

    # 1. Read ROM
    with open(rom_path, "rb") as f:
        rom_data = f.read()

    print(f"ROM size: {len(rom_data)} bytes")
    if len(rom_data) < 32768:
        print("ERROR: ROM size is too small for a standard GameBoy ROM (min 32KB)")
        return False

    # 2. Verify GameBoy Header (Nintendo Logo at 0x104 - 0x133)
    # GBDK ROMs must have the correct Nintendo logo bytes or the GameBoy won't boot it.
    nintendo_logo_sig = (
        b"\xce\xed\x66\x66\xcc\x0d\x00\x0b\x03\x73\x00\x83\x00\x0c\x00\x0d"
        b"\x00\x08\x11\x1f\x88\x89\x00\x0e\xdc\xcc\x6e\xe6\xdd\xdd\xd9\x99"
        b"\xbb\xbb\x67\x63\x6e\x0e\xec\xcc\xdd\xdc\x99\x9f\xbb\xb9\x33\x3e"
    )
    rom_logo = rom_data[0x104:0x134]
    if rom_logo == nintendo_logo_sig:
        print("PASS: Nintendo logo signature in ROM header is valid.")
    else:
        print("FAIL: Invalid Nintendo logo signature in ROM header. This is not a bootable GB ROM.")
        return False

    # 3. Parse tiles from tiles.c
    tiles_bytes = parse_tiles_c(tiles_c_path)

    # 4. Search for the tiles in the ROM
    idx = rom_data.find(tiles_bytes)
    if idx != -1:
        print(f"PASS: Found dandy_tiles byte sequence in ROM at offset 0x{idx:X} ({idx})!")
        return True
    else:
        print("FAIL: Could not find dandy_tiles byte sequence in the compiled ROM!")
        return False

if __name__ == "__main__":
    success = verify_rom()
    import sys
    sys.exit(0 if success else 1)
