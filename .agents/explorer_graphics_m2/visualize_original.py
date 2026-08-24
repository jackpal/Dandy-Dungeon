import os
from PIL import Image

def main():
    img_path = '/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/strike_original.png'
    if not os.path.exists(img_path):
        print("Error: Image not found.")
        return

    img = Image.open(img_path).convert("RGBA")
    
    # We define the 4 main colors based on our analysis:
    # 1. Black: (0, 0, 0)
    # 2. Blue: (46, 55, 174)
    # 3. Red: (201, 99, 99)
    # 4. Light Blue/Gray: (215, 223, 240)
    
    # Let's write a helper to classify a color into one of these 4 categories
    def get_color_char(rgba):
        r, g, b, a = rgba
        if a < 128:
            return ' ' # Transparent (though original has no alpha < 255)
        # Calculate Euclidean distance to the 4 prototype colors
        colors = {
            '.': (0, 0, 0),
            'B': (46, 55, 174),
            'R': (201, 99, 99),
            'L': (215, 223, 240),
            'W': (255, 255, 255) # For the placeholder tiles
        }
        min_dist = float('inf')
        best_char = '?'
        for char, proto in colors.items():
            dist = (r - proto[0])**2 + (g - proto[1])**2 + (b - proto[2])**2
            if dist < min_dist:
                min_dist = dist
                best_char = char
        return best_char

    tile_w, tile_h = 16, 16
    cols = img.width // tile_w
    rows = img.height // tile_h
    
    for r in range(rows):
        for c in range(cols):
            tile_idx = r * cols + c
            print(f"\n==================== TILE {tile_idx} ====================")
            for y in range(tile_h):
                line_chars = []
                for x in range(tile_w):
                    px = img.getpixel((c * tile_w + x, r * tile_h + y))
                    line_chars.append(get_color_char(px))
                print("".join(line_chars))

if __name__ == '__main__':
    main()
