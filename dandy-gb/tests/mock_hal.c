#include "mock_hal.h"
#include <string.h>

#define MAX_MOCK_DRAWS 2048
#define MAX_MOCK_SOUNDS 256

typedef struct {
    uint8_t x;
    uint8_t y;
    uint8_t tile_id;
} DrawCall;

typedef struct {
    uint8_t x;
    uint8_t y;
    uint8_t tile_id;
    uint8_t flags;
    bool active;
} SpriteState;

static DrawCall mock_draws[MAX_MOCK_DRAWS];
static int mock_draw_count = 0;

static uint8_t mock_sounds[MAX_MOCK_SOUNDS];
static int mock_sound_count = 0;

static SpriteState mock_sprites[40];
static int mock_hud_update_count = 0;

static uint8_t mock_camera_x = 0;
static uint8_t mock_camera_y = 0;
static bool mock_sprite_oob_error = false;

/* --- Game Engine HAL Implementation --- */

void hal_draw_tile(uint8_t x, uint8_t y, uint8_t tile_id) {
    if (mock_draw_count < MAX_MOCK_DRAWS) {
        mock_draws[mock_draw_count].x = x;
        mock_draws[mock_draw_count].y = y;
        mock_draws[mock_draw_count].tile_id = tile_id;
        mock_draw_count++;
    }
}

void hal_update_hud(void) {
    mock_hud_update_count++;
}

void hal_clear_sprites(uint8_t vp_left, uint8_t vp_top) {
    mock_camera_x = vp_left;
    mock_camera_y = vp_top;
    for (int i = 0; i < 40; ++i) {
        mock_sprites[i].active = false;
    }
}

void hal_set_sprite(uint8_t sprite_idx, uint8_t x, uint8_t y, uint8_t tile_id, uint8_t flags) {
    if (sprite_idx < 40) {
        mock_sprites[sprite_idx].x = x;
        mock_sprites[sprite_idx].y = y;
        mock_sprites[sprite_idx].tile_id = tile_id;
        mock_sprites[sprite_idx].flags = flags;
        mock_sprites[sprite_idx].active = true;
    } else {
        mock_sprite_oob_error = true;
    }
}

void hal_play_sound(uint8_t sound_id) {
    if (mock_sound_count < MAX_MOCK_SOUNDS) {
        mock_sounds[mock_sound_count] = sound_id;
        mock_sound_count++;
    }
}

/* --- Mock Query Extensions --- */

void mock_clear_buffers(void) {
    mock_sprite_oob_error = false;
    mock_draw_count = 0;
    mock_sound_count = 0;
    mock_hud_update_count = 0;
    mock_camera_x = 0;
    mock_camera_y = 0;
    for (int i = 0; i < 40; ++i) {
        mock_sprites[i].x = 0;
        mock_sprites[i].y = 0;
        mock_sprites[i].tile_id = 0;
        mock_sprites[i].flags = 0;
        mock_sprites[i].active = false;
    }
}

int mock_get_draw_count(void) {
    return mock_draw_count;
}

void mock_get_draw(int idx, uint8_t* x, uint8_t* y, uint8_t* tile_id) {
    if (idx >= 0 && idx < mock_draw_count) {
        if (x) *x = mock_draws[idx].x;
        if (y) *y = mock_draws[idx].y;
        if (tile_id) *tile_id = mock_draws[idx].tile_id;
    } else {
        if (x) *x = 0;
        if (y) *y = 0;
        if (tile_id) *tile_id = 0;
    }
}

int mock_get_sound_count(void) {
    return mock_sound_count;
}

uint8_t mock_get_sound(int idx) {
    if (idx >= 0 && idx < mock_sound_count) {
        return mock_sounds[idx];
    }
    return 0xFF;
}

void mock_get_sprite(uint8_t sprite_idx, uint8_t* x, uint8_t* y, uint8_t* tile_id, uint8_t* flags) {
    if (sprite_idx < 40) {
        if (x) *x = mock_sprites[sprite_idx].x;
        if (y) *y = mock_sprites[sprite_idx].y;
        if (tile_id) *tile_id = mock_sprites[sprite_idx].tile_id;
        if (flags) *flags = mock_sprites[sprite_idx].flags;
    } else {
        if (x) *x = 0;
        if (y) *y = 0;
        if (tile_id) *tile_id = 0;
        if (flags) *flags = 0;
    }
}

bool mock_is_sprite_active(uint8_t sprite_idx) {
    if (sprite_idx < 40) {
        return mock_sprites[sprite_idx].active;
    }
    return false;
}

int mock_get_hud_update_count(void) {
    return mock_hud_update_count;
}

void mock_get_camera(uint8_t* cam_x, uint8_t* cam_y) {
    if (cam_x) *cam_x = mock_camera_x;
    if (cam_y) *cam_y = mock_camera_y;
}

bool mock_get_sprite_oob_error(void) {
    return mock_sprite_oob_error;
}
