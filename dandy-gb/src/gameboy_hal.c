#include "dandy_core.h"
#include <gb/gb.h>
#include <gbdk/font.h>



/* Tiny helper to draw a string directly to VRAM background map */
void hal_draw_string(uint8_t x, uint8_t y, const char* str) {
    uint8_t i = 0;
    while (str[i] != '\0') {
        // GBDK font tiles are shifted by 32 (ASCII space is tile 0)
        set_bkg_tile_xy(x + i, y, str[i] - 32);
        i++;
    }
}

/* Helper to draw a string using the inverted (light-on-dark) font tiles */
static void hal_draw_string_inverted(uint8_t x, uint8_t y, const char* str) {
    uint8_t i = 0;
    while (str[i] != '\0') {
        // Inverted font starts at index 160 in VRAM
        set_bkg_tile_xy(x + i, y, 160 + (str[i] - 32));
        i++;
    }
}

/* Tiny custom itoa to avoid sprintf bloat (16-bit to save ROM space) */
static void u16_to_str(uint16_t val, char* buf, uint8_t digits) {
    for (int8_t i = digits - 1; i >= 0; --i) {
        buf[i] = '0' + (val % 10);
        val /= 10;
    }
    buf[digits] = '\0';
}

static void s16_to_str(int16_t val, char* buf, uint8_t digits) {
    bool neg = false;
    if (val < 0) {
        neg = true;
        val = -val;
    }
    for (int8_t i = digits - 1; i >= 0; --i) {
        buf[i] = '0' + (val % 10);
        val /= 10;
    }
    if (neg && digits > 0) {
        buf[0] = '-';
    }
    buf[digits] = '\0';
}

/* HAL Implementations */

void hal_draw_tile(uint8_t x, uint8_t y, uint8_t tile_id) {
    // Map player 2, 3, 4 tile IDs back to Player 1's range (24..31)
    if (tile_id >= TILE_PLAYER1 && tile_id <= TILE_PLAYER1 + 31) {
        tile_id = TILE_PLAYER1 + ((tile_id - TILE_PLAYER1) & 7);
    }
    
    // Draw custom background tile loaded starting at index 128 (0x80)
    set_bkg_tile_xy(x, y, 128 + tile_id);
}

void hal_update_hud(void) {
    char buf[10];
    uint8_t p = local_player_idx;
    
    // Fill the entire HUD scoreboard area (columns 0..19, rows 10..17)
    // with the inverted space tile (160), creating a solid dark background block.
    fill_bkg_rect(0, 10, 20, 8, 160);
    
    // Draw scoreboard elements using the inverted light-on-dark font
    // Row 11: Score
    hal_draw_string_inverted(1, 11, "SCORE: ");
    u16_to_str(player_score[p], buf, 6);
    hal_draw_string_inverted(8, 11, buf);
    
    // Row 12: Health
    hal_draw_string_inverted(1, 12, "HP:    ");
    s16_to_str(player_health[p], buf, 3);
    hal_draw_string_inverted(8, 12, buf);
    
    // Row 13: Bombs & Keys
    hal_draw_string_inverted(1, 13, "BOMBS: ");
    u16_to_str(player_bombs[p], buf, 2);
    hal_draw_string_inverted(8, 13, buf);
    
    hal_draw_string_inverted(11, 13, "KEYS: ");
    u16_to_str(player_keys[p], buf, 2);
    hal_draw_string_inverted(17, 13, buf);
    
    // Row 14: Level
    hal_draw_string_inverted(1, 14, "LEVEL: ");
    u16_to_str(current_level + 1, buf, 2);
    hal_draw_string_inverted(8, 14, buf);
}

void hal_clear_sprites(uint8_t vp_left, uint8_t vp_top) {
    (void)vp_left;
    (void)vp_top;
    // Hide all 40 hardware sprites by moving them off-screen (0, 0)
    for (uint8_t i = 0; i < 40; ++i) {
        move_sprite(i, 0, 0);
    }
}

void hal_set_sprite(uint8_t sprite_idx, uint8_t x, uint8_t y, uint8_t tile_id, uint8_t flags) {
    if (sprite_idx >= 40) return;
    
    // Map player 2, 3, 4 tile IDs back to Player 1's range (24..31)
    if (tile_id >= TILE_PLAYER1 && tile_id <= TILE_PLAYER1 + 31) {
        tile_id = TILE_PLAYER1 + ((tile_id - TILE_PLAYER1) & 7);
    }
    
    // Use custom sprite tile loaded starting at index 128 (0x80)
    set_sprite_tile(sprite_idx, 128 + tile_id);
    
    // GBDK hardware sprite coordinates are offset by (8, 16)
    move_sprite(sprite_idx, x + 8, y + 16);
    
    // Set sprite properties (OAM flags for flipping/palettes)
    set_sprite_prop(sprite_idx, flags);
}

static bool sound_initialized = false;

void hal_play_sound(uint8_t sound_id) {
    if (!sound_initialized) {
        NR52_REG = 0x80; // Turn on Sound chip
        NR50_REG = 0x77; // Max volume on left/right channels
        NR51_REG = 0xFF; // Route all 4 channels to left/right speakers
        sound_initialized = true;
    }
    
    switch (sound_id) {
        case SOUND_SHOOT:
            NR10_REG = 0x1E;
            NR11_REG = 0x80;
            NR12_REG = 0xF3;
            NR13_REG = 0x00;
            NR14_REG = 0xC7;
            break;
        case SOUND_HIT:
            NR21_REG = 0x80;
            NR22_REG = 0xF1;
            NR23_REG = 0x80;
            NR24_REG = 0xC4;
            break;
        case SOUND_FOOD:
            NR10_REG = 0x16;
            NR11_REG = 0x80;
            NR12_REG = 0xF2;
            NR13_REG = 0x00;
            NR14_REG = 0xC6;
            break;
        case SOUND_BOMB:
            NR41_REG = 0x1F;
            NR42_REG = 0xF7;
            NR43_REG = 0x57;
            NR44_REG = 0xC0;
            break;
        case SOUND_KEY:
            NR21_REG = 0x80;
            NR22_REG = 0xF2;
            NR23_REG = 0xF0;
            NR24_REG = 0xC6;
            break;
        case SOUND_DIE:
            NR10_REG = 0x3F;
            NR11_REG = 0x80;
            NR12_REG = 0xF5;
            NR13_REG = 0x50;
            NR14_REG = 0xC3;
            break;
        case SOUND_WARP:
            NR10_REG = 0x0E;
            NR11_REG = 0x40;
            NR12_REG = 0xF3;
            NR13_REG = 0x00;
            NR14_REG = 0xC7;
            break;
    }
}
