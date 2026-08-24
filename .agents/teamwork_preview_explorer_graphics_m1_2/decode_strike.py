import re
import base64
import struct

def extract_base64_from_js(js_path):
    with open(js_path, 'r') as f:
        content = f.read()
    
    # Use regex to find the base64 parts
    # It starts after strike.src = "data:image/png;base64,"+
    # and consists of quoted strings joined by +
    pattern = r'strike\.src\s*=\s*"data:image/png;base64,"\s*\+\s*(.*?;)'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError("Could not find strike.src base64 data in JS file")
    
    parts_block = match.group(1)
    # Find all double-quoted strings in this block
    str_pattern = r'"([^"]*)"'
    strings = re.findall(str_pattern, parts_block)
    
    # Concatenate them
    b64_str = "".join(strings)
    return b64_str

def main():
    js_path = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-js/strike.js"
    try:
        b64_str = extract_base64_from_js(js_path)
        print(f"Extracted base64 string of length: {len(b64_str)}")
        
        # Try decoding
        png_bytes = base64.b64decode(b64_str)
        print(f"Successfully decoded PNG: {len(png_bytes)} bytes")
        
        if png_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            print("Valid PNG header found")
            ihdr_offset = 8 + 4 + 4  # Skip header, length, and 'IHDR'
            width, height = struct.unpack('>II', png_bytes[ihdr_offset:ihdr_offset+8])
            print(f"PNG dimensions: {width}x{height}")
        else:
            print("Invalid PNG header!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
