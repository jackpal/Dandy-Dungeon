import os
from PIL import Image

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    strike_png_path = os.path.normpath(os.path.join(current_dir, "../../dandy-gb/teamwork_graphics/strike_original.png"))
    
    if not os.path.exists(strike_png_path):
        print(f"Error: {strike_png_path} does not exist")
        return
        
    img = Image.open(strike_png_path)
    print(f"Image size: {img.size}")
    
    # Let's save each tile as a small PNG to inspect, or analyze its non-transparent pixels
    os.makedirs(os.path.join(current_dir, "tiles_extracted"), exist_ok=True)
    
    cols = img.width // 16
    rows = img.height // 16
    
    print(f"Extracting {rows}x{cols} tiles...")
    for r in range(rows):
        for c in range(cols):
            idx = r * cols + c
            tile = img.crop((c*16, r*16, (c+1)*16, (r+1)*16))
            tile.save(os.path.join(current_dir, f"tiles_extracted/tile_{idx}.png"))
            
            # Count colors and non-transparent pixels
            rgba = tile.convert("RGBA")
            pixels = list(rgba.getdata())
            # Let's get unique RGB colors where we ignore the alpha channel or print it too
            unique_rgbs = set(p[:3] for p in pixels)
            print(f"Tile {idx:02d}: unique colors = {sorted(list(unique_rgbs))}")

if __name__ == "__main__":
    main()
