import os
from PIL import Image

def print_tile(tile, name):
    print(f"=== {name} ===")
    rgba = tile.convert("RGBA")
    pixels = rgba.load()
    for y in range(16):
        line = ""
        for x in range(16):
            r, g, b, a = pixels[x, y]
            if a == 0:
                line += " "
            elif r > 150 and g < 120 and b < 120:
                line += "R"  # Red
            elif b > 150 and r < 120 and g < 120:
                line += "B"  # Blue
            elif r > 180 and g > 180 and b > 180:
                line += "W"  # White/Light
            elif r == 0 and g == 0 and b == 0:
                line += "."  # Black
            else:
                line += "?"
        print(line)
    print()

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    strike_png_path = os.path.normpath(os.path.join(current_dir, "../../dandy-gb/teamwork_graphics/strike_original.png"))
    
    img = Image.open(strike_png_path)
    
    for idx in [9, 10, 11, 12, 13]:
        tile = img.crop((idx*16, 0, (idx+1)*16, 16))
        print_tile(tile, f"JS Tile {idx}")

if __name__ == "__main__":
    main()
