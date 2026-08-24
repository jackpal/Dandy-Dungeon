from PIL import Image

img = Image.open("/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/strike_original.png")
print("Image size:", img.size)

for col in range(8):
    box = (col * 16, 0, col * 16 + 16, 16)
    tile = img.crop(box)
    colors = tile.getcolors()
    print(f"\n--- Tile {col} ---")
    print(f"Unique colors: {colors}")
    # Print a small 16x16 ASCII grid where each character represents the color index
    color_map = {color[1]: idx for idx, color in enumerate(sorted(colors, key=lambda x: x[0], reverse=True))}
    for y in range(16):
        row_str = ""
        for x in range(16):
            p = tile.getpixel((x, y))
            row_str += str(color_map[p])
        print(row_str)

