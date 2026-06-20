#include <gb/gb.h>
#include <font.h>
#include "dandy_core.h"

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
    
    // Initialize the GBDK font system and load IBM font
    font_init();
    ibm_font = font_load(font_ibm);
    font_set(ibm_font);
    
    // Set up background map
    // We don't need sprites for this ASCII prototype since everything is background tiles!
    // Turn on Background display
    SHOW_BKG;
    
    DISPLAY_ON; // Turn screen back on
    
    // 2. Initialize Game Engine
    dandy_init();
    
    // 3. Main Game Loop (60 Hz)
    while (1) {
        // Read input and step game engine
        uint8_t buttons = get_joypad_buttons();
        dandy_step(buttons);
        
        // Redraw viewport if anything changed
        if (is_dirty) {
            dandy_draw_viewport();
            is_dirty = false;
        }
        
        // Synchronize with VBlank (frame rate limiter to 60fps)
        wait_vbl_done();
    }
}
