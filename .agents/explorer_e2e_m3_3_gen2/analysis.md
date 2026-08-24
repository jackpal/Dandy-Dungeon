# Dandy Dungeon E2E Testing Analysis & Case Designs (Milestone 3)

## 1. Executive Summary

This report presents a thorough, read-only analysis of the Dandy Dungeon C game engine (`dandy_core.c`, `dandy_core.h`) and its offline E2E test suite (`dandy_env.py`, `test_tier1.py`). The objective is to design a comprehensive test suite for **Milestone 3 (E2E Testing Track)**, covering:
- **Tier 2 (Boundary & Corner Cases)**: 49 highly specific test cases verifying edge values, map boundaries, capacity limits, and arithmetic overflows across all 10 features (F-01 to F-10).
- **Tier 3 (Cross-Feature Interactions)**: 8 test cases verifying concurrent and multi-system game rules.

During the source code investigation, three major architectural limitations/vulnerabilities were uncovered:
1. **Generator Spawning Out-of-Bounds/Wrap-Around (F-08)**: The generator spawning algorithm lack coordinate boundary checks, leading to row-wrapping at left/right edges and out-of-bounds array reads (`row_offsets[255]` or `row_offsets[30]`) at top/bottom edges.
2. **Flood Fill Stack Overflow (F-04)**: The non-recursive flood fill is capped at `FLOOD_STACK_SIZE = 64`. Complex door networks exceeding this size will leave doors locked.
3. **Health Overflow Instant-Death (F-03)**: Health increments by 100 without upper-bound clamping. Exceeding `32767` (maximum signed 16-bit integer) triggers an overflow to negative values, causing the player to die instantly on the next tick.

All designed test cases strictly adhere to the **Double-Assert Rule**, verifying both internal C engine globals and mock Hardware Abstraction Layer (HAL) side-effects.

---

## 2. Core Engine Architecture & Vulnerability Analysis

### 2.1 F-08: Generator Spawning & LFSR Determinism
The engine implements enemy spawning via a 16-tick sparse grid update. A generator at `(mx, my)` ticks only when:
$$\text{monster\_rotor} == (\text{my} \pmod 4) \times 4 + (\text{mx} \pmod 4)$$
This sparse grid freezing ensures off-screen entities are frozen. When active, it uses a 16-bit Galois Linear Feedback Shift Register (LFSR) with a feedback polynomial of `0xB400`:
```c
static uint16_t rand_seed = 0xACE1;
uint8_t lsb = rand_seed & 1;
rand_seed >>= 1;
if (lsb) { rand_seed ^= 0xB400u; }
```
If `(rand_seed & 7) < 4`, spawning is triggered. The starting direction is `(rand_seed & 3) * 2` (clockwise cardinal directions: 0=Up, 2=Right, 4=Down, 6=Left).

#### ⚠️ Bug 1: Out-of-Bounds Spawning & Map Wrap-Around
Line 627 of `dandy_core.c` calculates the spawn target index `g_pos`:
```c
uint16_t g_pos = row_offsets[my + dir_delta_y[check_dir]] + (mx + dir_delta_x[check_dir]);
```
- **X-Axis Wrap-Around**: At `mx = 59` (right edge), spawning Right (`dir_delta_x = 1`) results in `mx + 1 = 60`. In the 60-column map, `row_offsets[my] + 60` is equivalent to the 0th tile of row `my + 1`. The monster wraps to the left edge of the next row.
- **Y-Axis Out-of-Bounds**: At `my = 0` (top edge), spawning Up (`dir_delta_y = -1`) causes `my - 1 = -1` (underflows to `255` for unsigned `uint8_t`). It accesses `row_offsets[255]`, which reads arbitrary memory preceding/succeeding the stack/data segments, leading to potential segmentation faults. At `my = 29` (bottom edge), spawning Down accesses `row_offsets[30]`, which reads from `dir_delta_x` memory.

### 2.2 F-09: Multiplayer, Camera Clamping & Spectator Centroid
- **Camera Clamping**: The viewport camera is a 20x10 window drawn around the target player. The camera's top-left coordinate `(vp_left, vp_top)` is computed as:
  $$vp\_left = \text{clamp}(target\_x - 10, 0, 40)$$
  $$vp\_top = \text{clamp}(target\_y - 5, 0, 20)$$
  This clamps the viewport to the 60x30 map boundaries.
- **Spectator Mode Centroid**: When the local player dies (`health <= 0`), the camera targets the integer division centroid of all other joined and alive players:
  $$target\_x = \frac{\sum x_i}{N_{\text{alive}}}, \quad target\_y = \frac{\sum y_i}{N_{\text{alive}}}$$
  If all other players are dead ($N_{\text{alive}} = 0$), the target remains at the local player's dead coordinates.

### 2.3 F-10: Level Transitions
Stairs (`TILE_DOWN`) trigger `next_level()`, which increments `current_level` up to the maximum (4) and invokes `dandy_load_level()`.
- **Portal Spawning Overlap**: Player coordinates are offset from the portal (`TILE_UP`) using `spawn_offsets_x` and `spawn_offsets_y`. If the portal is placed at `(0, 0)`, the offsets are clamped to the boundary:
  - Player 0: `(0, 0)`
  - Player 3: `(0, 0)`
  This causes Player 0 and Player 3 to overlap at `(0, 0)`. The map tile registers the last-written sprite (Player 3), overwriting Player 0's visual representation while preserving their logical coordinates.
- **State Carrying**: The levels are loaded via RLE decompression. Player health, score, keys, and bombs are preserved, but active arrows are destroyed (`arrow_dir[p] = -1`). Player direction (`player_dir`) and move cooldown timers are carried over, meaning input timers do not reset.

---

## 3. Tier 2: Boundary & Corner Cases (49 Tests)

### Feature F-01: Movement & Timing

