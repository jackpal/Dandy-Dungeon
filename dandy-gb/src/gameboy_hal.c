#include "dandy_core.h"
#include <gb/gb.h>
#include <font.h>

/* ASCII translation table for tiles.
   Maps tile IDs to ASCII character codes.
*/
const uint8_t tile_to_ascii[32] = {
    [TILE_SPACE]      = ' ',
    [TILE_WALL]       = '*',
    [TILE_DOOR]       = 'D',
    [TILE_UP]         = 'U',
    [TILE_DOWN]       = 'v',
    [TILE_KEY]        = 'K',
    [TILE_FOOD]       = 'F',
    [TILE_MONEY]      = '$',
    [TILE_BOMB]       = 'B',
    [TILE_MONSTER1]   = '1',
    [TILE_MONSTER2]   = '2',
    [TILE_MONSTER3]   = '3',
    [TILE_HEART]      = 'H',
    [TILE_GENERATOR1] = 'g',
    [TILE_GENERATOR2] = 'o',
    [TILE_GENERATOR3] = 'q',
    
    // Arrows in 8 directions (Up, Up-Right, Right, Down-Right, Down, Down-Left, Left, Up-Left)
    [TILE_ARROW + 0]  = '^',
    [TILE_ARROW + 1]  = '/',
    [TILE_ARROW + 2]  = '>',
    [TILE_ARROW + 3]  = '\\',
    [TILE_ARROW + 4]  = 'v',
    [TILE_ARROW + 5]  = '/',
    [TILE_ARROW + 6]  = '<',
    [TILE_ARROW + 7]  = '\\',
    
    // Player in 8 directions (Up, Up-Right, Right, Down-Right, Down, Down-Left, Left, Up-Left)
    [TILE_PLAYER1 + 0] = '^',
    [TILE_PLAYER1 + 1] = '/',
    [TILE_PLAYER1 + 2] = '>',
    [TILE_PLAYER1 + 3] = '\\',
    [TILE_PLAYER1 + 4] = 'v',
    [TILE_PLAYER1 + 5] = '/',
    [TILE_PLAYER1 + 6] = '<',
    [TILE_PLAYER1 + 7] = '\\'
};

/* Tiny helper to draw a string directly to VRAM background map */
void hal_draw_string(uint8_t x, uint8_t y, const char* str) {
    uint8_t i = 0;
    while (str[i] != '\0') {
        // GBDK font tiles are shifted by 32 (ASCII space is tile 0)
        set_bkg_tile_xy(x + i, y, str[i] - 32);
        i++;
    }
}

/* Tiny custom itoa to avoid sprintf bloat */
static void u32_to_str(uint32_t val, char* buf, uint8_t digits) {
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
    uint8_t ascii = tile_to_ascii[tile_id];
    if (ascii == 0) ascii = ' ';
    
    // In our ASCII prototype, player and arrow directions are represented by their characters.
    // If it's a player tile, we want to make it stand out!
    // But since this is text, it just draws the character.
    // Later, when we have custom tiles, tile_id will map directly to the 8x8 sprite indices.
    
    // Viewport is at top of screen (y: 0..9)
    set_bkg_tile_xy(x, y, ascii - 32);
}

void hal_update_hud(void) {
    char buf[10];
    uint8_t p = local_player_idx;
    
    // Row 10: Separator border
    hal_draw_string(0, 10, "--------------------");
    
    // Row 11: Score
    hal_draw_string(1, 11, "SCORE: ");
    u32_to_str(player_score[p], buf, 6);
    hal_draw_string(8, 11, buf);
    
    // Row 12: Health
    hal_draw_string(1, 12, "HP:    ");
    s16_to_str(player_health[p], buf, 3);
    hal_draw_string(8, 12, buf);
    
    // Row 13: Bombs & Keys
    hal_draw_string(1, 13, "BOMBS: ");
    u32_to_str(player_bombs[p], buf, 2);
    hal_draw_string(8, 13, buf);
    
    hal_draw_string(11, 13, "KEYS: ");
    u32_to_str(player_keys[p], buf, 2);
    hal_draw_string(17, 13, buf);
    
    // Row 14: Level
    hal_draw_string(1, 14, "LEVEL: ");
    u32_to_str(current_level + 1, buf, 2);
    hal_draw_string(8, 14, buf);
    
    // Row 15-17: Controls / Info
    hal_draw_string(1, 16, "DANDY GB PROTOTYPE");
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
    
    // Resolve tile_id to ASCII character for our text font representation
    uint8_t ascii = tile_to_ascii[tile_id];
    if (ascii == 0) ascii = ' ';
    
    // Font tiles are shifted by 32 in VRAM
    set_sprite_tile(sprite_idx, ascii - 32);
    
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
