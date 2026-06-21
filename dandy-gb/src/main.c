#include <gb/gb.h>
#include <gbdk/font.h>
#include "dandy_core.h"
#ifdef USE_BLACK_FLOOR
#include "tiles_dark.h"
#else
#include "tiles_light.h"
#endif


/* Maps GBDK joypad bits to our core button masks */
uint8_t get_joypad_buttons(void) {
    uint8_t joy = joypad();
    uint8_t buttons = 0;
    
    if (joy & J_LEFT)   buttons |= BUTTON_LEFT;
    if (joy & J_RIGHT)  buttons |= BUTTON_RIGHT;
    if (joy & J_UP)     buttons |= BUTTON_UP;
    if (joy & J_DOWN)   buttons |= BUTTON_DOWN;
    if (joy & J_A)      buttons |= BUTTON_FIRE; // Button A fires arrow
    if (joy & J_B)      buttons |= BUTTON_BOMB; // Button B uses smart bomb
    
    return buttons;
}

void main(void) {
    font_t ibm_font;
    
    // 1. Initialize GameBoy hardware
    DISPLAY_OFF; // Turn off screen during VRAM modifications
    
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


    
    // Initialize the GBDK font system and load IBM font
    font_init();
    ibm_font = font_load(font_ibm);
    font_set(ibm_font);
    
    // Load custom game tiles starting at background and sprite tile index 128 (0x80)
#ifdef USE_BLACK_FLOOR
    set_bkg_data(128, DANDY_NUM_TILES, dandy_tiles_dark);
    set_sprite_data(128, DANDY_NUM_TILES, dandy_tiles_dark);
#else
    set_bkg_data(128, DANDY_NUM_TILES, dandy_tiles_light);
    set_sprite_data(128, DANDY_NUM_TILES, dandy_tiles_light);
#endif

    
    // Programmatically generate the inverted font in background VRAM at index 160 (0xA0)
    // Read each of the 96 standard font tiles, invert their 2bpp bytes, and save them at 160+i.
    // This provides a light-on-dark font for the scoreboard with zero additional ROM storage!
    {
        unsigned char tile_buf[16];
        for (uint16_t i = 0; i < 96; ++i) {
            get_bkg_data(i, 1, tile_buf);
            for (uint8_t j = 0; j < 16; ++j) {
                tile_buf[j] = ~tile_buf[j];
            }
            set_bkg_data(160 + i, 1, tile_buf);
        }
    }
    
    // Set up background map and hardware sprites
    SHOW_BKG;
    SHOW_SPRITES;
    
    DISPLAY_ON; // Turn screen back on
    
    // 2. Initialize Game Engine
    dandy_init();
    
    // 3. Main Game Loop (60 Hz)
    while (1) {
        // Read input and step game engine
        uint8_t inputs[MAX_PLAYERS] = {0, 0, 0, 0};
        inputs[0] = get_joypad_buttons();
        dandy_step(inputs);
        
        // Redraw viewport if anything changed
        if (is_dirty) {
            dandy_draw_viewport(local_player_idx);
            is_dirty = false;
        }
        
        // Synchronize with VBlank (frame rate limiter to 60fps)
        wait_vbl_done();
    }
}
