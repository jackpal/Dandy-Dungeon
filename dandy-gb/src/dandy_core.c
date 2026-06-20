#include "dandy_core.h"
#include "levels.h"
#include <string.h>

/* Retro-optimized Lookup Table for row offsets: y * 60 */
const uint16_t row_offsets[DANDY_LEVEL_HEIGHT] = {
    0, 60, 120, 180, 240, 300, 360, 420, 480, 540,
    600, 660, 720, 780, 840, 900, 960, 1020, 1080, 1140,
    1200, 1260, 1320, 1380, 1440, 1500, 1560, 1620, 1680, 1740
};

/* Direction Deltas (8-way)
   Directions: 0=Up, 1=Up-Right, 2=Right, 3=Down-Right, 4=Down, 5=Down-Left, 6=Left, 7=Up-Left
*/
const int8_t dir_delta_x[8] = { 0,  1, 1, 1, 0, -1, -1, -1 };
const int8_t dir_delta_y[8] = { -1, -1, 0, 1, 1,  1,  0, -1 };

/* Search order for sliding around obstacles */
const int8_t search_order[3] = { 0, -1, 1 };

/* Maps button bitmask (Down, Up, Right, Left) to direction index.
   Buttons are: Bit 0=Left, Bit 1=Right, Bit 2=Up, Bit 3=Down
*/
const int8_t buttons_to_dir[16] = {
    -1, // 0000 -> None
     6, // 0001 -> Left
     2, // 0010 -> Right
    -1, // 0011 -> Left+Right (Invalid)
     0, // 0100 -> Up
     7, // 0101 -> Up+Left
     1, // 0110 -> Up+Right
     0, // 0111 -> Up+Right+Left (Up)
     4, // 1000 -> Down
     5, // 1001 -> Down+Left
     3, // 1010 -> Down+Right
     4, // 1011 -> Down+Right+Left (Down)
    -1, // 1100 -> Down+Up (Invalid)
     6, // 1101 -> Down+Up+Left (Left)
     2, // 1110 -> Down+Up+Right (Right)
    -1  // 1111 -> All (Invalid)
};

/* Monster pathfinding direction lookup based on dy, dx
   dy in [-1, 0, 1] mapped to index [0, 1, 2]
   dx in [-1, 0, 1] mapped to index [0, 1, 2]
*/
const int8_t delta_to_dir[3][3] = {
    { 7, 0, 1 }, // dy = -1 (Up) -> [Up-Left, Up, Up-Right]
    { 6, 0, 2 }, // dy =  0      -> [Left,   Up, Right]    (Wait, center is 0 but shouldn't happen)
    { 5, 4, 3 }  // dy =  1 (Down)-> [Down-Left, Down, Down-Right]
};

/* Game State Globals */
uint8_t dandy_map[MAP_SIZE];
uint8_t current_level;
uint8_t monster_rotor;

uint8_t player_x;
uint8_t player_y;
int16_t player_health;
uint32_t player_score;
uint8_t player_bombs;
uint8_t player_keys;
int8_t player_dir;

uint8_t arrow_x;
uint8_t arrow_y;
int8_t arrow_dir;

uint8_t player_move_timer;
bool is_dirty;

/* Macro to check if a tile is the player (any of the 8 directions) */
#define IS_PLAYER(tile) ((tile) >= TILE_PLAYER1 && (tile) <= (TILE_PLAYER1 + 7))

/* Private function declarations */
static void do_buttons(uint8_t buttons);
static void move_arrow(void);
static void move_monsters(void);
static bool move_player(uint8_t dir);
static void do_bomb(void);
static void set_player_start_position(void);
static void next_level(void);
static void end_game(void);
static void iterative_flood_fill(uint8_t start_x, uint8_t start_y, uint8_t oc, uint8_t nc);
static int16_t clamp(int16_t val, int16_t min, int16_t max);
static int8_t to_delta(int16_t a, int16_t b);