#### Test 1: `test_f01_t2_move_clamp_top_boundary`
*   **Description**: Moving Up at the top boundary ($y=0$) clamps the coordinate.
*   **Setup**: Clean map, Player 0 at $(10, 0)$, facing Up.
*   **Inputs**: Step `BUTTON_UP`.
*   **C Globals Assertions**:
    *   `player_x[0] == 10`, `player_y[0] == 0`
    *   `player_move_timer[0] == 3` (cooldown active)
    *   `dandy_map[0 * 60 + 10] == TILE_PLAYER1 + 0` (facing Up)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 0`
    *   `mock_get_viewport_camera() == (0, 0)`
    *   `mock_get_sprite(0)` is active at viewport $(10 \times 8, 0 \times 8)$

#### Test 2: `test_f01_t2_move_clamp_bottom_boundary`
*   **Description**: Moving Down at the bottom boundary ($y=29$) clamps the coordinate.
*   **Setup**: Clean map, Player 0 at $(10, 29)$, facing Down.
*   **Inputs**: Step `BUTTON_DOWN`.
*   **C Globals Assertions**:
    *   `player_x[0] == 10`, `player_y[0] == 29`
    *   `dandy_map[29 * 60 + 10] == TILE_PLAYER1 + 4` (facing Down)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 0`
    *   `mock_get_viewport_camera() == (0, 20)`

#### Test 3: `test_f01_t2_move_clamp_left_boundary`
*   **Description**: Moving Left at the left boundary ($x=0$) clamps the coordinate.
*   **Setup**: Clean map, Player 0 at $(0, 10)$, facing Left.
*   **Inputs**: Step `BUTTON_LEFT`.
*   **C Globals Assertions**:
    *   `player_x[0] == 0`, `player_y[0] == 10`
    *   `dandy_map[10 * 60 + 0] == TILE_PLAYER1 + 6` (facing Left)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 0`
    *   `mock_get_viewport_camera() == (0, 5)`

#### Test 4: `test_f01_t2_move_clamp_right_boundary`
*   **Description**: Moving Right at the right boundary ($x=59$) clamps the coordinate.
*   **Setup**: Clean map, Player 0 at $(59, 10)$, facing Right.
*   **Inputs**: Step `BUTTON_RIGHT`.
*   **C Globals Assertions**:
    *   `player_x[0] == 59`, `player_y[0] == 10`
    *   `dandy_map[10 * 60 + 59] == TILE_PLAYER1 + 2` (facing Right)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 0`
    *   `mock_get_viewport_camera() == (40, 5)`

#### Test 5: `test_f01_t2_move_invalid_input_diagonal_conflict`
*   **Description**: Pressing conflicting cardinal inputs `BUTTON_LEFT | BUTTON_RIGHT` results in no movement.
*   **Setup**: Clean map, Player 0 at $(10, 10)$, facing Up (dir 0).
*   **Inputs**: Step `BUTTON_LEFT | BUTTON_RIGHT`.
*   **C Globals Assertions**:
    *   `player_x[0] == 10`, `player_y[0] == 10`
    *   `player_dir[0] == 0` (unchanged facing direction)
    *   `player_move_timer[0] == 0` (no cooldown triggered because input was mapped to -1)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 0`

#### Test 6: `test_f01_t2_move_invalid_input_all_pressed`
*   **Description**: Pressing all four direction buttons simultaneously results in no movement.
*   **Setup**: Clean map, Player 0 at $(10, 10)$.
*   **Inputs**: Step `BUTTON_UP | BUTTON_DOWN | BUTTON_LEFT | BUTTON_RIGHT`.
*   **C Globals Assertions**:
    *   `player_x[0] == 10`, `player_y[0] == 10`
    *   `player_move_timer[0] == 0`
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 0`

---

### Feature F-02: Slide Mechanics

#### Test 7: `test_f02_t2_slide_boundary_clamp_top`
*   **Description**: Moving Up-Right at the top boundary ($y=0$) when Right is blocked by a wall. Up is out-of-bounds, so the player remains stationary.
*   **Setup**: Clean map, Player 0 at $(10, 0)$. Wall at $(11, 0)$.
*   **Inputs**: Step `BUTTON_UP | BUTTON_RIGHT` (dir 1).
*   **C Globals Assertions**:
    *   `player_x[0] == 10`, `player_y[0] == 0` (Slide Up-Right $(11, -1)$ and Right $(11, 0)$ are blocked, Up $(10, -1)$ is clamped/blocked)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 0`

#### Test 8: `test_f02_t2_slide_boundary_clamp_bottom`
*   **Description**: Moving Left (6) blocked by wall at $(9, 29)$ near the bottom boundary. Slide Up-Left $(9, 28)$ is free, so player slides Up-Left.
*   **Setup**: Clean map, Player 0 at $(10, 29)$. Wall at $(9, 29)$ (Left).
*   **Inputs**: Step `BUTTON_LEFT` (dir 6).
*   **C Globals Assertions**:
    *   `player_x[0] == 9`, `player_y[0] == 28` (Slid Up-Left)
    *   `player_dir[0] == 6` (facing Left)
*   **Mock HAL Assertions**:
    *   `mock_get_viewport_camera() == (0, 20)` (clamped)

#### Test 9: `test_f02_t2_slide_boundary_clamp_left`
*   **Description**: Moving Left (6) blocked by wall at $(1, 10)$ on the edge of the map. Up-Left $(0, 9)$ is blocked. Down-Left is free, so player slides Down-Left.
*   **Setup**: Clean map, Player 0 at $(1, 10)$. Wall at $(0, 10)$ and $(0, 9)$.
*   **Inputs**: Step `BUTTON_LEFT` (dir 6).
*   **C Globals Assertions**:
    *   `player_x[0] == 0`, `player_y[0] == 11` (Slid Down-Left)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 0`

#### Test 10: `test_f02_t2_slide_boundary_clamp_right`
*   **Description**: Moving Right (2) blocked by wall at $(58, 10)$ near the right edge. Down-Right $(59, 11)$ is free, Up-Right $(59, 9)$ is blocked.
*   **Setup**: Player at $(58, 10)$. Wall at $(59, 10)$ and $(59, 9)$.
*   **Inputs**: Step `BUTTON_RIGHT` (dir 2).
*   **C Globals Assertions**:
    *   `player_x[0] == 59`, `player_y[0] == 11` (Slid Down-Right)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 0`

#### Test 11: `test_f02_t2_slide_complex_corner_blocked`
*   **Description**: Player in a tight corner where all slide options are blocked.
*   **Setup**: Player at $(10, 10)$. Walls at $(11, 10)$ (Right), $(11, 9)$ (Up-Right), and $(11, 11)$ (Down-Right).
*   **Inputs**: Step `BUTTON_RIGHT`.
*   **C Globals Assertions**:
    *   `player_x[0] == 10`, `player_y[0] == 10` (no movement)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 0`

