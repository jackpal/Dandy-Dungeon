import os
import numpy as np
from PIL import Image

def load_and_index_sheet():
    img_path = '/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/teamwork_graphics/strike_original.png'
    if not os.path.exists(img_path):
        raise FileNotFoundError(f"Original sheet not found at {img_path}")
    
    img = Image.open(img_path).convert("RGBA")
    w, h = img.size
    
    # Prototype colors in the original image (ordered by brightness/luminance)
    # index 0: Light Blue/Gray (Lightest)
    # index 1: Red (Medium-Light)
    # index 2: Blue (Medium-Dark)
    # index 3: Black (Darkest)
    prototypes = [
        (215, 223, 240), # 0
        (201, 99, 99),   # 1
        (46, 55, 174),   # 2
        (0, 0, 0)        # 3
    ]
    
    # Convert image to numpy array of indices 0..3
    pixels = np.array(img)
    indexed_sheet = np.zeros((h, w), dtype=np.uint8)
    

    for y in range(h):
        for x in range(w):
            r, g, b, a = [int(v) for v in pixels[y, x]]
            # If pixel is fully transparent, or if it is placeholder white, map to index 0
            if a < 128:
                indexed_sheet[y, x] = 0
                continue
            if r > 240 and g > 240 and b > 240: # White
                indexed_sheet[y, x] = 0
                continue
                
            # Find closest prototype color
            min_dist = float('inf')
            best_idx = 3
            for idx, proto in enumerate(prototypes):
                dist = (r - proto[0])**2 + (g - proto[1])**2 + (b - proto[2])**2
                if dist < min_dist:
                    min_dist = dist
                    best_idx = idx
            indexed_sheet[y, x] = best_idx
            
    return indexed_sheet, prototypes

def downscale_nearest(tile):
    # Sample top-left pixel of each 2x2 block
    return tile[::2, ::2]

def downscale_majority(tile, tie_breaker='dark'):
    out = np.zeros((8, 8), dtype=np.uint8)
    for y in range(8):
        for x in range(8):
            block = tile[2*y:2*y+2, 2*x:2*x+2]
            counts = np.bincount(block.flatten(), minlength=4)
            max_count = np.max(counts)
            candidates = np.where(counts == max_count)[0]
            if len(candidates) == 1:
                out[y, x] = candidates[0]
            else:
                if tie_breaker == 'dark':
                    # Prefer darker colors (higher index)
                    out[y, x] = np.max(candidates)
                elif tie_breaker == 'light':
                    # Prefer lighter colors (lower index)
                    out[y, x] = np.min(candidates)
                else:
                    out[y, x] = candidates[0]
    return out

def downscale_hinted(tile, tile_idx=0):
    out = np.zeros((8, 8), dtype=np.uint8)
    
    # 1. Detect left-right symmetry in the 16x16 tile
    left_side = tile[:, :8]
    right_side_flipped = np.fliplr(tile[:, 8:])
    symmetry_score = np.sum(left_side == right_side_flipped) / 128.0
    is_symmetric = symmetry_score > 0.85
    
    # 2. Define tile-specific weights for feature preservation
    # Default weights: favor foreground (0, 1, 2) over background (3) in ties
    weights = [2.0, 2.0, 2.0, 1.0]
    
    if tile_idx == 1:
        # Wall: Black (3) is foreground cracks, Blue (2) is background.
        # We want to preserve Black cracks.
        weights = [1.0, 1.0, 1.5, 2.5]
    elif tile_idx == 2:
        # Door: Black (3) is outline, others are body.
        weights = [1.0, 2.0, 2.0, 2.5]
    elif tile_idx == 7:
        # Money/Dollar Sign: Red (1) is foreground, Black (3) is background.
        # We want to strongly preserve Red to keep the S-curve and vertical lines connected.
        # Setting weight of Red to 3.1 ensures that 1 Red + 3 Black -> Red (3.1 > 3.0).
        weights = [1.0, 3.1, 1.0, 1.0]
    elif tile_idx in [3, 4, 5]:
        # Stairs and Key: Red (1) is foreground, Black (3) is background.
        weights = [1.0, 2.5, 1.0, 1.0]
        
    for y in range(8):
        for x in range(8):
            if is_symmetric and x >= 4:
                # Enforce symmetry by mirroring the left side
                out[y, x] = out[y, 7-x]
                continue
                
            block = tile[2*y:2*y+2, 2*x:2*x+2]
            
            if is_symmetric and x < 4:
                mirrored_block = tile[2*y:2*y+2, 2*(7-x):2*(7-x)+2]
                combined = np.concatenate([block.flatten(), mirrored_block.flatten()])
                counts = np.bincount(combined, minlength=4)
            else:
                counts = np.bincount(block.flatten(), minlength=4)
                
            # Apply weights
            weighted_scores = counts * weights
            out[y, x] = np.argmax(weighted_scores)
            
    # Specialized post-processing/hinting for Dollar Sign to ensure the vertical stroke is continuous
    if tile_idx == 7:
        # The vertical stroke of the dollar sign is at col 2 and col 4 (in 8x8 grid).
        # Let's ensure that if they are active on row 6, they continue to row 7.
        if out[6, 2] == 1:
            out[7, 2] = 1
        if out[6, 4] == 1:
            out[7, 4] = 1
        
    return out

