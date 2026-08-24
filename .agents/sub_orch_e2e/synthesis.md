# Synthesized E2E Test Suite Design: Tiers 2 & 3

This document synthesizes the findings and test case specifications from the three Explorer subagents. These tests evaluate the core C engine (`dandy_core.c`) under extreme boundaries, limitations, and cross-system interactions.

---

## 1. Core Engine Architectural Constraints & Discoveries

The Explorers identified the following critical engine constraints, which must be explicitly validated by the test suite:
1. **FLOOD_STACK_SIZE = 64 (F-04)**: The non-recursive door flood-fill is capped at 64. If a contiguous door network exceeds 64 tiles, only 64 are cleared. The remaining doors stay locked.
2. **Blocked Cooldown (F-01/F-02)**: The movement cooldown timer is set to `TICKS_PER_MOVE` (4) before movement checks are executed. Completely blocked movements still incur a 4-tick cooldown.
3. **Arrow Self-Collision (F-05)**: Firing an arrow and moving cardinally in the same direction on the same tick causes the arrow (starting at the player's old coordinate) to step into the player's new coordinate, colliding with the player tile and destroying itself.
4. **Off-Screen Freezing (F-07/F-08)**: Monsters and generators outside any active player's 10x20 viewport are frozen. Their positions do not update, and generators do not tick their LFSR seed.
5. **Arrow Viewport Check (F-05)**: Viewport boundaries are checked *before* hitting destructibles. Targets outside the player's viewport are immune to arrow damage.
6. **Hardware Sprite Cap of 40 (F-09)**: The viewport renderer registers a maximum of 40 hardware sprites; any additional visible entities are not registered as sprites.
7. **Health Overflow (F-03)**: Player health is a signed 16-bit integer (`int16_t`). Collecting food adds 100 HP. Exceeding `32767` overflows to a negative value, triggering instant death on the next tick.
8. **Generator Wrap-Around (F-08)**: Generator spawning does not check coordinate boundaries, resulting in row-wrapping at X-axis edges (X=59 wraps to X=0 of the next row) and out-of-bounds reads at Y-axis edges.
9. **Spectator Centroid Protection (F-09)**: Centroid camera centering is protected against division-by-zero when all players are dead, falling back to centering on the dead local player's coordinate.
10. **Portal Offset Clamping (F-10)**: Portals at (0,0) clamp player starting offsets, causing players to overlap logically and visually.

---

## 2. Tier 2: Boundary & Corner Cases (45 Test Cases)
These must be implemented in `dandy-gb/tests/test_tier2.py`.

### F-01: Movement & Timing
1. `test_f01_t2_move_clamp_top`: Player moving Up at $y=0$ clamps coordinate.
2. `test_f01_t2_move_clamp_bottom`: Player moving Down at $y=29$ clamps coordinate.
3. `test_f01_t2_move_clamp_left`: Player moving Left at $x=0$ clamps coordinate.
4. `test_f01_t2_move_clamp_right`: Player moving Right at $x=59$ clamps coordinate.
5. `test_f01_t2_move_diagonal_clamp`: Player moving diagonally (e.g. Up-Left at (0,0)) clamps coordinate.
6. `test_f01_t2_conflicting_cardinal_input`: Pressing LEFT+RIGHT or UP+DOWN results in no movement and no cooldown.
7. `test_f01_t2_all_directions_pressed`: Pressing all 4 directions results in no movement and no cooldown.

### F-02: Slide Mechanics
8. `test_f02_t2_slide_blocked_both_adjacent`: Moving cardinally when target and both adjacent slide offsets are blocked results in no movement, but incurs a 4-tick cooldown.
9. `test_f02_t2_slide_boundary_clamp_top`: Moving Up-Right at top boundary ($y=0$) when Right is blocked. Top is out of bounds, so player stays stationary.
10. `test_f02_t2_slide_boundary_clamp_bottom`: Moving Left (blocked by wall) at bottom boundary ($y=29$). Slid Up-Left (free) successfully.
11. `test_f02_t2_slide_boundary_clamp_left`: Moving Left (blocked by wall) at left boundary ($x=1$). Up-Left is blocked, Down-Left is free; slides Down-Left.
12. `test_f02_t2_slide_boundary_clamp_right`: Moving Right (blocked by wall) at right boundary ($x=58$). Up-Right is blocked, Down-Right is free; slides Down-Right.
13. `test_f02_t2_slide_clockwise_priority`: When moving cardinal blocked and both adjacent are free, verify search priority order.

### F-03: Item Collection
14. `test_f03_t2_collect_food_health_overflow`: Player with 32700 HP collects food (+100). Health overflows to -32736, and player dies on the next tick.
15. `test_f03_t2_collect_money_score_wrap`: Player with 65500 score collects money (+100). Score wraps to 64 (uint16_t).
16. `test_f03_t2_collect_key_wrap`: Player with 255 keys collects key. Keys count wraps to 0 (uint8_t).
17. `test_f03_t2_collect_bomb_wrap`: Player with 255 bombs collects bomb. Bombs count wraps to 0 (uint8_t).
18. `test_f03_t2_collect_item_at_health_0`: Dead player (health 0) cannot collect items; items remain on the map.

### F-04: Door & Key Mechanics
19. `test_f04_t2_door_flood_fill_stack_overflow`: Contiguous door network of 80 door tiles. Unlocking consumes 1 key. Exactly 64 doors are cleared; 16 doors at the far end remain locked.
20. `test_f04_t2_door_flood_fill_circular`: A circular ring of doors is completely cleared by a single unlock without infinite looping.
21. `test_f04_t2_door_flood_fill_boundary`: Door network touching map boundaries clears successfully.
22. `test_f04_t2_door_unlock_multi_key`: Unlocking a large door network consumes exactly 1 key.
23. `test_f04_t2_door_unlock_no_key_blocked_slide`: Moving into door with 0 keys and blocked slide offsets leaves player stationary.

### F-05: Combat & Projectiles
24. `test_f05_t2_arrow_destructible_outside_viewport`: Destructibles outside the 10x20 active viewport are immune to arrow damage because arrows destroy themselves at the viewport edge.
25. `test_f05_t2_arrow_destroy_at_map_boundary`: Arrow shot at map edge destroys itself on boundary.
26. `test_f05_t2_arrow_destroy_at_wall`: Arrow hitting wall destroys itself and plays `SOUND_HIT`.
27. `test_f05_t2_arrow_hit_destructible_types`: Shooting at:
    - Generator: Replaces generator with `TILE_SPACE`.
    - Heart: Degrades into `TILE_MONSTER3`.
    - Monster 3/2: Degrades tile level by 1.
    - Monster 1: Replaces with `TILE_SPACE`.
    - Bomb Tile: Triggers viewport smart bomb.
28. `test_f05_t2_shoot_no_active_arrow`: Verify that pressing fire when an arrow is already active does nothing.

### F-06: Smart Bomb
29. `test_f06_t2_smart_bomb_clears_viewport_only`: Smart bomb clears all monsters/generators inside player's 10x20 viewport, leaving those outside untouched.
30. `test_f06_t2_smart_bomb_no_entities`: Viewport-wide bomb with no monsters/generators inside viewport consumes 1 bomb, plays sound, does not crash.
31. `test_f06_t2_smart_bomb_no_bombs`: Pressing bomb button with 0 bombs does nothing.

### F-07: Monster Behavior
32. `test_f07_t2_monster_off_screen_freeze`: Monsters outside any active player's viewport do not move.
33. `test_f07_t2_monster_damage_scale`: Monster colliding with player deals $10 \times (\text{monster\_level})$ damage.
34. `test_f07_t2_monster_pathfinding_blocked`: Monster with completely blocked path to player remains stationary.
35. `test_f07_t2_monster_rotor_ticks`: Monsters move only on their designated 16-tick sparse grid rotor ticks.

### F-08: Generator Spawning
36. `test_f08_t2_generator_off_screen_freeze`: Generators outside player's viewport are frozen (no spawn, seed does not update).
37. `test_f08_t2_generator_surrounded`: Generator completely surrounded by walls cannot spawn a monster.
38. `test_f08_t2_generator_spawning_lfsr_determinism`: LFSR starts at `0xACE1`. Verify exact spawn ticks and directions on a fresh run.
39. `test_f08_t2_generator_spawn_wrap_around_x`: Generator at $x=59$ (right edge) spawning Right wraps around to $x=0$ of the next row.

### F-09: Multiplayer & Viewport
40. `test_f09_t2_viewport_hardware_sprite_limit`: If 50 monsters are in view, exactly 40 hardware sprites are registered.
41. `test_f09_t2_spectator_centroid_averaging`: When local player is dead, camera centers on the centroid of remaining alive players.
42. `test_f09_t2_spectator_all_dead`: When all players are dead, camera defaults to local dead player's coordinate.
43. `test_f09_t2_camera_clamping_corners`: Viewport camera clamps correctly to map boundaries at all 4 corners.

### F-10: Level Transitions
44. `test_f10_t2_level_transition_state_retention`: Health, score, keys, bombs, and movement timers carry over; active arrows are destroyed.
45. `test_f10_t2_level_portal_overlap`: When starting portal is at (0,0), players overlap at (0,0) without crashing.

---

## 3. Tier 3: Cross-Feature Interactions (8 Test Cases)
These must be implemented in `dandy-gb/tests/test_tier3.py`.

1. `test_f03_f07_t3_combat_and_food`: Player is attacked by a monster and collects food in the same tick; health is updated correctly (adds 100, subtracts $10 \times \text{level}$).
2. `test_f05_f06_t3_arrow_hits_bomb_tile`: Player shoots an arrow at a bomb tile, which triggers a smart bomb explosion, clearing the viewport.
3. `test_f01_f05_t3_shoot_while_moving_cardinal`: Player fires and moves in the same cardinal direction on the same tick; arrow starts at old coordinates, steps into player's new coordinates, causing a self-collision and self-destruction.
4. `test_f01_f05_t3_shoot_while_moving_perpendicular`: Player fires Up while moving Right; arrow and player move independently and do not collide.
5. `test_f04_f07_t3_monster_follows_through_open_door`: A monster tracks and moves through a door tile that the player unlocked in the previous tick.
6. `test_f03_f04_t3_key_pickup_and_unlock`: Player walks onto a key and immediately unlocks a door in a single motion (e.g. key at (10,10), door at (11,10)).
7. `test_f07_f09_t3_monsters_target_closest_player`: Two active players are joined; monsters split targeting, each tracking their nearest player by Manhattan distance.
8. `test_f08_f10_t3_generator_spawn_during_transition`: A generator is about to spawn on its rotor tick, but the player steps onto stairs; the transition aborts the spawn and loads the new level.

---

## 4. Quality & Assertion Standards

- **Double-Assert Rule**: Every test case must verify state changes in BOTH the engine's globals (e.g., `player_x`, `player_health`, `player_keys`, `dandy_map`) and the mock HAL logs (e.g., `mock_get_sound_count()`, `mock_get_draws()`, `mock_get_sprites()`).
- **Isolation**: Each test case must instantiate a fresh `DandyEnv()` to ensure absolute state isolation.
