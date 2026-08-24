# Technical Analysis: Palette & Sprite Integration (Milestone 4)

This report details the technical investigation for Milestone 4 (Palette & Sprite Integration) of the graphics downscaling pipeline in the GameBoy implementation of Dandy Dungeon (`dandy-gb/`).

---

## 1. Summary of Findings

1.  **Hardware Palette Control**: The GameBoy hardware palettes are controlled by registers `BGP_REG` (Background Palette), `OBP0_REG` (Sprite Palette 0), and `OBP1_REG` (Sprite Palette 1). Currently, these registers are hardcoded in `src/main.c` to the **Atmospheric Dark** configuration (`BGP_REG = 0x1B`, `OBP0_REG/OBP1_REG = 0xE0`).
2.  **Sprite Configurations**:
    *   **Offsets**: Sprite coordinates are offset by `(8, 16)` pixels in `src/gameboy_hal.c::hal_set_sprite` via GBDK's `move_sprite(sprite_idx, x + 8, y + 16)`. This is mathematically correct since GameBoy hardware sprite coordinates start at `(8, 16)` relative to the top-left of the screen.
    *   **Flags & OAM**: Sprite property flags (palette and flip) are set via `set_sprite_prop(sprite_idx, flags)`.
    *   **Transparency**: In GameBoy hardware, Color Index `0` of any sprite tile is **always rendered as transparent**, regardless of the palette mapping. Outlines and details utilize Color Indexes `1`, `2`, and `3`.
    *   **Palette Selection**: Because `OBP0_REG` and `OBP1_REG` are configured to identical mappings in both modes, the choice of OBP0 vs OBP1 (Bit 4 of the sprite flags) is redundant but works consistently.
3.  **HUD Rendering and Palette Interaction**:
    *   The HUD is drawn using programmatically inverted font tiles at index `160` to produce light-on-dark text on a dark background block.
    *   **Classic DMG**: `BGP_REG = 0xE4` (Normal). Index `0` is White, Index `3` is Black. Inverted space (tile `160`) has all pixels as Index `3` (Black), creating a **solid black HUD block** with White text (Index `0`).
    *   **Atmospheric Dark**: `BGP_REG = 0x1B` (Inverted). Index `0` is Black, Index `3` is White. Inverted space (tile `160`) has all pixels as Index `3` (White), creating a **solid white HUD block** with Black text (Index `0`).
    *   *Note*: In Atmospheric Dark mode, this creates a light scoreboard block, whereas the comment in `src/gameboy_hal.c` says: `"creating a solid dark background block"`. Keeping the current implementation maintains this white HUD background behavior, which is already present in the codebase. Proposing code changes to keep it black is discussed in the *HUD Consistency & Design Considerations* section.

---

## 2. Hardware Palette Mappings

GameBoy 2bpp color indexes (0 to 3) are mapped to 4 shades of gray (White, Light Gray, Dark Gray, Black) using the palette registers.

### Classic DMG Mode (Default)
*   **BGP_REG = 0xE4** (`11 10 01 00` binary):
    *   Index 3 -> Black (`11`)
    *   Index 2 -> Dark Gray (`10`)
    *   Index 1 -> Light Gray (`01`)
    *   Index 0 -> White (`00`)
    *   *Aesthetic*: Floor is White. Walls are Light Gray. Text/outlines are Black.
*   **OBP0_REG / OBP1_REG = 0xD8** (`11 01 10 00` binary):
    *   Index 3 -> Black (`11`)
    *   Index 2 -> Light Gray (`01`)  *(Details)*
    *   Index 1 -> Dark Gray (`10`)   *(Body)*
    *   Index 0 -> Transparent (Hardware forced)
    *   *Aesthetic*: Sprites are dark silhouettes with Dark Gray bodies, Light Gray details, and Black outlines.

### Atmospheric Dark Mode (`USE_BLACK_FLOOR`)
*   **BGP_REG = 0x1B** (`00 01 10 11` binary):
    *   Index 3 -> White (`00`)
    *   Index 2 -> Light Gray (`01`)
    *   Index 1 -> Dark Gray (`10`)
    *   Index 0 -> Black (`11`)
    *   *Aesthetic*: Floor is Black. Walls are Dark Gray. Text/decorations are White.
*   **OBP0_REG / OBP1_REG = 0xE0** (`11 10 00 00` binary):
    *   Index 3 -> Black (`11`)
    *   Index 2 -> Dark Gray (`10`)   *(Details)*
    *   Index 1 -> White (`00`)       *(Body)*
    *   Index 0 -> Transparent (Hardware forced)
    *   *Aesthetic*: Sprites have bright White bodies, Dark Gray details, and Black outlines.

---

## 3. Sprite Configuration & Transparency

