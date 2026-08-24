import base64
import re

def main():
    js_path = '/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-js/strike.js'
    with open(js_path, 'r') as f:
        content = f.read()

    matches = re.findall(r'"([A-Za-z0-9+/=]+)"', content)
    base64_parts = [m for m in matches if not m.startswith('data:image')]
    base64_str = "".join(base64_parts)
    
    png_bytes = base64.b64decode(base64_str)
    
    out_path = '/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_m1_3/strike_decoded.png'
    with open(out_path, 'wb') as f:
        f.write(png_bytes)
    print("Saved decoded image to strike_decoded.png")

if __name__ == '__main__':
    main()
