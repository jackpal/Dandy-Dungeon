import base64
import re
import struct

def main():
    js_path = '/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-js/strike.js'
    with open(js_path, 'r') as f:
        content = f.read()

    # Find the base64 string parts inside double quotes
    matches = re.findall(r'"([A-Za-z0-9+/=]+)"', content)
    # The first one might be "data:image/png;base64,", let's filter or join the rest
    base64_parts = []
    for m in matches:
        if m.startswith('data:image'):
            continue
        base64_parts.append(m)
    
    base64_str = "".join(base64_parts)
    print(f"Total base64 string length: {len(base64_str)}")
    
    png_bytes = base64.b64decode(base64_str)
    print(f"Decoded PNG bytes: {len(png_bytes)}")
    
    # Let's parse the PNG signature and IHDR chunk to find dimensions
    # PNG signature: 8 bytes (89 50 4E 47 0D 0A 1A 0A)
    # IHDR chunk: 4 bytes length, 4 bytes type ('IHDR'), 13 bytes data, 4 bytes CRC
    if png_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        print("Valid PNG signature.")
    else:
        print("Invalid PNG signature!")
        return
        
    ihdr_len = struct.unpack('>I', png_bytes[8:12])[0]
    ihdr_type = png_bytes[12:16]
    if ihdr_type == b'IHDR':
        width, height = struct.unpack('>II', png_bytes[16:24])
        print(f"Dimensions: {width}x{height}")
    else:
        print("Could not find IHDR chunk!")

if __name__ == '__main__':
    main()
