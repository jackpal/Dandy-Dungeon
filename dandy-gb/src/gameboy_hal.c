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

void hal_update_hud(uint32_t score, int16_t health, uint8_t bombs, uint8_t keys) {
    char buf[10];
    
    // Clear HUD area once if needed, or just overwrite.
    // HUD is rows 10..17. We'll draw a nice border and text.
    
    // Row 10: Separator border
    // "--------------------"
    // GBDK font '-' is ASCII 45 -> tile 13
    // We only need to draw this once on level load, but drawing it is cheap.
    hal_draw_string(0, 10, "--------------------");
    
    // Row 11: Score
    // "SCORE: 000000"
    hal_draw_string(1, 11, "SCORE: ");
    u32_to_str(score, buf, 6);
    hal_draw_string(8, 11, buf);
    
    // Row 12: Health
    // "HP:    100"
    hal_draw_string(1, 12, "HP:    ");
    s16_to_str(health, buf, 3);
    hal_draw_string(8, 12, buf);
    
    // Row 13: Bombs & Keys
    // "BOMBS: 00  KEYS: 00"
    hal_draw_string(1, 13, "BOMBS: ");
    u32_to_str(bombs, buf, 2);
    hal_draw_string(8, 13, buf);
    
    hal_draw_string(11, 13, "KEYS: ");
    u32_to_str(keys, buf, 2);
    hal_draw_string(17, 13, buf);
    
    // Row 14: Level
    // "LEVEL: 01"
    hal_draw_string(1, 14, "LEVEL: ");
    u32_to_str(current_level + 1, buf, 2);
    hal_draw_string(8, 14, buf);
    
    // Row 15-17: Controls / Info
    hal_draw_string(1, 16, "DANDY GB PROTOTYPE");
}
