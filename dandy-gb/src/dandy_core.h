#ifndef DANDY_CORE_H
#define DANDY_CORE_H

#include <stdint.h>
#include <stdbool.h>

/* Game Constants */
#define TICKS_PER_MOVE  4
#define MAP_SIZE        1800 // 60 * 30
#define MAX_PLAYERS     4

/* Tile ID Constants */
#define TILE_SPACE       0
#define TILE_WALL        1
#define TILE_DOOR        2
#define TILE_UP          3
#define TILE_DOWN        4
#define TILE_KEY         5
#define TILE_FOOD        6
#define TILE_MONEY       7
#define TILE_BOMB        8
#define TILE_MONSTER1    9
#define TILE_MONSTER2    10
#define TILE_MONSTER3    11
#define TILE_HEART       12
#define TILE_GENERATOR1  13
#define TILE_GENERATOR2  14
#define TILE_GENERATOR3  15
#define TILE_ARROW       16
#define TILE_PLAYER1     24  // TILE_ARROW + 8
#define IS_PLAYER(tile)  ((tile) >= TILE_PLAYER1 && (tile) <= (TILE_PLAYER1 + 31))

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
extern const uint8_t dandy_num_levels;

/* Player State Arrays */
extern uint8_t player_x[MAX_PLAYERS];
extern uint8_t player_y[MAX_PLAYERS];
extern int16_t player_health[MAX_PLAYERS];
extern uint16_t player_score[MAX_PLAYERS];
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
extern void hal_clear_sprites(uint8_t vp_left, uint8_t vp_top);
extern void hal_set_sprite(uint8_t sprite_idx, uint8_t x, uint8_t y, uint8_t tile_id, uint8_t flags);
extern void hal_play_sound(uint8_t sound_id);

/* Retro Sound Effect IDs */
#define SOUND_SHOOT     0
#define SOUND_HIT       1
#define SOUND_FOOD      2
#define SOUND_BOMB      3
#define SOUND_KEY       4
#define SOUND_DIE       5
#define SOUND_WARP      6

#endif /* DANDY_CORE_H */
