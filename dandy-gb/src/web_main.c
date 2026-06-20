#include "dandy_core.h"
#include <emscripten.h>

// Define JavaScript hooks directly in C using EM_JS
// This creates seamless bindings without needing custom library link flags
EM_JS(void, js_draw_tile, (uint8_t player_idx, uint8_t x, uint8_t y, uint8_t tile_id), {
    if (window.jsDrawTile) {
        window.jsDrawTile(player_idx, x, y, tile_id);
    }
});

EM_JS(void, js_update_hud, (uint8_t player_idx, uint32_t score, int16_t health, uint8_t bombs, uint8_t keys), {
    if (window.jsUpdateHud) {
        window.jsUpdateHud(player_idx, score, health, bombs, keys);
    }
});

// Keep track of which player's viewport is currently rendering
static uint8_t rendering_player_idx = 0;

// Implement HAL functions required by dandy_core.h
void hal_draw_tile(uint8_t x, uint8_t y, uint8_t tile_id) {
    js_draw_tile(rendering_player_idx, x, y, tile_id);
}

void hal_update_hud(void) {
    for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
        if (player_joined[p]) {
            js_update_hud(p, player_score[p], player_health[p], player_bombs[p], player_keys[p]);
        }
    }
}

// Exported WebAssembly API for the JS frontend
EMSCRIPTEN_KEEPALIVE
void web_init(void) {
    dandy_init(); // Initializes with only Player 1 joined
    local_player_idx = 0;
    dandy_load_level(current_level);
}

EMSCRIPTEN_KEEPALIVE
void web_step(uint8_t p1_input, uint8_t p2_input, uint8_t p3_input, uint8_t p4_input) {
    uint8_t inputs[MAX_PLAYERS];
    inputs[0] = p1_input;
    inputs[1] = p2_input;
    inputs[2] = p3_input;
    inputs[3] = p4_input;
    dandy_step(inputs);
}

EMSCRIPTEN_KEEPALIVE
void web_draw_viewports(void) {
    for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
        if (player_joined[p]) {
            rendering_player_idx = p;
            dandy_draw_viewport(p);
        }
    }
}

EMSCRIPTEN_KEEPALIVE
uint8_t web_get_current_level(void) {
    return current_level;
}

EMSCRIPTEN_KEEPALIVE
uint8_t web_get_num_players(void) {
    uint8_t count = 0;
    for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
        if (player_joined[p]) count++;
    }
    return count;
}

EMSCRIPTEN_KEEPALIVE
void web_join_player(uint8_t p_idx) {
    dandy_join_player(p_idx);
}

EMSCRIPTEN_KEEPALIVE
bool web_is_player_joined(uint8_t p_idx) {
    return dandy_is_player_joined(p_idx);
}
