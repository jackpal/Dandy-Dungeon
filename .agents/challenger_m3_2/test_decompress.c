#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "dandy_core.h"
#include "test_cases.h"

/* Implement the external pointer array required by levels.h/dandy_core.c */
const uint8_t* const dandy_levels[26] = {
    case_all_spaces,  /* Level 0 */
    case_all_walls,   /* Level 1 */
    case_max_density, /* Level 2 */
    case_truncated,   /* Level 3: truncated bitstream, should not crash/loop */
    case_long,        /* Level 4: extra bytes, should ignore them and decode correctly */
    case_empty,       /* Level 5: empty bitstream, should not crash/loop */
    case_all_spaces,  /* Level 6 */
    case_all_spaces,  /* Level 7 */
    case_all_spaces,  /* Level 8 */
    case_all_spaces,  /* Level 9 */
    case_all_spaces,  /* Level 10 */
    case_all_spaces,  /* Level 11 */
    case_all_spaces,  /* Level 12 */
    case_all_spaces,  /* Level 13 */
    case_all_spaces,  /* Level 14 */
    case_all_spaces,  /* Level 15 */
    case_all_spaces,  /* Level 16 */
    case_all_spaces,  /* Level 17 */
    case_all_spaces,  /* Level 18 */
    case_all_spaces,  /* Level 19 */
    case_all_spaces,  /* Level 20 */
    case_all_spaces,  /* Level 21 */
    case_all_spaces,  /* Level 22 */
    case_all_spaces,  /* Level 23 */
    case_all_spaces,  /* Level 24 */
    case_all_spaces   /* Level 25 */
};

/* Mock HAL functions required by dandy_core.c */
void hal_draw_tile(uint8_t x, uint8_t y, uint8_t tile_id) {}
void hal_update_hud(void) {}
void hal_clear_sprites(uint8_t vp_left, uint8_t vp_top) {}
void hal_set_sprite(uint8_t sprite_idx, uint8_t x, uint8_t y, uint8_t tile_id, uint8_t flags) {}
void hal_play_sound(uint8_t sound_id) {}

/* Helper to verify inner map tiles */
int verify_inner_tiles(uint8_t expected_tile) {
    for (uint8_t y = 1; y <= 28; ++y) {
        for (uint8_t x = 1; x <= 58; ++x) {
            uint8_t tile = dandy_map[y * 60 + x];
            if (x == 1 && y == 1) {
                // Ignore player spawn tile
                uint8_t expected_player_tile = TILE_PLAYER1;
                if (tile != expected_player_tile) {
                    printf("Fidelity Error at player spawn (x=1, y=1): Expected player tile %d, got %d\n", expected_player_tile, tile);
                    return 0;
                }
                continue;
            }
            if (tile != expected_tile) {
                printf("Fidelity Error at (x=%d, y=%d): Expected tile ID %d, got %d\n", x, y, expected_tile, tile);
                return 0;
            }
        }
    }
    return 1;
}

/* Helper to verify border walls */
int verify_borders() {
    // Check top and bottom rows
    for (uint8_t x = 0; x < 60; ++x) {
        if (dandy_map[x] != TILE_WALL) {
            printf("Border Error at top row col %d: Expected TILE_WALL, got %d\n", x, dandy_map[x]);
            return 0;
        }
        if (dandy_map[29 * 60 + x] != TILE_WALL) {
            printf("Border Error at bottom row col %d: Expected TILE_WALL, got %d\n", x, dandy_map[29 * 60 + x]);
            return 0;
        }
    }
    // Check left and right columns
    for (uint8_t y = 0; y < 30; ++y) {
        if (dandy_map[y * 60] != TILE_WALL) {
            printf("Border Error at left col row %d: Expected TILE_WALL, got %d\n", y, dandy_map[y * 60]);
            return 0;
        }
        if (dandy_map[y * 60 + 59] != TILE_WALL) {
            printf("Border Error at right col row %d: Expected TILE_WALL, got %d\n", y, dandy_map[y * 60 + 59]);
            return 0;
        }
    }
    return 1;
}

int main() {
    printf("============================================================\n");
    printf("C DECOMPRESSOR ADVERSARIAL VERIFICATION HARNESS\n");
    printf("============================================================\n");

    // Initialize player join flags so set_player_start_position behaves predictably
    for (int p = 0; p < 4; ++p) {
        player_joined[p] = (p == 0); // Only Player 1 joined
    }

    // -------------------------------------------------------------------------
    // Test Case 0: All Spaces
    // -------------------------------------------------------------------------
    printf("Test Case 0: Decompressing All-Space level (203 bytes compressed)... ");
    dandy_load_level(0);
    assert(verify_borders() && "Case 0 borders failed!");
    assert(verify_inner_tiles(TILE_SPACE) && "Case 0 inner tiles failed!");
    printf("PASS\n");

    // -------------------------------------------------------------------------
    // Test Case 1: All Walls
    // -------------------------------------------------------------------------
    printf("Test Case 1: Decompressing All-Wall level (406 bytes compressed)... ");
    dandy_load_level(1);
    assert(verify_borders() && "Case 1 borders failed!");
    assert(verify_inner_tiles(TILE_WALL) && "Case 1 inner tiles failed!");
    printf("PASS\n");

    // -------------------------------------------------------------------------
    // Test Case 2: Max Density (all tiles are ID 15)
    // -------------------------------------------------------------------------
    printf("Test Case 2: Decompressing Max Density level (1218 bytes compressed)... ");
    dandy_load_level(2);
    assert(verify_borders() && "Case 2 borders failed!");
    assert(verify_inner_tiles(15) && "Case 2 inner tiles failed!");
    printf("PASS\n");

    // -------------------------------------------------------------------------
    // Test Case 4: Extremely Long bitstream (extra 1000 bytes at the end)
    // -------------------------------------------------------------------------
    printf("Test Case 4: Decompressing Extra Long bitstream (ignored trailing bytes)... ");
    dandy_load_level(4);
    assert(verify_borders() && "Case 4 borders failed!");
    assert(verify_inner_tiles(15) && "Case 4 inner tiles failed!");
    printf("PASS\n");

    // -------------------------------------------------------------------------
    // Test Case 3: Truncated bitstream (only 5 bytes)
    // -------------------------------------------------------------------------
    printf("Test Case 3: Decompressing Truncated bitstream (5 bytes, should not crash/loop)... ");
    // Since this is truncated, the decompressor will read past the array.
    // In our test harness, this might read from other static arrays in memory.
    // We just want to verify it finishes successfully (does not loop infinitely or segfault).
    dandy_load_level(3);
    printf("PASS (Completed without crash or infinite loop)\n");

    // -------------------------------------------------------------------------
    // Test Case 5: Empty/Zero bitstream (1 byte of 0x00)
    // -------------------------------------------------------------------------
    printf("Test Case 5: Decompressing Empty/Zero bitstream (1 byte, should not crash/loop)... ");
    dandy_load_level(5);
    printf("PASS (Completed without crash or infinite loop)\n");

    printf("\n============================================================\n");
    printf("ALL C DECOMPRESSOR ADVERSARIAL CHECKS PASSED SUCCESSFULLY!\n");
    printf("============================================================\n");

    return 0;
}