def recreate_colored_sheet(indexed_sheet, colors, upscale=8):
    h, w = indexed_sheet.shape
    out_img = Image.new("RGBA", (w, h))
    pixels = out_img.load()
    
    for y in range(h):
        for x in range(w):
            idx = indexed_sheet[y, x]
            out_img.putpixel((x, y), colors[idx] + (255,))
            
    if upscale > 1:
        try:
            nn = Image.Resampling.NEAREST
        except AttributeError:
            nn = Image.NEAREST
        out_img = out_img.resize((w * upscale, h * upscale), nn)
        
    return out_img

def main():
    out_dir = '/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_graphics_m2/'
    os.makedirs(out_dir, exist_ok=True)
    indexed_sheet, original_colors = load_and_index_sheet()
    h, w = indexed_sheet.shape
    
    tile_w, tile_h = 16, 16
    cols = w // tile_w
    rows = h // tile_h
    
    # GameBoy Classic DMG Palette
    dmg_colors = [
        (255, 255, 255), # 0 (White)
        (170, 170, 170), # 1 (Light Gray)
        (85, 85, 85),    # 2 (Dark Gray)
        (0, 0, 0)        # 3 (Black)
    ]
    
    # We will run three algorithms:
    # 1. Nearest-Neighbor
    # 2. Majority Vote (with dark preference)
    # 3. Font-Hinting inspired
    
    algorithms = {
        'nn': downscale_nearest,
        'majority': lambda tile, idx: downscale_majority(tile, 'dark'),
        'hinted': downscale_hinted
    }
    
    results = {}
    for name, algo in algorithms.items():
        downscaled_sheet = np.zeros((rows * 8, cols * 8), dtype=np.uint8)
        for r in range(rows):
            for c in range(cols):
                tile_idx = r * cols + c
                tile = indexed_sheet[r*tile_h:(r+1)*tile_h, c*tile_w:(c+1)*tile_w]
                
                # Run algorithm
                if name == 'nn':
                    dtile = algo(tile)
                else:
                    dtile = algo(tile, tile_idx)
                    
                downscaled_sheet[r*8:(r+1)*8, c*8:(c+1)*8] = dtile
        results[name] = downscaled_sheet
        
        # Save sheet with original colors
        img_orig = recreate_colored_sheet(downscaled_sheet, original_colors, upscale=8)
        img_orig.save(os.path.join(out_dir, f'mathematical_tiles_{name}_orig.png'))
        
        # Save sheet with DMG colors
        img_dmg = recreate_colored_sheet(downscaled_sheet, dmg_colors, upscale=8)
        img_dmg.save(os.path.join(out_dir, f'mathematical_tiles_{name}_dmg.png'))
        
        print(f"Generated downscaled sheets for algorithm: {name}")

    # Generate a comprehensive side-by-side comparison sheet
    # Format: for each of the 32 tiles, we show a row:
    # Original 16x16 (upscaled 8x to 128x128) | NN 8x8 (upscaled 16x to 128x128) | Majority 8x8 (upscaled 16x) | Hinted 8x8 (upscaled 16x)
    # Let's use DMG colors for this comparison, as it represents the GameBoy output.
    
    try:
        nn_filter = Image.Resampling.NEAREST
    except AttributeError:
        nn_filter = Image.NEAREST
        
    comp_w = 128 * 4 + 30  # 4 tiles of 128x128, plus 10px spacing
    comp_h = 128 * 32 + 31 * 10 # 32 tiles, plus 10px spacing
    
    comp_img = Image.new("RGB", (comp_w, comp_h), (50, 50, 50))
    
    for idx in range(32):
        r, c = idx // 16, idx % 16
        # Crop original 16x16
        orig_tile_idx = indexed_sheet[r*tile_h:(r+1)*tile_h, c*tile_w:(c+1)*tile_w]
        orig_img = Image.new("RGB", (16, 16))
        for ty in range(16):
            for tx in range(16):
                orig_img.putpixel((tx, ty), dmg_colors[orig_tile_idx[ty, tx]])
        orig_upscaled = orig_img.resize((128, 128), nn_filter)
        
        # Paste original
        y_offset = idx * 138
        comp_img.paste(orig_upscaled, (0, y_offset))
        
        # Paste downscaled versions
        for col_idx, name in enumerate(['nn', 'majority', 'hinted']):
            ds_sheet = results[name]
            ds_r, ds_c = idx // 16, idx % 16
            ds_tile = ds_sheet[ds_r*8:(ds_r+1)*8, ds_c*8:(ds_c+1)*8]
            
            ds_img = Image.new("RGB", (8, 8))
            for ty in range(8):
                for tx in range(8):
                    ds_img.putpixel((tx, ty), dmg_colors[ds_tile[ty, tx]])
            ds_upscaled = ds_img.resize((128, 128), nn_filter)
            
            x_offset = (col_idx + 1) * 138
            comp_img.paste(ds_upscaled, (x_offset, y_offset))
            
    comp_img.save(os.path.join(out_dir, 'comparison_grid.png'))
    print("Generated comparison_grid.png successfully!")

if __name__ == '__main__':
    main()