/* Parallel stack arrays for non-recursive flood fill (128 bytes total) */
#define FLOOD_STACK_SIZE 64
static uint8_t flood_stack_x[FLOOD_STACK_SIZE];
static uint8_t flood_stack_y[FLOOD_STACK_SIZE];
static int8_t flood_stack_ptr = 0;

static void flood_push(uint8_t x, uint8_t y) {
    if (flood_stack_ptr < FLOOD_STACK_SIZE) {
        flood_stack_x[flood_stack_ptr] = x;
        flood_stack_y[flood_stack_ptr] = y;
        flood_stack_ptr++;
    }
}

/* Core Engine Implementation */

void dandy_init(void) {
    current_level = 0;
    player_score = 0;
    player_health = 100;
    player_bombs = 0;
    player_keys = 0;
    player_dir = 0;
    monster_rotor = 0;
    arrow_dir = -1;
    player_move_timer = 0;
    
    dandy_load_level(current_level);
}

void dandy_load_level(uint8_t level_idx) {
    // Copy level data from ROM to RAM map
    memcpy(dandy_map, dandy_levels[level_idx], MAP_SIZE);
    
    set_player_start_position();
    arrow_dir = -1;
    is_dirty = true;
}

void dandy_step(uint8_t buttons) {
    do_buttons(buttons);
    move_arrow();
    move_monsters();
    
    // Update HUD via HAL
    hal_update_hud(player_score, player_health, player_bombs, player_keys);
    
    if (player_health <= 0) {
        end_game();
    }
}

void dandy_draw_viewport(void) {
    int16_t vp_left = clamp((int16_t)player_x - 10, 0, DANDY_LEVEL_WIDTH - 20);
    int16_t vp_top = clamp((int16_t)player_y - 5, 0, DANDY_LEVEL_HEIGHT - 10);
    
    for (uint8_t sy = 0; sy < 10; ++sy) {
        uint16_t row_offset = row_offsets[vp_top + sy];
        for (uint8_t sx = 0; sx < 20; ++sx) {
            uint8_t tile = dandy_map[row_offset + (vp_left + sx)];
            hal_draw_tile(sx, sy, tile);
        }
    }
}

static void set_player_start_position(void) {
    // Find the first TILE_UP ('u')
    uint16_t up_pos = 0xFFFF;
    for (uint16_t i = 0; i < MAP_SIZE; ++i) {
        if (dandy_map[i] == TILE_UP) {
            up_pos = i;
            break;
        }
    }
    
    if (up_pos != 0xFFFF) {
        // Position player one tile above the ladder
        player_x = up_pos % DANDY_LEVEL_WIDTH;
        player_y = (up_pos / DANDY_LEVEL_WIDTH) - 1;
    } else {
        // Fallback
        player_x = 1;
        player_y = 1;
    }
    
    dandy_map[row_offsets[player_y] + player_x] = TILE_PLAYER1 + player_dir;
}

static void next_level(void) {
    if (current_level < DANDY_NUM_LEVELS - 1) {
        current_level++;
    }
    dandy_load_level(current_level);
}

static void end_game(void) {
    current_level = 0;
    player_health = 100;
    player_keys = 0;
    player_bombs = 0;
    player_score = 0;
    player_dir = 0;
    dandy_load_level(current_level);
}