#### Test 12: `test_f02_t2_slide_priority_clockwise`
*   **Description**: When moving cardinal Right (2) is blocked, and BOTH adjacent directions (Up-Right 1, Down-Right 3) are free, the engine checks counter-clockwise first.
*   **Setup**: Clean map, Player at $(10, 10)$. Wall at $(11, 10)$ (Right). Both $(11, 9)$ and $(11, 11)$ are `TILE_SPACE`.
*   **Inputs**: Step `BUTTON_RIGHT`.
*   **C Globals Assertions**:
    *   `player_x[0] == 11`, `player_y[0] == 9` (slid counter-clockwise to Up-Right)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 0`

---

### Feature F-03: Item Collection

#### Test 13: `test_f03_t2_collect_food_health_overflow`
*   **Description**: Exceeding the positive limit of `int16_t` health ($32767$) via food collection triggers a signed overflow, turning health negative and killing the player on the next tick.
*   **Setup**: Clean map, Player 0 at $(10, 10)$, health set to `32700`. Food tile at $(11, 10)$.
*   **Inputs**:
    1. Step `BUTTON_RIGHT` (collects food, health becomes `32800` which overflows to `-32736`).
    2. Step `0` (tick processes player death because health is $\le 0$).
*   **C Globals Assertions**:
    *   After step 1: `player_health[0] == -32736`
    *   After step 2: `player_health[0] == 0` (clamped to 0 on death), `dandy_map[10 * 60 + 11] == TILE_SPACE` (player tile cleared)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 2` (`SOUND_FOOD` on step 1, `SOUND_DIE` on step 2)

#### Test 14: `test_f03_t2_collect_money_score_wrap`
*   **Description**: Score is a `uint16_t` (max 65535). Collecting money at score $65500$ wraps around.
*   **Setup**: Clean map, Player 0 at $(10, 10)$, score set to `65500`. Money at $(11, 10)$.
*   **Inputs**: Step `BUTTON_RIGHT`.
*   **C Globals Assertions**:
    *   `player_score[0] == 64` ($(65500 + 100) \pmod{65536} = 64$)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 1` (`SOUND_KEY`)

#### Test 15: `test_f03_t2_collect_key_wrap`
*   **Description**: Keys is a `uint8_t` (max 255). Collecting a key at 255 wraps to 0.
*   **Setup**: Clean map, Player 0 at $(10, 10)$, keys set to `255`. Key at $(11, 10)$.
*   **Inputs**: Step `BUTTON_RIGHT`.
*   **C Globals Assertions**:
    *   `player_keys[0] == 0` ($(255 + 1) \pmod{256} = 0$)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 1` (`SOUND_KEY`)

#### Test 16: `test_f03_t2_collect_bomb_wrap`
*   **Description**: Bombs is a `uint8_t` (max 255). Collecting a bomb at 255 wraps to 0.
*   **Setup**: Clean map, Player 0 at $(10, 10)$, bombs set to `255`. Bomb at $(11, 10)$.
*   **Inputs**: Step `BUTTON_RIGHT`.
*   **C Globals Assertions**:
    *   `player_bombs[0] == 0`
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 1` (`SOUND_KEY`)

#### Test 17: `test_f03_t2_collect_food_negative_health`
*   **Description**: Confirms that a logically dead player (health 0) cannot collect food even if button inputs are sent.
*   **Setup**: Clean map, Player 0 at $(10, 10)$, health set to `0`. Food at $(11, 10)$.
*   **Inputs**: Step `BUTTON_RIGHT`.
*   **C Globals Assertions**:
    *   `player_x[0] == 10`, `player_y[0] == 10` (did not move)
    *   `player_health[0] == 0`
    *   `dandy_map[10 * 60 + 11] == TILE_FOOD` (intact)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 0`

#### Test 18: `test_f03_t2_collect_item_on_stairs`
*   **Description**: Stepping onto stairs warps player immediately.
*   **Setup**: Player at $(10, 10)$. Stairs (`TILE_DOWN`) at $(11, 10)$.
*   **Inputs**: Step `BUTTON_RIGHT`.
*   **C Globals Assertions**:
    *   `current_level == 1`
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 1` (`SOUND_WARP`)

---

### Feature F-04: Door & Key Mechanics

#### Test 19: `test_f04_t2_door_flood_fill_stack_overflow`
*   **Description**: Exposing the `FLOOD_STACK_SIZE = 64` limit. Unlocking a door network of 80 doors leaves 16 doors locked because they overflow the stack.
*   **Setup**: Clean map, Player 0 at $(10, 10)$ with 1 key. Create a contiguous line of 80 door tiles starting from $(11, 10)$ extending horizontally.
*   **Inputs**: Step `BUTTON_RIGHT` (into the first door).
*   **C Globals Assertions**:
    *   Exactly 64 door tiles are converted to `TILE_SPACE` (including the player's occupied tile).
    *   Exactly 16 door tiles at the far end of the network remain `TILE_DOOR`.
    *   `player_keys[0] == 0` (only 1 key consumed).
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 1` (`SOUND_KEY`)

#### Test 20: `test_f04_t2_door_flood_fill_circular`
*   **Description**: A circular ring of doors is completely cleared by a single unlock without infinite looping.
*   **Setup**: Player at $(10, 10)$ with 1 key. Doors placed in a $3 \times 3$ hollow square at $x \in [11, 13], y \in [9, 11]$ (8 doors total).
*   **Inputs**: Step `BUTTON_RIGHT` (into the door at $(11, 10)$).
*   **C Globals Assertions**:
    *   All 8 doors in the loop are cleared to `TILE_SPACE`/Player.
    *   `player_keys[0] == 0`.
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 1` (`SOUND_KEY`)

#### Test 21: `test_f04_t2_door_flood_fill_boundary`
*   **Description**: Unlocking a door network that touches the map boundaries.
*   **Setup**: Player at $(1, 0)$ with 1 key. Doors placed along the top edge at $(0, 0)$, $(1, 0)$, $(2, 0)$.
*   **Inputs**: Step `BUTTON_LEFT` (into $(0, 0)$).
*   **C Globals Assertions**:
    *   All doors along the boundary are cleared.
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 1` (`SOUND_KEY`)

