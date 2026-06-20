#ifndef DANDY_CORE_H
#define DANDY_CORE_H

#include <stdint.h>
#include <stdbool.h>

/* Game Constants */
#define TICKS_PER_MOVE  4
#define MAP_SIZE        1800 // 60 * 30
#define MAX_PLAYERS     4

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
extern bool player_joined[MAX_PLAYERS];
extern uint8_t local_player_idx;

/* Player State Arrays */
extern uint8_t player_x[MAX_PLAYERS];
extern uint8_t player_y[MAX_PLAYERS];
extern int16_t player_health[MAX_PLAYERS];
extern uint32_t player_score[MAX_PLAYERS];
extern uint8_t player_bombs[MAX_PLAYERS];
extern uint8_t player_keys[MAX_PLAYERS];
extern int8_t player_dir[MAX_PLAYERS];
extern uint8_t player_move_timer[MAX_PLAYERS];

extern uint8_t arrow_x[MAX_PLAYERS];
extern uint8_t arrow_y[MAX_PLAYERS];
extern int8_t arrow_dir[MAX_PLAYERS]; // -1 if inactive

extern bool is_dirty; // Set to true when screen needs redraw

/* Core Functions */
void dandy_init(void);
void dandy_step(const uint8_t player_inputs[MAX_PLAYERS]);
void dandy_load_level(uint8_t level_idx);
void dandy_draw_viewport(uint8_t local_p_idx);
void dandy_join_player(uint8_t p_idx);
bool dandy_is_player_joined(uint8_t p_idx);

/* Helper functions that core needs from HAL */
// These must be implemented by the platform-specific HAL (e.g., gameboy_hal.c)
extern void hal_draw_tile(uint8_t x, uint8_t y, uint8_t tile_id);
extern void hal_update_hud(void);

#endif /* DANDY_CORE_H */
