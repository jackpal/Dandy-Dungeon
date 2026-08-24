# Verification & Coverage Report (Milestone 2)

We have successfully implemented the Tier 1 Happy-Path Feature Coverage test suite for the Dandy Dungeon project at `dandy-gb/tests/test_tier1.py`. The suite is fully production-grade, isolated, and passes all tests successfully.

## 1. Test Suite Summary
- **Test File**: `dandy-gb/tests/test_tier1.py`
- **Number of Test Cases**: Exactly **50 distinct test cases** (5 per feature for F-01 to F-10).
- **Double-Assert Rule**: 100% compliance. Every single test case asserts BOTH:
  1. Engine's internal globals (coordinates, health, score, keys, map tiles, arrow, etc.).
  2. Mock HAL's side effects (sound effects, viewport drawings, camera coordinates, active hardware sprites).
- **Isolation**: Each test case loads a unique copy of the `libdandy_test.so` shared library on disk to guarantee 100% isolation of internal static variables (like the random seed and button history).

## 2. Feature Coverage & Implementation Details

### F-01 (Movement & Timing) — 5 Test Cases
- `test_f01_move_success_cardinal`: Verified that cardinal moves update coordinates, update map tiles, set direction, and set the move timer to 3. Viewport is drawn, camera centers, and active player hardware sprite is registered.
- `test_f01_move_success_diagonal`: Verified diagonal movement.
- `test_f01_move_cooldown_blocking`: Verified that holding inputs is blocked during the 4-tick cooldown, moving exactly once every 4 ticks.
- `test_f01_unjoined_player_ignored`: Verified that inputs for unjoined players are ignored.
- `test_f01_dead_player_ignored`: Verified that dead players (health <= 0) ignore inputs. Joint player 1 to prevent global game over reset.

### F-02 (Slide Mechanics) — 5 Test Cases
- `test_f02_slide_cardinal_blocked_clockwise`: Verified that a blocked cardinal move slides player Down-Right (clockwise) if free.
- `test_f02_slide_cardinal_blocked_counterclockwise`: Verified sliding Up-Right (counter-clockwise).
- `test_f02_slide_diagonal_blocked_clockwise`: Verified that a blocked diagonal move slides player Right if free.
- `test_f02_slide_diagonal_blocked_counterclockwise`: Verified sliding Up.
- `test_f02_slide_all_blocked`: Verified that if all adjacent directions are blocked, player remains stationary.

### F-03 (Item Collection) — 5 Test Cases
- `test_f03_collect_food`: Verified collecting food adds 100 HP, plays `SOUND_FOOD`, and can exceed 100 HP.
- `test_f03_collect_money`: Verified money adds 100 score, plays `SOUND_KEY`.
- `test_f03_collect_key`: Verified key adds 1 key, plays `SOUND_KEY`.
- `test_f03_collect_bomb`: Verified bomb adds 1 bomb, plays `SOUND_KEY`.
- `test_f03_collect_multiple_items`: Verified sequence of collecting food and key, asserting both HP/key updates and sound logs.

### F-04 (Door & Key) — 5 Test Cases
- `test_f04_door_blocked_with_no_key`: Verified door blocks movement when player has 0 keys. Placed walls diagonally to prevent slide deflection.
- `test_f04_door_unlock_single`: Verified unlocking isolated door consumes 1 key, turns door to space, and plays `SOUND_KEY`.
- `test_f04_door_flood_fill_horizontal`: Verified horizontal contiguous doors are flood-filled and cleared using 1 key.
- `test_f04_door_flood_fill_diagonal`: Verified diagonally-connected doors are flood-filled and cleared.
- `test_f04_door_flood_fill_large_network`: Verified a 2x3 block of doors is cleared in a single tick.

### F-05 (Combat & Projectiles) — 5 Test Cases
- `test_f05_shoot_arrow_empty_space`: Verified shooting arrow spawns it in front in the same tick, plays `SOUND_SHOOT`.
- `test_f05_arrow_flight`: Verified arrow moves 1 tile per tick.
- `test_f05_arrow_hit_wall`: Verified arrow hitting wall is destroyed.
- `test_f05_arrow_hit_monster_degrade`: Verified arrow degrades level 2 monster to level 1 and plays `SOUND_HIT`.
- `test_f05_arrow_hit_generator_destroy`: Verified arrow destroys generator to space, plays `SOUND_HIT`.

### F-06 (Smart Bomb) — 5 Test Cases
- `test_f06_bomb_no_bombs`: Verified bomb input with 0 bombs has no effect.
- `test_f06_bomb_success_clears_monsters`: Verified bomb clears all viewport monsters, plays `SOUND_BOMB`.
- `test_f06_bomb_success_clears_generators`: Verified bomb clears all viewport generators.
- `test_f06_bomb_does_not_affect_outside`: Verified off-screen monsters and generators are unaffected.
- `test_f06_bomb_by_shooting_bomb_tile`: Verified arrow hitting bomb tile triggers viewport explosion.

### F-07 (Monster Behavior) — 5 Test Cases
- `test_f07_monster_pathfinding_towards_player`: Verified monster moves towards player on its active rotor tick. Placed at deterministic rotor coordinates.
- `test_f07_monster_contact_damage`: Verified level 1 monster deals 10 damage, plays `SOUND_HIT`, and is removed.
- `test_f07_monster_contact_damage_by_level`: Verified level 3 monster deals 30 damage.
- `test_f07_player_death_removes_tile`: Verified player death (HP=0) clears player tile from map and plays `SOUND_DIE`. Joined player 1 as a spectator to prevent immediate level reset.
- `test_f07_off_screen_monster_frozen`: Verified off-screen monster remains frozen on its active rotor tick.

### F-08 (Generator Spawning) — 5 Test Cases
- `test_f08_generator_spawn_level1`: Verified generator spawns level 1 monster in adjacent space on seed tick.
- `test_f08_generator_spawn_level3`: Verified generator spawns level 3 monster.
- `test_f08_generator_spawn_dir_blocked`: Verified generator spawns in next clockwise direction if primary is blocked.
- `test_f08_generator_off_screen_frozen`: Verified off-screen generator remains frozen.
- `test_f08_generator_no_spawn_on_fail_tick`: Placed three generators to tick concurrently. Gen 1 and 2 spawn, Gen 3 fails spawning due to LFSR seed check.

### F-09 (Multiplayer & Viewport) — 5 Test Cases
- `test_f09_multiplayer_join`: Verified joining players 1, 2, and 3 spawns them at correct offsets around the start portal. Looked up portal coordinates dynamically to avoid hardcoding.
- `test_f09_camera_centering`: Verified camera centers on local player coordinates.
- `test_f09_camera_clamping_left_top`: Verified camera clamps to (0, 0) at map top-left.
- `test_f09_camera_clamping_right_bottom`: Verified camera clamps to (40, 20) at map bottom-right.
- `test_f09_spectator_mode`: Verified that when local player dies, camera centers on the centroid of remaining alive players.

### F-10 (Level Transitions) — 5 Test Cases
- `test_f10_stairs_loads_next_level`: Verified stepping on stairs loads next level, plays `SOUND_WARP`, resets coordinates.
- `test_f10_next_level_clamps_at_max`: Verified stairs at level 4 clamps and reloads.
- `test_f10_game_over_resets_to_level_0`: Verified player death resets level to 0, wipes inventory/score, and reloads level 0 portal. Dynamically resolved level 0 portal coordinates.
- `test_f10_game_over_clears_inventories_multiplayer`: Verified all players dying resets game state.
- `test_f10_manual_level_load`: Verified load_level dynamically loads map without playing warp sound.