*   **Transparency**: No code changes are required to support sprite transparency. GBDK and GameBoy hardware automatically treat Color Index `0` as transparent. The graphics asset compiler must ensure that transparent pixels in the original sprites are mapped to Color Index `0` in the compiled 2bpp binary data.
*   **Offsets**: The vertical and horizontal offsets `x + 8` and `y + 16` in `src/gameboy_hal.c` are fully correct and compliant with GBDK/GameBoy hardware sprite layout requirements.
*   **OAM Flags**: `set_sprite_prop(sprite_idx, flags)` is used. Since the two sprite palettes (`OBP0_REG` and `OBP1_REG`) are set to identical values, any palette selection flags in OAM will result in the correct visual mapping.

---

## 4. HUD Consistency & Design Considerations

In `src/gameboy_hal.c`, the scoreboard is filled using:
```c
fill_bkg_rect(0, 10, 20, 8, 160);
```
Where `160` is the inverted space tile (all pixels set to Index `3`).
*   In **Classic DMG**, Index `3` is Black, so the HUD is Black with White text.
*   In **Atmospheric Dark**, Index `3` is White, so the HUD is White with Black text.

If we want the HUD scoreboard to be **solid dark (Black) in both modes**, we should conditionally choose the background fill tile and the font range based on `#ifdef USE_BLACK_FLOOR`:
*   **Without `USE_BLACK_FLOOR` (Classic DMG)**:
    *   Fill HUD with tile `160` (inverted space = Index 3 = Black).
    *   Draw HUD text using inverted font `160 + char` (text = Index 0 = White).
*   **With `USE_BLACK_FLOOR` (Atmospheric Dark)**:
    *   Fill HUD with tile `0` (normal space = Index 0 = Black).
    *   Draw HUD text using normal font `char` (text = Index 3 = White).

### Recommendation:
To keep the code simple, low-overhead, and maintain full compatibility with the existing graphics layout:
1.  We should implement the palette toggling in `src/main.c` using `#ifdef USE_BLACK_FLOOR`.
2.  If the team wishes to maintain a Black HUD in both modes, we can implement compile-time macro switches in `src/gameboy_hal.c`. If a White HUD in Atmospheric Dark mode is acceptable (or even desired for contrast), then `src/gameboy_hal.c` can remain unchanged.
3.  We will provide both options in our proposals.

---

## 5. Proposed Changes

### Proposal 5.1: Update `src/main.c` with Compile-Time Palette Switching

We will wrap the palette registers in `#ifdef USE_BLACK_FLOOR` block.

**File**: `dandy-gb/src/main.c`

```c
<<<<
    // Explicitly configure hardware palettes from our approved blueprint:
    // BGP = 0x1B (00 01 10 11): BKG Color 0 is Black (floor), 1 is Dark Gray (walls), 2 is Light Gray, 3 is White (text)
    BGP_REG = 0x1B;
    // OBP0/1 = 0xE0 (11 10 00 00): Sprite Color 0 is Transparent, 1 is White (body), 2 is Dark Gray, 3 is Black (outlines)
    OBP0_REG = 0xE0;
    OBP1_REG = 0xE0;
====
#ifdef USE_BLACK_FLOOR
    // Atmospheric Dark:
    // BGP = 0x1B (00 01 10 11): BKG Color 0 is Black (floor), 1 is Dark Gray (walls), 2 is Light Gray, 3 is White (text)
    BGP_REG = 0x1B;
    // OBP0/1 = 0xE0 (11 10 00 00): Sprite Color 0 is Transparent, 1 is White (body), 2 is Dark Gray, 3 is Black (outlines)
    OBP0_REG = 0xE0;
    OBP1_REG = 0xE0;
#else
    // Classic DMG (Default):
    // BGP = 0xE4 (11 10 01 00): BKG Color 0 is White (floor), 1 is Light Gray (walls/dots), 2 is Dark Gray, 3 is Black (text/HUD)
    BGP_REG = 0xE4;
    // OBP0/1 = 0xD8 (11 01 10 00): Sprite Color 0 is Transparent, 1 is Dark Gray (body), 2 is Light Gray (details), 3 is Black (outlines)
    OBP0_REG = 0xD8;
    OBP1_REG = 0xD8;
#endif
>>>>
```

---

### Proposal 5.2: Supporting the Compile-Time Flag in the `Makefile`

To make compilation and testing seamless, we should define `CFLAGS` in the `Makefile` and support an easy toggling variable `BLACK_FLOOR`.

**File**: `dandy-gb/Makefile`