static void do_buttons(uint8_t buttons) {
    static uint8_t old_buttons = 0;
    uint8_t delta_down = buttons & ~old_buttons;
    old_buttons = buttons;
    
    // Smart Bomb (Edge triggered)
    if (delta_down & BUTTON_BOMB) {
        if (player_bombs > 0) {
            player_bombs--;
            do_bomb();
        }
    }
    
    // Fire Arrow (Level triggered)
    if (buttons & BUTTON_FIRE) {
        if (arrow_dir == -1) {
            arrow_x = player_x;
            arrow_y = player_y;
            arrow_dir = player_dir;
        }
    }
    
    // Movement
    int8_t d = buttons_to_dir[buttons & 0x0F]; // Use lower 4 bits for direction
    if (d >= 0) {
        player_dir = d;
        // Update player sprite direction immediately in the map
        dandy_map[row_offsets[player_y] + player_x] = TILE_PLAYER1 + player_dir;
        is_dirty = true;
        
        if (player_move_timer == 0) {
            player_move_timer = TICKS_PER_MOVE;
            // Slide mechanics: try main direction, then ±1 direction
            for (uint8_t di = 0; di < 3; ++di) {
                int8_t dd = (player_dir + search_order[di]) & 7;
                if (move_player(dd)) {
                    break;
                }
            }
        }
    }
    
    if (player_move_timer > 0) {
        player_move_timer--;
    }
}

static bool move_player(uint8_t dir) {
    int16_t nx = clamp((int16_t)player_x + dir_delta_x[dir], 0, DANDY_LEVEL_WIDTH - 1);
    int16_t ny = clamp((int16_t)player_y + dir_delta_y[dir], 0, DANDY_LEVEL_HEIGHT - 1);
    uint16_t pos = row_offsets[ny] + nx;
    uint8_t tile = dandy_map[pos];
    bool can_move = true;
    
    switch (tile) {
        case TILE_SPACE:
            break;
        case TILE_DOOR:
            if (player_keys > 0) {
                player_keys--;
                iterative_flood_fill(nx, ny, TILE_DOOR, TILE_SPACE);
            } else {
                can_move = false;
            }
            break;
        case TILE_MONEY:
            player_score += 100;
            break;
        case TILE_KEY:
            player_keys++;
            break;
        case TILE_BOMB:
            player_bombs++;
            break;
        case TILE_FOOD:
            player_health += 100;
            break;
        case TILE_DOWN:
            next_level();
            return true; // We changed level, count as moved
        default:
            can_move = false;
            break;
    }
    
    if (can_move) {
        // Clear old position
        dandy_map[row_offsets[player_y] + player_x] = TILE_SPACE;
        // Update coordinates
        player_x = (uint8_t)nx;
        player_y = (uint8_t)ny;
        // Set new position with rotated player sprite
        dandy_map[row_offsets[player_y] + player_x] = TILE_PLAYER1 + player_dir;
        is_dirty = true;
    }
    
    return can_move;
}

static void move_arrow(void) {
    if (arrow_dir != -1) {
        int16_t nx = clamp((int16_t)arrow_x + dir_delta_x[arrow_dir], 0, DANDY_LEVEL_WIDTH - 1);
        int16_t ny = clamp((int16_t)arrow_y + dir_delta_y[arrow_dir], 0, DANDY_LEVEL_HEIGHT - 1);
        
        uint16_t old_pos = row_offsets[arrow_y] + arrow_x;
        uint16_t new_pos = row_offsets[ny] + nx;
        
        uint8_t tile_at_old = dandy_map[old_pos];
        uint8_t tile_at_new = dandy_map[new_pos];
        
        // Clear arrow from old position if it was indeed an arrow
        if (tile_at_old >= TILE_ARROW && tile_at_old <= TILE_ARROW + 7) {
            dandy_map[old_pos] = TILE_SPACE;
        }
        
        // Check viewport boundary (arrow dies if it leaves the visible 20x10 screen in the original JS,
        // but wait, is it visible viewport relative?
        // Let's implement simple viewport check.
        // Actually, we can get the viewport bounds.
        // For simplicity, let's calculate the viewport bounds.
        int16_t vp_left = clamp((int16_t)player_x - 10, 0, DANDY_LEVEL_WIDTH - 20);
        int16_t vp_top = clamp((int16_t)player_y - 5, 0, DANDY_LEVEL_HEIGHT - 10);
        
        if (nx < vp_left || ny < vp_top || nx >= vp_left + 20 || ny >= vp_top + 10) {
            // Arrow leaves viewport -> dies
            arrow_dir = -1;
            is_dirty = true;
            return;
        }
        
        if (tile_at_new != TILE_SPACE) {
            // Hit something! Arrow dies.
            arrow_dir = -1;
            
            // Check if we hit a destructible target (Monster, Generator, Heart, Bomb)
            // In JS: if (nv >= kBomb && nv < kArrow)
            if (tile_at_new >= TILE_BOMB && tile_at_new < TILE_ARROW) {
                uint8_t replacement = TILE_SPACE;
                if (tile_at_new == TILE_BOMB) {
                    do_bomb();
                } else if (tile_at_new == TILE_HEART) {
                    replacement = TILE_MONSTER3;
                } else if (tile_at_new == TILE_MONSTER2 || tile_at_new == TILE_MONSTER3) {
                    replacement = tile_at_new - 1; // Monster 3 -> 2, Monster 2 -> 1
                }
                dandy_map[new_pos] = replacement;
            }
        } else {
            // Move arrow forward and rotate its sprite
            dandy_map[new_pos] = TILE_ARROW + ((arrow_dir - 5) & 7);
            arrow_x = (uint8_t)nx;
            arrow_y = (uint8_t)ny;
        }
        is_dirty = true;
    }
}