#### Test 22: `test_f04_t2_door_unlock_multi_key_consumption`
*   **Description**: Verifies that even if a massive door network is cleared, only 1 key is decremented from the player's inventory.
*   **Setup**: Player at $(10, 10)$ with 5 keys. Doors placed at $(11, 10)$, $(12, 10)$, $(13, 10)$.
*   **Inputs**: Step `BUTTON_RIGHT`.
*   **C Globals Assertions**:
    *   `player_keys[0] == 4` (exactly 1 key consumed)
    *   All three doors cleared.
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 1` (`SOUND_KEY`)

#### Test 23: `test_f04_t2_door_unlock_no_key_diagonal_slide_blocked`
*   **Description**: Player with 0 keys tries to move into a door, slide directions are blocked by walls. Player remains stationary.
*   **Setup**: Player at $(10, 10)$, 0 keys. Door at $(11, 10)$. Walls at $(11, 9)$ and $(11, 11)$.
*   **Inputs**: Step `BUTTON_RIGHT`.
*   **C Globals Assertions**:
    *   `player_x[0] == 10`, `player_y[0] == 10`
    *   `dandy_map[10 * 60 + 11] == TILE_DOOR`
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 0`

---

### Feature F-05: Combat & Projectiles

#### Test 24: `test_f05_t2_arrow_boundary_destroy_left`
*   **Description**: An arrow moving Left is destroyed when it crosses the left edge of the player's viewport.
*   **Setup**: Player 0 at $(10, 10)$ (viewport left edge is $10 - 10 = 0$).
*   **Inputs**:
    1. Step `BUTTON_FIRE | BUTTON_LEFT` (fires arrow Left, arrow spawns at $(9, 10)$).
    2. Step 9 empty inputs (arrow moves to $8, 7, \dots, 0$).
    3. Step 1 empty input (arrow moves to $-1$, crosses viewport left edge, destroyed).
*   **C Globals Assertions**:
    *   After step 1: `arrow_x[0] == 9`, `arrow_dir[0] == 6`
    *   After step 10 (10th move): `arrow_dir[0] == -1` (destroyed), `dandy_map[10 * 60 + 0] == TILE_SPACE`
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 1` (`SOUND_SHOOT` only)

#### Test 25: `test_f05_t2_arrow_boundary_destroy_right`
*   **Description**: Arrow moving Right destroyed at viewport right edge ($player\_x + 9$).
*   **Setup**: Player 0 at $(10, 10)$ (viewport right edge is $10 + 9 = 19$).
*   **Inputs**:
    1. Step `BUTTON_FIRE | BUTTON_RIGHT` (fires arrow Right, spawns at $(11, 10)$).
    2. Step 9 empty inputs (arrow reaches $(19, 10)$ on 9th tick, then moves to $(20, 10)$ which is outside viewport).
*   **C Globals Assertions**:
    *   After 9 ticks: `arrow_x[0] == 19`
    *   After 10 ticks: `arrow_dir[0] == -1`
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 1`

#### Test 26: `test_f05_t2_arrow_boundary_destroy_top`
*   **Description**: Arrow moving Up destroyed at viewport top edge ($player\_y - 5$).
*   **Setup**: Player 0 at $(10, 10)$ (viewport top edge is $10 - 5 = 5$).
*   **Inputs**:
    1. Step `BUTTON_FIRE | BUTTON_UP` (spawns at $(10, 9)$).
    2. Step 5 empty inputs (reaches $(10, 5)$, then moves to $(10, 4)$ and dies).
*   **C Globals Assertions**:
    *   After 5 ticks: `arrow_dir[0] == -1`
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 1`

#### Test 27: `test_f05_t2_arrow_boundary_destroy_bottom`
*   **Description**: Arrow moving Down destroyed at viewport bottom edge ($player\_y + 4$).
*   **Setup**: Player 0 at $(10, 10)$ (viewport bottom edge is $10 + 4 = 14$).
*   **Inputs**:
    1. Step `BUTTON_FIRE | BUTTON_DOWN` (spawns at $(10, 11)$).
    2. Step 4 empty inputs.
*   **C Globals Assertions**:
    *   After 4 ticks: `arrow_dir[0] == -1`
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 1`

