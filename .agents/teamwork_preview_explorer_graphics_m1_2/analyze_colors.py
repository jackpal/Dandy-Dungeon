from PIL import Image
import base64
import io

def main():
    js_path = "/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-js/strike.js"
    with open(js_path, 'r') as f:
        content = f.read()
    
    import re
    pattern = r'strike\.src\s*=\s*"data:image/png;base64,"\s*\+\s*(.*?;)'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        print("Could not find strike.src base64 data")
        return
        
    parts_block = match.group(1)
    str_pattern = r'"([^"]*)"'
    strings = re.findall(str_pattern, parts_block)
    b64_str = "".join(strings)
    
    png_bytes = base64.b64decode(b64_str)
    
    # Load with PIL
    img = Image.open(io.BytesIO(png_bytes))
    print(f"Image format: {img.format}, size: {img.size}, mode: {img.mode}")
    
    # Get unique colors
    colors = img.getcolors(maxcolors=256)
    print("Unique colors (count, color):")
    for count, color in sorted(colors, reverse=True):
        print(f"  {count}: {color}")

if __name__ == "__main__":
    main()
