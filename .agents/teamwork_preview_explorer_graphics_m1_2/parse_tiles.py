import re

def parse_tiles_c(tiles_c_path):
    with open(tiles_c_path, 'r') as f:
        content = f.read()
    
    match = re.search(r'const unsigned char dandy_tiles\[\]\s*=\s*\{(.*?)\};', content, re.DOTALL)
    if not match:
        raise ValueError("Could not find dandy_tiles array in tiles.c")
        
    array_content = match.group(1)
    hex_values = re.findall(r'0x[0-9a-fA-F]{2}', array_content)
    bytes_data = bytearray(int(val, 16) for val in hex_values)
    return bytes_data

def main():
    tiles_c_path = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/src/tiles.c"
    try:
        tiles_bytes = parse_tiles_c(tiles_c_path)
        print(f"Parsed {len(tiles_bytes)} bytes from tiles.c")
        if len(tiles_bytes) == 512:
            print("Successfully verified 512 bytes (32 tiles * 16 bytes/tile)")
        else:
            print("Error: Length is not 512 bytes!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