static void do_bomb(void) {
    // Blow up all monsters and generators in the visible viewport
    int16_t vp_left = clamp((int16_t)player_x - 10, 0, DANDY_LEVEL_WIDTH - 20);
    int16_t vp_top = clamp((int16_t)player_y - 5, 0, DANDY_LEVEL_HEIGHT - 10);
    
    for (uint8_t y = 0; y < 10; ++y) {
        uint16_t row_offset = row_offsets[vp_top + y];
        for (uint8_t x = 0; x < 20; ++x) {
            uint16_t pos = row_offset + (vp_left + x);
            uint8_t tile = dandy_map[pos];
            if ((tile >= TILE_MONSTER1 && tile <= TILE_MONSTER3) ||
                (tile >= TILE_GENERATOR1 && tile <= TILE_GENERATOR3)) {
                dandy_map[pos] = TILE_SPACE;
            }
        }
    }
    is_dirty = true;
}

static void move_monsters(void) {
    int16_t vp_left = clamp((int16_t)player_x - 10, 0, DANDY_LEVEL_WIDTH - 20);
    int16_t vp_top = clamp((int16_t)player_y - 5, 0, DANDY_LEVEL_HEIGHT - 10);
    
    uint8_t dx = 4;
    uint8_t dy = 4;
    
    monster_rotor++;
    if (monster_rotor >= 16) {
        monster_rotor = 0;
    }
    
    // Retro Optimization: Scan only a sparse grid based on rotor
    uint8_t x_start = vp_left + (monster_rotor % dx);
    uint8_t y_start = vp_top + (monster_rotor / dx);
    uint8_t x_end = vp_left + 20;
    uint8_t y_end = vp_top + 10;
    
    for (uint8_t my = y_start; my < y_end; my += dy) {
        uint16_t row_offset = row_offsets[my];
        for (uint8_t mx = x_start; mx < x_end; mx += dx) {
            uint16_t pos = row_offset + mx;
            uint8_t tile = dandy_map[pos];
            
            if (tile >= TILE_MONSTER1 && tile <= TILE_MONSTER3) {
                // Determine direction towards player
                int8_t p_dy = to_delta(player_y, my);
                int8_t p_dx = to_delta(player_x, mx);
                int8_t m_dir = delta_to_dir[p_dy + 1][p_dx + 1];
                
                // Try moving in main direction, then search neighbors
                for (uint8_t d = 0; d < 3; ++d) {
                    int8_t dd = (m_dir + search_order[d]) & 7;
                    uint16_t n_pos = row_offsets[my + dir_delta_y[dd]] + (mx + dir_delta_x[dd]);
                    uint8_t n_tile = dandy_map[n_pos];
                    
                    if (IS_PLAYER(n_tile)) {
                        // Hurt player!
                        dandy_map[pos] = TILE_SPACE;
                        player_health -= 10 * (tile - TILE_MONSTER1 + 1);
                        is_dirty = true;
                        break;
                    } else if (n_tile == TILE_SPACE) {
                        // Move monster
                        dandy_map[pos] = TILE_SPACE;
                        dandy_map[n_pos] = tile;
                        is_dirty = true;
                        break;
                    } else if (n_tile >= TILE_ARROW && n_tile <= TILE_ARROW + 7) {
                        // Blocked by arrow, don't slide
                        break;
                    }
                }
            } else if (tile >= TILE_GENERATOR1 && tile <= TILE_GENERATOR3) {
                // Generators spawn monsters randomly (50% chance per check)
                // In JS: if (Math.random() < 0.5) { spawn... }
                // On retro hardware, we'll use a simple pseudo-random generator or system clock.
                // We'll simulate a 50% chance using the rotor/frame count or a simple shift register.
                // For now, let's use a very simple condition.
                static uint16_t rand_seed = 0xACE1;
                // Simple Galois LFSR for 16-bit random numbers
                uint8_t lsb = rand_seed & 1;
                rand_seed >>= 1;
                if (lsb) {
                    rand_seed ^= 0xB400u;
                }
                
                if ((rand_seed & 7) < 4) { // ~50% chance
                    uint8_t spawn_dir = (rand_seed & 3) * 2; // Diagonal directions (0, 2, 4, 6)
                    for (uint8_t dd = 0; dd < 8; dd += 2) {
                        uint8_t check_dir = (spawn_dir + dd) % 8;
                        uint16_t g_pos = row_offsets[my + dir_delta_y[check_dir]] + (mx + dir_delta_x[check_dir]);
                        if (dandy_map[g_pos] == TILE_SPACE) {
                            // Spawn Monster of corresponding tier (1, 2, or 3)
                            dandy_map[g_pos] = TILE_MONSTER1 + (tile - TILE_GENERATOR1);
                            is_dirty = true;
                            break;
                        }
                    }
                }
            }
        }
    }
}