```makefile
<<<<
# Source and Object Files
SRCS = $(SRC_DIR)/main.c $(SRC_DIR)/dandy_core.c $(SRC_DIR)/gameboy_hal.c
OBJS = $(OBJ_DIR)/main.o $(OBJ_DIR)/dandy_core.o $(OBJ_DIR)/gameboy_hal.o $(OBJ_DIR)/levels.o $(OBJ_DIR)/tiles.o

# Flags
# -Wa-l: Generate assembler list file
# -Wl-m: Generate linker map file
LCCFLAGS = -Wa-l -Wl-m -Wl-yo2
====
# Source and Object Files
SRCS = $(SRC_DIR)/main.c $(SRC_DIR)/dandy_core.c $(SRC_DIR)/gameboy_hal.c
OBJS = $(OBJ_DIR)/main.o $(OBJ_DIR)/dandy_core.o $(OBJ_DIR)/gameboy_hal.o $(OBJ_DIR)/levels.o $(OBJ_DIR)/tiles.o

# Compiler Flags
CFLAGS = -Wf--opt-code-size
ifeq ($(BLACK_FLOOR), 1)
    CFLAGS += -DUSE_BLACK_FLOOR
endif

# Linker Flags
# -Wa-l: Generate assembler list file
# -Wl-m: Generate linker map file
LCCFLAGS = -Wa-l -Wl-m -Wl-yo2
>>>>
```

And update the object compilation rule:

```makefile
<<<<
# Compile C source files
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	$(LCC) -Wf--opt-code-size -c -o $@ $<
====
# Compile C source files
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	$(LCC) $(CFLAGS) -c -o $@ $<
>>>>
```

This allows building the Atmospheric Dark ROM with:
```bash
make clean && make BLACK_FLOOR=1
```
And the Classic DMG ROM with:
```bash
make clean && make
```

---

### Proposal 5.3: (Optional) Consistent Dark HUD in `src/gameboy_hal.c`

If the team wants a **consistently dark HUD background** in both modes, we can apply this patch to `src/gameboy_hal.c` to use normal font tiles in Atmospheric Dark mode.

**File**: `dandy-gb/src/gameboy_hal.c`

```c
<<<<
/* Helper to draw a string using the inverted (light-on-dark) font tiles */
static void hal_draw_string_inverted(uint8_t x, uint8_t y, const char* str) {
    uint8_t i = 0;
    while (str[i] != '\0') {
        // Inverted font starts at index 160 in VRAM
        set_bkg_tile_xy(x + i, y, 160 + (str[i] - 32));
        i++;
    }
}
====
/* Helper to draw a string using the inverted (light-on-dark) font tiles */
static void hal_draw_string_inverted(uint8_t x, uint8_t y, const char* str) {
    uint8_t i = 0;
    while (str[i] != '\0') {
#ifdef USE_BLACK_FLOOR
        // Under USE_BLACK_FLOOR, normal font is already white-on-black (Index 3 on Index 0)
        set_bkg_tile_xy(x + i, y, str[i] - 32);
#else
        // Inverted font starts at index 160 in VRAM
        set_bkg_tile_xy(x + i, y, 160 + (str[i] - 32));
#endif
        i++;
    }
}
>>>>
```

And update the background fill in `hal_update_hud`:

```c
<<<<
void hal_update_hud(void) {
    char buf[10];
    uint8_t p = local_player_idx;
    
    // Fill the entire HUD scoreboard area (columns 0..19, rows 10..17)
    // with the inverted space tile (160), creating a solid dark background block.
    fill_bkg_rect(0, 10, 20, 8, 160);
====
void hal_update_hud(void) {
    char buf[10];
    uint8_t p = local_player_idx;
    
    // Fill the entire HUD scoreboard area (columns 0..19, rows 10..17)
    // creating a solid dark background block.
#ifdef USE_BLACK_FLOOR
    // Space tile 0 is Index 0 (Black) under USE_BLACK_FLOOR
    fill_bkg_rect(0, 10, 20, 8, 0);
#else
    // Inverted Space tile 160 is Index 3 (Black) under normal BGP
    fill_bkg_rect(0, 10, 20, 8, 160);
#endif
>>>>
```

---

## 6. Verification Method

To verify these changes:
1.  **Classic DMG Mode**:
    *   Build with: `make clean && make`
    *   Launch in emulator: `dandy.gb` (under `bin/`).
    *   Verify: Floor corridor tiles are White ( DMG light green/yellow). Sprites are dark gray/black. Scoreboard is Black background with White text.
2.  **Atmospheric Dark Mode**:
    *   Build with: `make clean && make BLACK_FLOOR=1`
    *   Launch in emulator: `dandy.gb` (under `bin/`).
    *   Verify: Floor corridor tiles are Black ( DMG darkest shade). Sprites have bright White bodies and Dark Gray details. Scoreboard is:
        *   Without Proposal 5.3: White background block with Black text.
        *   With Proposal 5.3: Black background block with White text.
3.  **Sprite Transparency**:
    *   Verify that sprites drawn on top of background floor details (like cracks/dots) correctly show the floor details behind the transparent parts (Color Index 0) of the sprite.
4.  **Emulator Tests**:
    *   Run `make test_emu` to ensure that game state initialization and player movement are unaffected by compilation and palette swaps.
