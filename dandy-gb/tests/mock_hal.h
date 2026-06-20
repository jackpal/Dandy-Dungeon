#ifndef MOCK_HAL_H
#define MOCK_HAL_H

#include <stdint.h>
#include <stdbool.h>

/* Standard GameBoy HAL function signatures required by the engine */
void hal_draw_tile(uint8_t x, uint8_t y, uint8_t tile_id);
void hal_update_hud(void);
void hal_clear_sprites(uint8_t vp_left, uint8_t vp_top);
void hal_set_sprite(uint8_t sprite_idx, uint8_t x, uint8_t y, uint8_t tile_id, uint8_t flags);
void hal_play_sound(uint8_t sound_id);

/* Mock Control & Query Extensions (Exposed to Python Test Runner) */
void mock_clear_buffers(void);

int mock_get_draw_count(void);
void mock_get_draw(int idx, uint8_t* x, uint8_t* y, uint8_t* tile_id);

int mock_get_sound_count(void);
uint8_t mock_get_sound(int idx);

void mock_get_sprite(uint8_t sprite_idx, uint8_t* x, uint8_t* y, uint8_t* tile_id, uint8_t* flags);
bool mock_is_sprite_active(uint8_t sprite_idx);
bool mock_get_sprite_oob_error(void);

int mock_get_hud_update_count(void);
void mock_get_camera(uint8_t* cam_x, uint8_t* cam_y);

#endif /* MOCK_HAL_H */