/* Highly optimized non-recursive 8-way flood fill using parallel 8-bit stacks */
static void iterative_flood_fill(uint8_t start_x, uint8_t start_y, uint8_t oc, uint8_t nc) {
    if (oc == nc || dandy_map[row_offsets[start_y] + start_x] != oc) return;
    
    flood_stack_ptr = 0;
    
    // Mark immediately and push
    dandy_map[row_offsets[start_y] + start_x] = nc;
    flood_push(start_x, start_y);
    
    while (flood_stack_ptr > 0) {
        // Pop
        flood_stack_ptr--;
        uint8_t x = flood_stack_x[flood_stack_ptr];
        uint8_t y = flood_stack_y[flood_stack_ptr];
        
        // Scan 8 neighbors
        for (int8_t dy = -1; dy <= 1; ++dy) {
            int16_t ny = (int16_t)y + dy;
            if (ny < 0 || ny >= DANDY_LEVEL_HEIGHT) continue;
            
            uint16_t row_offset = row_offsets[ny];
            
            for (int8_t dx = -1; dx <= 1; ++dx) {
                if (dx == 0 && dy == 0) continue;
                
                int16_t nx = (int16_t)x + dx;
                if (nx < 0 || nx >= DANDY_LEVEL_WIDTH) continue;
                
                uint16_t pos = row_offset + nx;
                if (dandy_map[pos] == oc) {
                    dandy_map[pos] = nc; // Mark immediately to prevent double-queuing!
                    flood_push((uint8_t)nx, (uint8_t)ny);
                }
            }
        }
    }
}

/* Core Math Helpers */

static int16_t clamp(int16_t val, int16_t min, int16_t max) {
    if (val < min) return min;
    if (val > max) return max;
    return val;
}

static int8_t to_delta(int16_t target, int16_t current) {
    if (target > current) return 1;
    if (target < current) return -1;
    return 0;
}