#### Test 28: `test_f05_t2_arrow_collision_asymmetric`
*   **Description**: Two arrows fired towards each other collide. Player 0's arrow is processed first, hits Player 1's arrow, and is destroyed. Player 1's arrow remains intact (asymmetric destruction).
*   **Setup**: Player 0 at $(10, 10)$, facing Right. Player 1 at $(13, 10)$, facing Left. Both joined.
*   **Inputs**:
    1. Step `BUTTON_FIRE` for P0, `BUTTON_FIRE` for P1 (P0 arrow spawns at $(11, 10)$ facing Right; P1 arrow spawns at $(12, 10)$ facing Left).
    2. Step 1 empty input (P0 arrow moves to $(12, 10)$ where P1's arrow tile is. P0's arrow is destroyed. P1's arrow moves to $(11, 10)$ and survives).
*   **C Globals Assertions**:
    *   `arrow_dir[0] == -1` (Player 0's arrow destroyed)
    *   `arrow_dir[1] == 6` (Player 1's arrow active, now at $(11, 10)$)
    *   `dandy_map[10 * 60 + 11] == TILE_ARROW + 1` (Player 1's Left-facing arrow tile)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 2` (`SOUND_SHOOT` for both)

#### Test 29: `test_f05_t2_arrow_hit_inactive_player_start`
*   **Description**: An arrow shot at a starting portal where an unjoined player's logical coordinate resides does NOT hit them, because their tile is not on the map.
*   **Setup**: Level 0 loaded. Player 1 is NOT joined, but logically starts at $(up\_x + 1, up\_y)$ per `spawn_offsets_x`. Player 0 is joined and fires an arrow at $(up\_x + 1, up\_y)$.
*   **Inputs**: Step `BUTTON_FIRE` facing the target.
*   **C Globals Assertions**:
    *   Arrow passes through the cell (tile is `TILE_SPACE`).
    *   `arrow_dir[0]` remains active.
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 1` (`SOUND_SHOOT`)

---

### Feature F-06: Smart Bomb Action

#### Test 30: `test_f06_t2_bomb_empty_viewport`
*   **Description**: Detonating a smart bomb in a viewport containing no monsters or generators.
*   **Setup**: Clean map, Player 0 at $(10, 10)$, bombs set to 1.
*   **Inputs**: Step `BUTTON_BOMB`.
*   **C Globals Assertions**:
    *   `player_bombs[0] == 0` (bomb consumed)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 1` (`SOUND_BOMB`)

#### Test 31: `test_f06_t2_bomb_max_targets`
*   **Description**: Detonating a smart bomb clears a maximum capacity of 199 monsters filling the entire 10x20 viewport (except player's tile).
*   **Setup**: Player 0 at $(10, 10)$, bombs set to 1. Fill all other 199 tiles in the $20 \times 10$ viewport (cols 0..19, rows 5..14) with `TILE_MONSTER1`.
*   **Inputs**: Step `BUTTON_BOMB`.
*   **C Globals Assertions**:
    *   All 199 monsters are cleared to `TILE_SPACE`.
    *   `player_bombs[0] == 0`.
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 1` (`SOUND_BOMB`)

#### Test 32: `test_f06_t2_bomb_partial_viewport_overlap`
*   **Description**: Smart bomb clears monsters inside the viewport, but leaves monsters just outside the viewport boundaries intact.
*   **Setup**: Player 0 at $(10, 10)$ (viewport columns 0..19, rows 5..14). Bombs set to 1. Monsters at $(19, 10)$ (inside) and $(20, 10)$ (outside).
*   **Inputs**: Step `BUTTON_BOMB`.
*   **C Globals Assertions**:
    *   `dandy_map[10 * 60 + 19] == TILE_SPACE` (cleared)
    *   `dandy_map[10 * 60 + 20] == TILE_MONSTER1` (intact)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 1` (`SOUND_BOMB`)

---

### Feature F-07: Monster Behavior

#### Test 33: `test_f07_t2_monster_rotor_exact_tick`
*   **Description**: A monster only moves on its specific sparse grid rotor tick, and remains frozen on all other 15 ticks.
*   **Setup**: Player 0 at $(10, 10)$ (viewport active). Monster 1 at $(9, 8)$. Rotor index: $(8 \pmod 4) \times 4 + (9 \pmod 4) = 1$.
*   **Inputs**:
    *   Step 1 (rotor becomes 1: monster moves to $(10, 9)$).
    *   Step 2 to 16 (rotor cycles 2..15, then 0: monster remains stationary at $(10, 9)$).
*   **C Globals Assertions**:
    *   After step 1: `dandy_map[9 * 60 + 10] == TILE_MONSTER1`
    *   After step 16: `dandy_map[9 * 60 + 10] == TILE_MONSTER1` (did not move again)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 0`

#### Test 34: `test_f07_t2_monster_slide_pathfinding`
*   **Description**: A monster slides around a wall obstacle to reach the player.
*   **Setup**: Player 0 at $(10, 10)$. Monster 1 at $(9, 8)$ (rotor index 1). Wall at $(10, 9)$ (direct diagonal path is blocked). Slide directions for monster: Up-Right $(10, 8)$ and Down-Left $(9, 9)$. Up-Right is closer to player $(10, 10)$.
*   **Inputs**: Step 1.
*   **C Globals Assertions**:
    *   Monster moves to $(10, 8)$ (slides around the wall).
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 0`

#### Test 35: `test_f07_t2_monster_nearest_player_tie`
*   **Description**: Monster pathfinds towards the nearest player. In a distance tie, it picks the lower player index.
*   **Setup**: Player 0 at $(8, 10)$, Player 1 at $(12, 10)$. Both joined and alive. Monster 1 at $(10, 9)$ (equidistant to both: Manhattan distance = 3). Rotor index: $(9 \pmod 4) \times 4 + (10 \pmod 4) = 4 + 2 = 6$.
*   **Inputs**: Step 6.
*   **C Globals Assertions**:
    *   Monster moves towards Player 0 (lower index) to $(9, 9)$.
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 0`

#### Test 36: `test_f07_t2_monster_attack_dead_player`
*   **Description**: A monster moves onto a dead player's position (which is now `TILE_SPACE`), treating it as traversable space without triggering an attack.
*   **Setup**: Player 0 at $(10, 10)$ is dead (`health = 0`, tile is `TILE_SPACE`). Player 1 is at $(1, 1)$ alive. Monster 1 at $(9, 10)$ (rotor index 9).
*   **Inputs**: Step 9.
*   **C Globals Assertions**:
    *   Monster moves onto $(10, 10)$ (no damage dealt, monster remains on map).
    *   `dandy_map[10 * 60 + 10] == TILE_MONSTER1`.
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 0` (no hit sound)

---

### Feature F-08: Generator Spawning

#### Test 37: `test_f08_t2_generator_surrounded_walls`
*   **Description**: A generator completely surrounded by walls cannot spawn monsters.
*   **Setup**: Player 0 at $(10, 10)$. Generator 1 at $(9, 8)$ (rotor index 1). Walls at $(9, 7)$, $(10, 8)$, $(9, 9)$, $(8, 8)$ (all 4 cardinal directions blocked).
*   **Inputs**: Step 1.
*   **C Globals Assertions**:
    *   No monster spawned. All surrounding tiles remain `TILE_WALL`.
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 0`

#### Test 38: `test_f08_t2_generator_surrounded_entities`
*   **Description**: A generator surrounded by items, portals, or players cannot spawn monsters (only `TILE_SPACE` is valid for spawning).
*   **Setup**: Player 0 at $(9, 7)$ (Up). Generator 1 at $(9, 8)$ (rotor 1). Keys at $(10, 8)$ (Right). Food at $(9, 9)$ (Down). Portal at $(8, 8)$ (Left).
*   **Inputs**: Step 1.
*   **C Globals Assertions**:
    *   No monster spawned.
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 0`

#### Test 39: `test_f08_t2_generator_boundary_spawn_wrap_right`
*   **Description**: Generator at the right map edge ($x=59$) wraps around and spawns a monster on the left edge of the next row ($x=0, y=my+1$).
*   **Setup**: Player 0 at $(50, 10)$ (viewport covers right edge). Generator 1 at $(59, 8)$ (rotor index: $(8 \pmod 4) \times 4 + (59 \pmod 4) = 0 \times 4 + 3 = 3$).
    *   At step 3, the LFSR seed is `0x7138`.
    *   `(0x7138 & 7) < 4` is True ($0 < 4$). `spawn_dir = 0` (Up).
    *   Up $(59, 7)$ is free $\rightarrow$ spawn monster.
    Let's block Up $(59, 7)$ and Down $(59, 9)$ and Left $(58, 8)$.
    The clockwise search order will try: Up (blocked) $\rightarrow$ Right $(60, 8)$ $\rightarrow$ Down (blocked) $\rightarrow$ Left (blocked).
    Right is $(60, 8)$, which maps to $(0, 9)$ (left edge of row 9).
    Place walls at $(59, 7)$, $(59, 9)$, $(58, 8)$.
*   **Inputs**: Step 3.
*   **C Globals Assertions**:
    *   `dandy_map[9 * 60 + 0] == TILE_MONSTER1` (monster spawned at left edge of row 9!)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 0`

#### Test 40: `test_f08_t2_generator_boundary_spawn_wrap_left`
*   **Description**: Generator at the left map edge ($x=0$) wraps around and spawns a monster on the right edge of the previous row ($x=59, y=my-1$).
*   **Setup**: Player 0 at $(5, 10)$. Generator 1 at $(0, 8)$ (rotor index: $(8 \pmod 4) \times 4 + (0 \pmod 4) = 0$).
    *   At step 16 (rotor 0), LFSR seed is `0xE270`. `spawn_dir = 0` (Up).
    *   Block Up $(0, 7)$, Down $(0, 9)$, Right $(1, 8)$.
    *   Clockwise search order: Up (blocked) $\rightarrow$ Right (blocked) $\rightarrow$ Down (blocked) $\rightarrow$ Left $(-1, 8)$, which maps to $(59, 7)$ (right edge of row 7).
    Place walls at $(0, 7)$, $(0, 9)$, $(1, 8)$.
*   **Inputs**:
    *   Step 16 empty inputs.
*   **C Globals Assertions**:
    *   `dandy_map[7 * 60 + 59] == TILE_MONSTER1` (monster spawned at right edge of row 7!)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 0`

---

### Feature F-09: Multiplayer & Viewport

#### Test 41: `test_f09_t2_camera_clamp_top_left`
*   **Description**: Viewport camera is clamped to $(0, 0)$ when player is at the top-left corner.
*   **Setup**: Player 0 at $(2, 2)$.
*   **Inputs**: Step `0` (draw viewport).
*   **C Globals Assertions**:
    *   `player_x[0] == 2`, `player_y[0] == 2`
*   **Mock HAL Assertions**:
    *   `mock_get_viewport_camera() == (0, 0)`

#### Test 42: `test_f09_t2_camera_clamp_top_right`
*   **Description**: Viewport camera is clamped to $(40, 0)$ when player is at the top-right corner.
*   **Setup**: Player 0 at $(58, 2)$.
*   **Inputs**: Step `0`.
*   **C Globals Assertions**:
    *   `player_x[0] == 58`, `player_y[0] == 2`
*   **Mock HAL Assertions**:
    *   `mock_get_viewport_camera() == (40, 0)`

#### Test 43: `test_f09_t2_camera_clamp_bottom_left`
*   **Description**: Viewport camera is clamped to $(0, 20)$ when player is at the bottom-left corner.
*   **Setup**: Player 0 at $(2, 28)$.
*   **Inputs**: Step `0`.
*   **C Globals Assertions**:
    *   `player_x[0] == 2`, `player_y[0] == 28`
*   **Mock HAL Assertions**:
    *   `mock_get_viewport_camera() == (0, 20)`

#### Test 44: `test_f09_t2_camera_clamp_bottom_right`
*   **Description**: Viewport camera is clamped to $(40, 20)$ when player is at the bottom-right corner.
*   **Setup**: Player 0 at $(58, 28)$.
*   **Inputs**: Step `0`.
*   **C Globals Assertions**:
    *   `player_x[0] == 58`, `player_y[0] == 28`
*   **Mock HAL Assertions**:
    *   `mock_get_viewport_camera() == (40, 20)`

#### Test 45: `test_f09_t2_spectator_mode_no_alive_players`
*   **Description**: In spectator mode, if all other players are also dead, the camera falls back to centering on the dead local player's last coordinates.
*   **Setup**: Player 0 at $(15, 12)$ (dead, `health = 0`). Player 1 at $(30, 20)$ (dead, `health = 0`). Player 2 and 3 not joined.
*   **Inputs**: Step `0` (draw viewport).
*   **C Globals Assertions**:
    *   `player_health[0] == 0`, `player_health[1] == 0`
*   **Mock HAL Assertions**:
    *   `mock_get_viewport_camera() == (5, 7)` ($(15-10, 12-5)$)

---

### Feature F-10: Level Transitions

#### Test 46: `test_f10_t2_portal_spawn_overlap`
*   **Description**: If a level's starting portal `TILE_UP` is at $(0, 0)$, Player 0 and Player 3 spawn offsets clamp to $(0, 0)$ and overlap. Player 3's sprite overwrites Player 0's sprite on the map, but both are logically present at $(0, 0)$.
*   **Setup**: Level 0 loaded. Edit map to place `TILE_UP` at $(0, 0)$. Join Player 1, 2, 3.
    *   Spawn offsets:
        *   P0: $(0, -1) \rightarrow (0, 0)$ (clamped)
        *   P1: $(1, 0) \rightarrow (1, 0)$
        *   P2: $(0, 1) \rightarrow (0, 1)$
        *   P3: $(-1, 0) \rightarrow (0, 0)$ (clamped)
*   **Inputs**: Step `0` (triggers load starting positions).
*   **C Globals Assertions**:
    *   `player_x[0] == 0`, `player_y[0] == 0`
    *   `player_x[3] == 0`, `player_y[3] == 0`
    *   `dandy_map[0] == TILE_PLAYER1 + 24` (Player 3 tile facing Up, overwrote Player 0's tile `TILE_PLAYER1`)
*   **Mock HAL Assertions**:
    *   `mock_get_viewport_camera() == (0, 0)`
    *   Both Player 0 and Player 3 sprites are registered at viewport coordinate $(0, 0)$ in the hardware sprite list.

#### Test 47: `test_f10_t2_stats_carry_over`
*   **Description**: Health, Score, Bombs, and Keys are perfectly preserved across a level transition.
*   **Setup**: Player 0 at $(10, 10)$. Health = 150, Score = 500, Bombs = 3, Keys = 2. Stairs at $(11, 10)$.
*   **Inputs**: Step `BUTTON_RIGHT`.
*   **C Globals Assertions**:
    *   `current_level == 1`
    *   `player_health[0] == 150`
    *   `player_score[0] == 500`
    *   `player_bombs[0] == 3`
    *   `player_keys[0] == 2`
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 1` (`SOUND_WARP`)

#### Test 48: `test_f10_t2_arrows_destroyed_on_warp`
*   **Description**: Active arrows are destroyed when a level transition occurs.
*   **Setup**: Player 0 at $(10, 10)$. Facing Right. Stairs at $(12, 10)$.
*   **Inputs**:
    1. Step `BUTTON_FIRE` (fires arrow, arrow at $(11, 10)$, stairs at $(12, 10)$).
    2. Step `BUTTON_RIGHT` (player moves to $(11, 10)$).
    3. Step `BUTTON_RIGHT` (player moves to $(12, 10)$, triggers warp).
*   **C Globals Assertions**:
    *   `current_level == 1`
    *   `arrow_dir[0] == -1` (destroyed)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 2` (`SOUND_SHOOT`, `SOUND_WARP`)

#### Test 49: `test_f10_t2_invalid_level_index_corrupt`
*   **Description**: Investigates/Documents boundary risk where an invalid level index ($level\_idx = 5$, out of bounds) is programmatically loaded, reading a garbage pointer and causing a crash. (Written as a defensive check asserting that loading an invalid level index is handled or prevented).
*   **Setup**: Fresh environment.
*   **Inputs**: Call `load_level(5)` directly.
*   **Expected Outcome**: Since `dandy_levels` has only 5 elements, accessing index 5 reads out-of-bounds ROM memory. E2E environment should raise a segmentation fault or memory access error in ctypes.
*   **C Globals Assertions**:
    *   (N/A - Program crashes or raises OSError/ArgumentError in Python wrapper).
*   **Mock HAL Assertions**:
    *   (N/A).

---

## 4. Tier 3: Cross-Feature Interactions (8 Tests)

### Test 50: `test_f05_f06_arrow_triggers_smart_bomb`
*   **Description**: An arrow hits a `TILE_BOMB` tile, triggering a viewport smart bomb explosion that clears all monsters/generators in the viewport without consuming the player's inventory bombs.
*   **Setup**: Player 0 at $(10, 10)$ facing Right. Bombs = 0. Bomb tile at $(12, 10)$. Monster 1 at $(10, 8)$ (inside viewport).
*   **Inputs**:
    1. Step `BUTTON_FIRE` (fires arrow, arrow at $(11, 10)$).
    2. Step `0` (arrow moves to $(12, 10)$, hits the bomb tile. This triggers `do_bomb(0)`).
*   **C Globals Assertions**:
    *   `player_bombs[0] == 0` (inventory bombs remain 0)
    *   `arrow_dir[0] == -1` (arrow destroyed)
    *   `dandy_map[10 * 60 + 12] == TILE_SPACE` (bomb tile cleared)
    *   `dandy_map[8 * 60 + 10] == TILE_SPACE` (monster in viewport cleared!)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 2` (`SOUND_SHOOT` on step 1, `SOUND_HIT` on step 2. Note: smart bomb triggered by arrow plays `SOUND_HIT` rather than `SOUND_BOMB` because it is an arrow strike!).

---

### Test 51: `test_f03_f07_food_collect_monster_attack_simultaneous`
*   **Description**: Player moves onto a food tile, and in the same tick, a monster moves onto the player's new position. The player successfully gains 100 HP, then takes damage from the monster.
*   **Setup**: Player 0 at $(10, 10)$ with 50 HP. Food at $(11, 10)$. Monster 1 at $(12, 10)$ (rotor index: $(10 \pmod 4) \times 4 + (12 \pmod 4) = 8 + 0 = 8$).
*   **Inputs**:
    *   Step 8 with `BUTTON_RIGHT` (player moves to $(11, 10)$ and collects food. Then monster at $(12, 10)$ ticks on rotor 8, pathfinds to player at $(11, 10)$, deals 10 damage, and is removed).
*   **C Globals Assertions**:
    *   `player_x[0] == 11`, `player_y[0] == 10`
    *   `player_health[0] == 140` ($50 + 100 - 10 = 140$)
    *   `dandy_map[10 * 60 + 12] == TILE_SPACE` (monster removed)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 2` (`SOUND_FOOD`, `SOUND_HIT`)

---

### Test 52: `test_f04_f07_monster_pathfind_door_unlocked`
*   **Description**: Monster is blocked by a closed door. Player unlocks the door, and the monster immediately pathfinds through the newly opened space.
*   **Setup**: Player 0 at $(10, 10)$ with 1 key. Door at $(11, 10)$. Monster 1 at $(12, 10)$ (rotor index 8). The monster is blocked by the door.
*   **Inputs**:
    *   Step 8 with `BUTTON_RIGHT` (player moves to $(11, 10)$, consumes key, door network cleared. Monster is processed next in the same tick, sees path is now `TILE_SPACE`/Player, moves onto $(11, 10)$ and attacks player).
*   **C Globals Assertions**:
    *   `player_keys[0] == 0`
    *   `player_health[0] == 90` (took 10 damage)
    *   Monster removed from map.
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 2` (`SOUND_KEY`, `SOUND_HIT`)

---

### Test 53: `test_f01_f10_cooldown_carried_over_warp`
*   **Description**: Player steps onto stairs to transition levels. Their move cooldown timer is carried over and not reset, preventing immediate movement in the next level if the timer hasn't expired.
*   **Setup**: Player 0 at $(10, 10)$. Stairs at $(11, 10)$.
*   **Inputs**:
    1. Step `BUTTON_RIGHT` (player moves to $(11, 10)$, move timer becomes 3, warp triggered, next level loaded).
    2. Step `BUTTON_RIGHT` in the new level (move timer is 2, player is blocked by cooldown, does not move).
*   **C Globals Assertions**:
    *   After step 1: `current_level == 1`, `player_move_timer[0] == 2` (cooldown active)
    *   After step 2: Player coordinates are still at Level 1 starting portal, `player_move_timer[0] == 1`
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 1` (`SOUND_WARP`)

---

### Test 54: `test_f05_f07_arrow_intercepts_moving_monster`
*   **Description**: Player shoots an arrow at an incoming monster. The arrow and monster are moving towards each other. The arrow moves first and hits the monster, destroying both before the monster can move or attack.
*   **Setup**: Player 0 at $(10, 10)$ facing Right. Monster 1 at $(12, 10)$ (rotor index 8).
*   **Inputs**:
    1. Step 8 with `BUTTON_FIRE` (P0 fires arrow. Arrow spawns at $(11, 10)$. In the same tick:
        - `move_arrows()` runs, arrow moves to $(12, 10)$ and hits the monster. Monster is destroyed/replaced by space, arrow destroyed.
        - `move_monsters()` runs next, but monster at $(12, 10)$ is already dead, so no attack/movement occurs).
*   **C Globals Assertions**:
    *   `arrow_dir[0] == -1` (destroyed)
    *   `dandy_map[10 * 60 + 12] == TILE_SPACE` (monster destroyed)
    *   `player_health[0] == 100` (no damage taken)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 2` (`SOUND_SHOOT`, `SOUND_HIT`)

---

### Test 55: `test_f08_f07_spawned_monster_no_immediate_move`
*   **Description**: A generator spawns a monster. The newly spawned monster does not move or attack in the same tick it was spawned, even if its coordinate matches the active rotor tick.
*   **Setup**: Player 0 at $(10, 10)$. Generator 1 at $(9, 8)$ (rotor index 1).
    *   At step 1, the generator ticks and spawns a monster at $(9, 7)$.
    *   The rotor index for $(9, 7)$ is $(7 \pmod 4) \times 4 + (9 \pmod 4) = 3 \times 4 + 1 = 13$.
    *   Even though the step is tick 1, the monster's rotor is 13, so it wouldn't tick anyway. What if the monster rotor is 1?
    *   Rotor index for $(9, 9)$ is $(9 \pmod 4) \times 4 + (9 \pmod 4) = 4 + 1 = 5$.
    *   In all cases, the row-by-row grid scan has already passed row 7 or row 9 is skipped by the sparse grid step of 4.
*   **Inputs**: Step 1.
*   **C Globals Assertions**:
    *   Monster spawned at $(9, 7)$.
    *   Monster remains at $(9, 7)$ (does not move).
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 0`

---

### Test 56: `test_f05_f08_arrow_interrupts_spawn`
*   **Description**: Player shoots an arrow at a generator that is scheduled to spawn a monster in this tick. The arrow hits and destroys the generator in `move_arrows()`, preventing the spawn in the subsequent `move_monsters()`.
*   **Setup**: Player 0 at $(10, 8)$ facing Left. Generator 1 at $(8, 8)$ (rotor index 0).
*   **Inputs**:
    *   Step 16 with `BUTTON_FIRE` (P0 fires arrow Left. Arrow spawns at $(9, 8)$. In the same tick:
        - `move_arrows()` runs, arrow moves to $(8, 8)$ and destroys generator.
        - `move_monsters()` runs next. Since generator at $(8, 8)$ is now `TILE_SPACE`, no spawning occurs).
*   **C Globals Assertions**:
    *   `arrow_dir[0] == -1` (destroyed)
    *   `dandy_map[8 * 60 + 8] == TILE_SPACE` (generator destroyed)
    *   No monster spawned around $(8, 8)$.
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 2` (`SOUND_SHOOT`, `SOUND_HIT`)

---

### Test 57: `test_f09_f10_warp_with_dead_player`
*   **Description**: In a 2-player game, Player 1 is dead. Player 0 transitions to the next level. In the new level, both players are spawned at the portal, meaning the dead player's sprite is placed on the map despite their dead status.
*   **Setup**: Level 0 loaded. Player 0 at $(10, 10)$ alive. Player 1 at $(1, 1)$ dead (`health = 0`, joined = True). Stairs at $(11, 10)$.
*   **Inputs**: Step `BUTTON_RIGHT`.
*   **C Globals Assertions**:
    *   `current_level == 1`
    *   `player_health[1] == 0` (remains dead)
    *   Player 1 coordinates set to Level 1 portal offset: `player_x[1] == up_x + 1`, `player_y[1] == up_y`
    *   `dandy_map[up_y * 60 + (up_x + 1)] == TILE_PLAYER1 + 8` (Player 1 sprite placed on map!)
*   **Mock HAL Assertions**:
    *   `mock_get_sound_count() == 1` (`SOUND_WARP`)

---

## 5. Verification & Execution Plan

To verify these test case designs, a test implementer should:
1.  **Add Test Cases**: Append these 57 tests to a new test suite file, e.g., `dandy-gb/tests/test_tier2_tier3.py`.
2.  **Compile the Shared Library**: Run `make test_lib` in the `dandy-gb/` directory to build a fresh copy of `libdandy_test.so`.
3.  **Run the Test Suite**: Execute the Python test runner:
    ```bash
    python3 -m unittest dandy-gb/tests/test_tier2_tier3.py
    ```
4.  **Confirm Isolation**: Verify that the `DandyEnv` class correctly creates unique temporary copies of `libdandy_test.so` for each test case, ensuring no persistent state leakage (especially for the LFSR `rand_seed` static variable).
5.  **Address Vulns**: If any test fails due to the identified vulnerabilities (OOB generator spawning, stack limits, or health overflows), it confirms the engine's bugs. These should be documented or addressed in the engine source code as appropriate.
