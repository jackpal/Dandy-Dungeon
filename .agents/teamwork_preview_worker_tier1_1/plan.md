# Execution Plan - Tier 1 Happy-Path Feature Coverage Test Suite (Milestone 2)

We will implement a comprehensive, production-grade Python unit test suite at `dandy-gb/tests/test_tier1.py` containing exactly 50 test cases (5 per feature for F-01 to F-10). Every test case will strictly follow the **Double-Assert Rule**, asserting both the internal global engine state and the mock HAL side effects (draws, sounds, sprites, camera, HUD).

## Step 1: Draft the Test Suite Structure
We will create `dandy-gb/tests/test_tier1.py` with:
- Standard Python `unittest` skeleton.
- Import of `DandyEnv` from `dandy_env`.
- Helper methods for setting up clean custom maps and verifying common double-assertions to keep code DRY and highly readable.

## Step 2: Implement F-01 (Movement & Timing) Tests (5 cases)
- `test_f01_move_success_cardinal`: Standard cardinal movement on space.
- `test_f01_move_success_diagonal`: Standard diagonal movement on space.
- `test_f01_move_cooldown_blocking`: 4-tick move cooldown blocking inputs.
- `test_f01_unjoined_player_ignored`: Inputs for unjoined players are ignored.
- `test_f01_dead_player_ignored`: Inputs for dead players are ignored.

## Step 3: Implement F-02 (Slide Mechanics) Tests (5 cases)
- `test_f02_slide_cardinal_blocked_clockwise`: Cardinal move blocked, slides clockwise.
- `test_f02_slide_cardinal_blocked_counterclockwise`: Cardinal move blocked, slides counter-clockwise.
- `test_f02_slide_diagonal_blocked_clockwise`: Diagonal move blocked, slides clockwise.
- `test_f02_slide_diagonal_blocked_counterclockwise`: Diagonal move blocked, slides counter-clockwise.
- `test_f02_slide_all_blocked`: All directions blocked, player stationary.

## Step 4: Implement F-03 (Item Collection) Tests (5 cases)
- `test_f03_collect_food`: Food adds +100 health, plays food sound.
- `test_f03_collect_money`: Money adds +100 score, plays key sound.
- `test_f03_collect_key`: Key adds +1 key, plays key sound.
- `test_f03_collect_bomb`: Bomb adds +1 bomb, plays key sound.
- `test_f03_collect_multiple_items`: Sequence of item collections.

## Step 5: Implement F-04 (Door & Key Mechanics) Tests (5 cases)
- `test_f04_door_blocked_with_no_key`: Moving onto door with 0 keys is blocked.
- `test_f04_door_unlock_single`: Unlocking isolated door consumes 1 key and plays sound.
- `test_f04_door_flood_fill_horizontal`: Horizontal contiguous doors flood-filled and cleared.
- `test_f04_door_flood_fill_diagonal`: Diagonally-connected doors flood-filled and cleared.
- `test_f04_door_flood_fill_large_network`: A 2x3 block of doors cleared with a single key.

## Step 6: Implement F-05 (Combat & Projectiles) Tests (5 cases)
- `test_f05_shoot_arrow_empty_space`: Shoot arrow, spawns in front, plays sound.
- `test_f05_arrow_flight`: Arrow moves 1 tile per tick.
- `test_f05_arrow_hit_wall`: Arrow hitting solid wall is destroyed.
- `test_f05_arrow_hit_monster_degrade`: Arrow degrades level 2 monster to level 1 and plays hit sound.
- `test_f05_arrow_hit_generator_destroy`: Arrow destroys generator to space, plays hit sound.

## Step 7: Implement F-06 (Smart Bomb Action) Tests (5 cases)
- `test_f06_bomb_no_bombs`: Pressing bomb with 0 bombs does nothing.
- `test_f06_bomb_success_clears_monsters`: Clears monsters in viewport, plays bomb sound.
- `test_f06_bomb_success_clears_generators`: Clears generators in viewport, plays bomb sound.
- `test_f06_bomb_does_not_affect_outside`: Off-screen monsters/generators unaffected.
- `test_f06_bomb_by_shooting_bomb_tile`: Arrow hitting bomb tile triggers smart bomb.

## Step 8: Implement F-07 (Monster Behavior) Tests (5 cases)
- `test_f07_monster_pathfinding_towards_player`: Monster moves towards player on its active rotor tick.
- `test_f07_monster_contact_damage`: Monster level 1 deals 10 damage and plays hit sound.
- `test_f07_monster_contact_damage_by_level`: Monster level 3 deals 30 damage and plays hit sound.
- `test_f07_player_death_removes_tile`: Player dying removes player tile and plays die sound.
- `test_f07_off_screen_monster_frozen`: Off-screen monster remains frozen on its rotor tick.

## Step 9: Implement F-08 (Generator Spawning) Tests (5 cases)
- `test_f08_generator_spawn_level1`: Generator spawns level 1 monster in adjacent space on seed tick.
- `test_f08_generator_spawn_level3`: Generator spawns level 3 monster on seed tick.
- `test_f08_generator_spawn_dir_blocked`: Generator spawns in next clockwise direction if primary is blocked.
- `test_f08_generator_off_screen_frozen`: Off-screen generator remains frozen and does not spawn.
- `test_f08_generator_no_spawn_on_fail_tick`: Third generator tick does not spawn due to LFSR seed check.

## Step 10: Implement F-09 (Multiplayer & Viewport) Tests (5 cases)
- `test_f09_multiplayer_join`: Joining multiple players at offsets around portal.
- `test_f09_camera_centering`: Camera centered around player 0.
- `test_f09_camera_clamping_left_top`: Camera clamped to (0,0) at map top-left.
- `test_f09_camera_clamping_right_bottom`: Camera clamped to (40,20) at map bottom-right.
- `test_f09_spectator_mode`: Camera centers on centroid of remaining alive players when local player dies.

## Step 11: Implement F-10 (Level Transitions) Tests (5 cases)
- `test_f10_stairs_loads_next_level`: Stepping on stairs increments level and warps to portal.
- `test_f10_next_level_clamps_at_max`: Warping on final level clamps level and reloads.
- `test_f10_game_over_resets_to_level_0`: Single player dying resets progress, stats, and reloads level 0.
- `test_f10_game_over_clears_inventories_multiplayer`: All players dying resets game state and reloads level 0.
- `test_f10_manual_level_load`: Programmatic level loading resets player coordinates to portal.

## Step 12: Run and Verify the Test Suite
- Execute `make test` inside the `dandy-gb/` directory.
- Check test discovery and output logs to ensure all 50 tests pass.
- Fix any issues, lint errors, or style guide non-compliance.
- Document changes in `changes.md` and write a formal `handoff.md`.
