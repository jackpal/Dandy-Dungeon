# Handoff Report: Palette & Sprite Integration (Milestone 4)

This report summarizes the technical findings and recommendations for the GameBoy hardware palette and sprite transparency integration.

---

## 1. Observation

During the read-only investigation, the following files and code patterns were observed:

### A. Palette Register Initialization in `src/main.c`
In `dandy-gb/src/main.c` (lines 28-32), the hardware palettes are initialized as follows:
```c
28:     // BGP = 0x1B (00 01 10 11): BKG Color 0 is Black (floor), 1 is Dark Gray (walls), 2 is Light Gray, 3 is White (text)
29:     BGP_REG = 0x1B;
30:     // OBP0/1 = 0xE0 (11 10 00 00): Sprite Color 0 is Transparent, 1 is White (body), 2 is Dark Gray, 3 is Black (outlines)
31:     OBP0_REG = 0xE0;
32:     OBP1_REG = 0xE0;
```
This hardcodes the **Atmospheric Dark** mode palette.

### B. Sprite Settings in `src/gameboy_hal.c`
In `dandy-gb/src/gameboy_hal.c` (lines 107-123), the `hal_set_sprite` function maps tile IDs, moves sprites with the correct hardware coordinates offset `(8, 16)`, and applies sprite properties (OAM flags):
```c
107: void hal_set_sprite(uint8_t sprite_idx, uint8_t x, uint8_t y, uint8_t tile_id, uint8_t flags) {
...
118:     // GBDK hardware sprite coordinates are offset by (8, 16)
119:     move_sprite(sprite_idx, x + 8, y + 16);
120:     
121:     // Set sprite properties (OAM flags for flipping/palettes)
122:     set_sprite_prop(sprite_idx, flags);
123: }
```

### C. HUD Scoreboard Inverted Font and Background in `src/gameboy_hal.c`
In `dandy-gb/src/gameboy_hal.c` (lines 68-70), the scoreboard background is filled with inverted space (tile index `160`), which sets all pixels in that region to Color Index `3`:
```c
68:     // Fill the entire HUD scoreboard area (columns 0..19, rows 10..17)
69:     // with the inverted space tile (160), creating a solid dark background block.
70:     fill_bkg_rect(0, 10, 20, 8, 160);
```

### D. Compile Rules in `Makefile`
In `dandy-gb/Makefile` (lines 46-47), C compilation flags are hardcoded in the rule itself without a `CFLAGS` variable:
```makefile
46: $(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
47: 	$(LCC) -Wf--opt-code-size -c -o $@ $<
```

---

## 2. Logic Chain

1.  **Observation A** shows that `BGP_REG`, `OBP0_REG`, and `OBP1_REG` are hardcoded to the Atmospheric Dark palette (`0x1B` and `0xE0` respectively).
2.  To support compile-time toggling between **Classic DMG** and **Atmospheric Dark** using the `#ifdef USE_BLACK_FLOOR` macro, we must introduce conditional macro blocks in `src/main.c` to assign:
    *   Classic DMG (Default): `BGP_REG = 0xE4`, `OBP0_REG/OBP1_REG = 0xD8`.
    *   Atmospheric Dark: `BGP_REG = 0x1B`, `OBP0_REG/OBP1_REG = 0xE0`.
3.  **Observation D** indicates that the `Makefile` lacks a `CFLAGS` variable or support for conditional preprocessor defines (like `-DUSE_BLACK_FLOOR`). Adding a conditional block linked to a `BLACK_FLOOR` variable (e.g., `make BLACK_FLOOR=1`) allows clean, automated toggling during compilation.
4.  **Observation B** confirms that:
    *   Sprite positions are correctly offset by `(8, 16)`.
    *   Sprite properties are set via OAM.
    *   Because the two sprite palettes (`OBP0_REG` and `OBP1_REG`) are mapped to the exact same colors in both configurations, sprite color rendering is independent of which palette is chosen in OAM flags.
    *   GameBoy hardware natively handles Color Index `0` of sprites as transparent.
    *   **Therefore**, no changes are needed in `src/gameboy_hal.c` or any other file for sprite transparency or palette switching, making it a highly localized change.
5.  **Observation C** shows that the HUD uses the inverted font (tile index `160`).
    *   In Classic DMG, this makes the HUD background Black (Index `3` = Black) and text White (Index `0` = White), which is dark as intended.
    *   In Atmospheric Dark, this makes the HUD background White (Index `3` = White) and text Black (Index `0` = Black), creating a light scoreboard block.
    *   If the team wants a dark HUD in both modes, we can conditionally fill the background and draw text using the normal vs. inverted font in `src/gameboy_hal.c` (Proposal 5.3 in `analysis.md`). If the current white HUD is acceptable, no changes are needed in `src/gameboy_hal.c`.

---

## 3. Caveats

*   **HUD Visual Discrepancy**: Under Atmospheric Dark mode, the scoreboard background becomes White by default if we don't modify `src/gameboy_hal.c` (since the background palette is inverted, making Index `3` map to White). We have provided two options: Proposal 5.1 & 5.2 (keeps the original behavior, changing only `main.c` and `Makefile`), and Proposal 5.3 (adds a patch to `gameboy_hal.c` to keep the HUD Black in both modes).
*   **Asset Compiler Compatibility**: We assume the downscaling/graphics asset compiler correctly outputs sprite sheets where transparent areas map to Color Index `0`. If they map to another index, transparency will fail.

---

## 4. Conclusion

*   Configure GameBoy hardware palettes dynamically in `src/main.c` using an `#ifdef USE_BLACK_FLOOR` block.
*   Update the `Makefile` to introduce a `CFLAGS` variable and support a simple `BLACK_FLOOR=1` switch for builds.
*   Keep `src/gameboy_hal.c` unchanged unless the team explicitly prefers a dark HUD in Atmospheric Dark mode, in which case we should apply Proposal 5.3.
*   Sprite transparency is fully supported out-of-the-box by the hardware/HAL once the palette registers are set up correctly.

---

## 5. Verification Method

To independently verify the implementation:

1.  **Compile and Run Classic DMG**:
    ```bash
    make clean && make
    ```
    *   Inspect `bin/dandy.gb` in an emulator.
    *   **Pass Criteria**: Floor corridor tiles must be White. Sprites must render as dark silhouettes. The scoreboard at the bottom must have a solid black background with white text.
2.  **Compile and Run Atmospheric Dark**:
    ```bash
    make clean && make BLACK_FLOOR=1
    ```
    *   Inspect `bin/dandy.gb` in an emulator.
    *   **Pass Criteria**: Floor corridor tiles must be Black. Sprites must render with bright white bodies and dark gray details.
    *   *HUD Verification*:
        *   Without Proposal 5.3: Scoreboard has a White background with Black text.
        *   With Proposal 5.3: Scoreboard has a Black background with White text.
3.  **Sprite Transparency**:
    *   Walk the player over floor tiles with decorations/cracks. Verify that the floor details are visible behind the player sprite's transparent regions (e.g. between the arms/legs).
4.  **Automated Emulator Tests**:
    ```bash
    make test_emu
    ```
    *   Verify that the test suite compiles and all tests pass successfully, proving that palette switching has not caused regressions in game logic.
