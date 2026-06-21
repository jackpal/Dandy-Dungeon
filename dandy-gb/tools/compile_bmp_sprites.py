import os
import sys

# ==============================================================================
# NATIVE 8x8 PIXEL ART GLYPH SPECIFICATIONS ("Code-as-Art")
# ==============================================================================
# Color Semantic Codes:
# For Background Tiles (BGP = 0x1B: 3=White, 2=Light Gray, 1=Dark Gray, 0=Black):
# - '0': Solid Black (Floor corridor, empty space)
# - '1': Dark Gray (Wall bricks, doors, stairs railings)
# - '2': Light Gray (Gold '$', keys, food, potion body)
# - '3': Bright White (HUD text / scoreboard font)
#
# For Sprite Tiles (OBP0 = 0xE0: 3=Black, 2=Dark Gray, 1=White, 0=Transparent):
# - '0': Transparent (Dungeon floor shows through)
# - '1': Bright White (Heroic player body, ghost body, glowing eyes)
# - '2': Dark Gray (Metal armor, shield, weapons, monster skin shading)
# - '3': Solid Black (Character outlines, eyes)
# ==============================================================================

GLYPHS = {
    # 0: TILE_SPACE (Empty corridor floor -> Solid Black)
    0: [
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000"
    ],
    # 1: TILE_WALL (Running bond brick texture in Dark Gray on Black mortar)
    1: [
        "00000000", # Mortar top
        "01110111", # Left brick face & Right brick face (Dark Gray 1)
        "01110111",
        "01110111",
        "00000000", # Mortar middle
        "01111111", # Large centered brick face
        "01111111",
        "01111111"
    ],
    # 2: TILE_DOOR (Vertical iron gate bars on Black background)
    2: [
        "00000000",
        "01010101", # Vertical bars
        "01010101",
        "01010101",
        "01010101",
        "01010101",
        "01010101",
        "00000000"
    ],
    # 3: TILE_UP (Stairs Up -> Clean ascending staircase "U" shape)
    3: [
        "00000000",
        "01111110", # Top step
        "01000010",
        "01000010", # Vertical railings
        "01000010",
        "01000010",
        "01111110", # Bottom step (100% complete outline!)
        "00000000"
    ],
    # 4: TILE_DOWN (Stairs Down -> Receding pit steps going into Black void)
    4: [
        "00000000",
        "01111110", # Outer step (Dark Gray 1)
        "01222210", # Middle step (Light Gray 2)
        "01200210", # Center pit void (Black 0)
        "01200210",
        "01222210",
        "01111110",
        "00000000"
    ],
    # 5: TILE_KEY (Skeleton key in Light Gray)
    5: [
        "00000000",
        "00222000", # Key head loop
        "02002220", # Key ring and horizontal shaft
        "00222020", # Key teeth
        "00000020",
        "00000000",
        "00000000",
        "00000000"
    ],
    # 6: TILE_FOOD (Roast leg of meat in Light Gray)
    6: [
        "00000000",
        "00222000", # Meat body
        "02222200",
        "02222200",
        "00222020", # Bone shaft
        "00000002", # Bone joint
        "00000000",
        "00000000"
    ],
    # 7: TILE_MONEY (Iconic Gold Dollar Sign '$' in Light Gray - Perfectly Symmetrical!)
    7: [
        "00002000", #     $     (Line top)
        "00222200", #   $$$$    (S top curve, perfectly centered)
        "00202000", #   $ $     (S left side + vertical line)
        "00022200", #    $$$    (S middle crossover)
        "00002020", #     $ $   (Vertical line + S right side)
        "00222200", #   $$$$    (S bottom curve, perfectly centered)
        "00002000", #     $     (Line bottom)
        "00002000"  #     $     (Line bottom tail)
    ],

    # 8: TILE_BOMB (Round bomb with lit, sparkling White fuse)
    8: [
        "00000030", # Spark (White 3)
        "00000200", # Fuse (Light Gray 2)
        "00222000", # Bomb top
        "02222200", # Bomb body
        "02222200",
        "02222200",
        "00222000",
        "00000000"
    ],
    # 9: TILE_MONSTER1 (Ghost -> Spooky White body with Black outlines/eyes. Sprite-only!)
    9: [
        "00333300", #   ####
        "03111130", #  #WWWW#
        "31311313", # W#W##W#W (Black eyes)
        "31111113", # WWWWWWWW
        "31111113", # WWWWWWWW
        "31111113", # WWWWWWWW
        "03101130", #  #W WW#  (Wavy bottom)
        "00303300"  #   # ##
    ],
    # 10: TILE_MONSTER2 (Demon/Imp -> Dark Gray body, White eyes, Black outlines. Sprite-only!)
    10: [
        "03000030", #  #    # (Horns)
        "03333330", #  ######
        "32211223", # DDDWWDDD# (White eyes)
        "32222223", # DDDDDDDD#
        "03222230", #  #DDDD#
        "03211230", #  #DWWD#  (Fangs)
        "00322300", #   #DD#
        "00033000"  #    ##
    ],
    # 11: TILE_MONSTER3 (Golem/Giant -> Rocky texture. Sprite-only!)
    11: [
        "03333330",
        "32233223", # Rocky head with cracks
        "32122123", # Rock brow (White highlights)
        "33322333", # Rock nose
        "32222223", # Rock jaw
        "32333323", # Rock mouth
        "03222230",
        "00333300"
    ],
    # 12: TILE_HEART (Alchemical flask containing Light Gray heart potion)
    12: [
        "00000000",
        "00111000", # Flask neck
        "01202100", # Heart outline
        "12222210", # Heart body (Light Gray 2)
        "12222210",
        "01222100",
        "00121000",
        "00010000"
    ],
    # 13: TILE_GENERATOR1 (Monster Nest Lvl 1 -> Small bone/twig pile)
    13: [
        "00000000",
        "00011000",
        "00111100",
        "01100110",
        "01011010",
        "11111111",
        "11111111",
        "00000000"
    ],
    # 14: TILE_GENERATOR2 (Monster Nest Lvl 2 -> Nest with a skull detail)
    14: [
        "00000000",
        "00111100",
        "01222210", # Skull forehead
        "12022021", # Skull eyes
        "12222221",
        "01202100", # Skull teeth/jaw
        "11111111",
        "00000000"
    ],
    # 15: TILE_GENERATOR3 (Monster Nest Lvl 3 -> Demon monolith spawner)
    15: [
        "00111100",
        "01222210",
        "12322321", # Glowing white eyes
        "12222221",
        "12233221", # Demon mouth
        "12300321",
        "11111111",
        "00000000"
    ],
    # 16: TILE_ARROW_DOWN (Arrow flying Down. Sprite-only!)
    16: [
        "00030000",
        "00030000",
        "00030000",
        "00030000",
        "00030000",
        "03030300",
        "00333000", # Tip
        "00030000"
    ],
    # 17: TILE_ARROW_UP (Arrow flying Up. Sprite-only!)
    17: [
        "00030000",
        "00333000", # Tip
        "03030300",
        "00030000",
        "00030000",
        "00030000",
        "00030000",
        "00030000"
    ],
    # 18: TILE_ARROW_LEFT (Arrow flying Left. Sprite-only!)
    18: [
        "00000000",
        "00030000",
        "00300000",
        "03333333", # Shaft & Tip
        "00300000",
        "00030000",
        "00000000",
        "00000000"
    ],
    # 19: TILE_ARROW_RIGHT (Arrow flying Right. Sprite-only!)
    19: [
        "00000000",
        "00003000",
        "00000300",
        "03333333", # Shaft & Tip
        "00000300",
        "00003000",
        "00000000",
        "00000000"
    ],
    # 20..23: Padding/Unused (Empty background -> Solid Black)
    20: [ "0"*8 ] * 8,
    21: [ "0"*8 ] * 8,
    22: [ "0"*8 ] * 8,
    23: [ "0"*8 ] * 8,
    
    # 24: TILE_PLAYER1_DOWN (Heroic knight facing Down -> White body, Black outline, Light Gray shield. Sprite-only!)
    24: [
        "00333300", #    ####    (Helmet top)
        "03111130", #   #WWWW#   (Face visor)
        "31311313", #  W#W##W#W  (Visor slit & eyes)
        "31111113", #  WWWWWWWW  (Shield shoulder)
        "03222230", #   #DDDD#   (Metal chest plate)
        "03111130", #   #WWWW#   (White tunic)
        "00311300", #    #WW#    (Legs)
        "00333300"  #    ####    (Boots)
    ],
    # 25: TILE_PLAYER1_UP (Heroic knight facing Up -> Back of helmet and White cape. Sprite-only!)
    25: [
        "00333300",
        "03111130", # Helmet back
        "31111113",
        "31111113",
        "03111130", # Large white cape
        "03111130",
        "00311300",
        "00333300"
    ],
    # 26: TILE_PLAYER1_LEFT (Heroic knight facing Left, holding shield in front. Sprite-only!)
    26: [
        "00333300",
        "03111130",
        "32211300", # Shield at left
        "32211130",
        "03111130",
        "03111130",
        "00311300",
        "00333300"
    ],
    # 27: TILE_PLAYER1_RIGHT (Heroic knight facing Right, holding shield in front. Sprite-only!)
    27: [
        "00333300",
        "03111130",
        "00311223", # Shield at right
        "03112223",
        "03111130",
        "03111130",
        "00311300",
        "00333300"
    ],
    # 28..31: Unused/Padding (Empty background -> Solid Black)
    28: [ "0"*8 ] * 8,
    29: [ "0"*8 ] * 8,
    30: [ "0"*8 ] * 8,
    31: [ "0"*8 ] * 8
}

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_h_path = os.path.normpath(os.path.join(current_dir, "../src/tiles.h"))
    output_c_path = os.path.normpath(os.path.join(current_dir, "../src/tiles.c"))
    
    print("Compiling 32 native 8x8 pixel-art glyphs into GBDK 2bpp format...")
    
    gb_tile_bytes = []
    
    # Process all 32 tiles
    for t_idx in range(32):
        glyph = GLYPHS.get(t_idx, [ "0"*8 ] * 8)
        tile_bytes = []
        
        # Pack each of the 8 rows of the glyph
        for y in range(8):
            low_byte = 0
            high_byte = 0
            row_str = glyph[y]
            
            # Pack the 8 horizontal pixels into 2 planar bytes (low_byte & high_byte)
            for x in range(8):
                val = int(row_str[x]) # Color index 0..3
                bit0 = val & 1
                bit1 = (val >> 1) & 1
                
                # Pack MSB-first
                low_byte |= (bit0 << (7 - x))
                high_byte |= (bit1 << (7 - x))
                
            tile_bytes.append(low_byte)
            tile_bytes.append(high_byte)
            
        gb_tile_bytes.append(tile_bytes)
        
    # ==========================================
    # Generate C Header (tiles.h)
    # ==========================================
    h_content = [
        "/* Generated automatically from native 8x8 code glyphs. Do not edit. */",
        "#ifndef DANDY_TILES_H",
        "#define DANDY_TILES_H",
        "",
        "#include <stdint.h>",
        "",
        "#define DANDY_NUM_TILES 32",
        "#define DANDY_TILE_SIZE 16",
        "",
        "/* GameBoy 2bpp tile data for all 32 tiles */",
        "extern const unsigned char dandy_tiles[DANDY_NUM_TILES * DANDY_TILE_SIZE];",
        "",
        "#endif /* DANDY_TILES_H */"
    ]
    
    print(f"Writing C header to {output_h_path}...")
    with open(output_h_path, "w") as f:
        f.write("\n".join(h_content))
        
    # ==========================================
    # Generate C Source (tiles.c)
    # ==========================================
    c_content = [
        "/* Generated automatically from native 8x8 code glyphs. Do not edit. */",
        '#include "tiles.h"',
        "",
        "/* 32 tiles * 16 bytes per tile = 512 bytes */",
        "const unsigned char dandy_tiles[] = {"
    ]
    
    for t_idx, tile in enumerate(gb_tile_bytes):
        c_content.append(f"    /* Tile {t_idx} */")
        hex_rows = []
        for row_idx in range(0, len(tile), 8):
            chunk = tile[row_idx:row_idx+8]
            hex_str = ", ".join([f"0x{val:02X}" for val in chunk])
            hex_rows.append(f"    {hex_str}")
        c_content.append(",\n".join(hex_rows) + ("," if t_idx < 31 else ""))
        
    c_content.append("};")
    
    print(f"Writing C source to {output_c_path}...")
    with open(output_c_path, "w") as f:
        f.write("\n".join(c_content))
        
    print("Sprite compilation complete! Output: 512 bytes of perfectly designed, un-aliased native 8x8 GameBoy assets.")

if __name__ == "__main__":
    main()
