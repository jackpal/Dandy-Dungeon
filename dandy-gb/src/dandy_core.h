#ifndef DANDY_CORE_H
#define DANDY_CORE_H

#include <stdint.h>
#include <stdbool.h>

/* Game Constants */
#define TICKS_PER_MOVE  4
#define MAP_SIZE        1800 // 60 * 30

/* Button Masks (Input abstraction) */
#define BUTTON_LEFT   (1 << 0)
#define BUTTON_RIGHT  (1 << 1)
#define BUTTON_UP     (1 << 2)
#define BUTTON_DOWN   (1 << 3)
#define BUTTON_FIRE   (1 << 4)
#define BUTTON_BOMB   (1 << 5)

/* Game State Globals (extern) */
extern uint8_t dandy_map[MAP_SIZE];
extern uint8_t current_level;
extern uint8_t monster_rotor;

extern uint8_t player_x;
extern uint8_t player_y;
extern int16_t player_health;
extern uint32_t player_score;
extern uint8_t player_bombs;
extern uint8_t player_keys;
extern int8_t player_dir;

extern uint8_t arrow_x;
extern uint8_t arrow_y;
extern int8_t arrow_dir; // -1 if inactive

extern uint8_t player_move_timer;
extern bool is_dirty; // Set to true when screen needs redraw

/* Core Functions */
void dandy_init(void);
void dandy_step(uint8_t buttons);
void dandy_load_level(uint8_t level_idx);
void dandy_draw_viewport(void);

/* Helper functions that core needs from HAL */
// These must be implemented by the platform-specific HAL (e.g., gameboy_hal.c)
extern void hal_draw_tile(uint8_t x, uint8_t y, uint8_t tile_id);
extern void hal_update_hud(uint32_t score, int16_t health, uint8_t bombs, uint8_t keys);

#endif /* DANDY_CORE_H */
