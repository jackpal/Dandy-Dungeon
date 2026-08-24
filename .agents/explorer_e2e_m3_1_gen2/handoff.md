# Handoff Report: Dandy Dungeon E2E Test Suite Design (Milestone 3)

This report provides the read-only analysis, logic chains, and concrete E2E test designs for Milestone 3 of the Dandy Dungeon Testing Track.

---

## 1. Observation

During the read-only investigation of the Dandy Dungeon C codebase and Python test runner, the following exact code structures, boundary limits, and behaviors were observed:

### A. Flood Fill Stack Limits
In `dandy-gb/src/dandy_core.c:98-109`, the stack for the non-recursive flood fill is declared with a fixed size of 64:
```c
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
```
If `flood_stack_ptr` reaches 64, any further pushes are silently ignored.

### B. Movement Cooldown
In `dandy-gb/src/dandy_core.c:361-370`, the player movement timer is set to `TICKS_PER_MOVE` (4) before attempting any movements, regardless of success:
```c
if (player_move_timer[p_idx] == 0) {
    player_move_timer[p_idx] = TICKS_PER_MOVE;
    // Slide mechanics: try main direction, then ±1 direction
    for (uint8_t di = 0; di < 3; ++di) {
        int8_t dd = (player_dir[p_idx] + search_order[di]) & 7;
        if (move_player(p_idx, dd)) {
            break;
        }
    }
}
```
If all three directions are blocked, the player remains stationary, but the cooldown timer is still active.

### C. Firing and Movement Ordering (Self-Collision)
In `dandy-gb/src/dandy_core.c:344-351` (arrow firing) and `354-371` (movement):
```c
// Fire Arrow (Level triggered)
if (buttons & BUTTON_FIRE) {
    if (arrow_dir[p_idx] == -1) {
        arrow_x[p_idx] = player_x[p_idx];
        arrow_y[p_idx] = player_y[p_idx];
        arrow_dir[p_idx] = player_dir[p_idx];
        hal_play_sound(SOUND_SHOOT);
    }
}
```
Firing sets the arrow coordinates to the player's *current* coordinates. The player then moves to the adjacent tile. When `move_arrows()` runs later in the tick, it steps the arrow from the player's old position into the player's new position, causing a collision with the player tile which destroys the arrow harmlessly.

### D. Generator LFSR Seed
In `dandy-gb/src/dandy_core.c:615-624`, the random seed is defined as a local static variable:
```c
} else if (tile >= TILE_GENERATOR1 && tile <= TILE_GENERATOR3) {
    static uint16_t rand_seed = 0xACE1;
    uint8_t lsb = rand_seed & 1;
    rand_seed >>= 1;
    if (lsb) {
        rand_seed ^= 0xB400u;
    }
```
Because the Python environment isolator (`dandy_env.py`) creates a fresh copy of the shared library on disk for every test case, `rand_seed` is guaranteed to be reset to `0xACE1` on the first tick of every test, making generator spawning 100% deterministic.

### E. Player Health and Overflows
In `dandy-gb/src/dandy_core.h:51`:
```c
extern int16_t player_health[MAX_PLAYERS];
```
In `dandy-gb/src/dandy_core.c:409-412`:
```c
case TILE_FOOD:
    player_health[p_idx] += 100;
    hal_play_sound(SOUND_FOOD);
    break;
```
There is no positive health clamping. If health exceeds the maximum signed 16-bit integer ($32767$), it overflows to a negative value, triggering player death and game over.

---

## 2. Logic Chain

1. **Flood Fill Limit**: Since `flood_push` ignores pushes when `flood_stack_ptr >= 64`, a large or highly branching door network requiring more than 64 pushes will leave several door tiles intact after unlocking the initial door.
2. **Blocked Cooldown**: Since `player_move_timer` is set to 4 before the slide checks are run, any completely blocked movement still incurs a 4-tick cooldown during which no inputs can be processed.
3. **Arrow Self-Hit**: When a player inputs both `BUTTON_FIRE` and a cardinal direction:
   - Arrow coordinates are initialized to the player's current coordinate $(X, Y)$.
   - Player moves to $(X+1, Y)$.
   - `move_arrows()` steps the arrow to $(X+1, Y)$, where it hits the player tile and destroys itself.
   - Thus, firing and moving forward cardinally on the same tick is a self-blocking action.
4. **Generator Determinism**: Since `rand_seed` is static and reset per test, the LFSR update sequence starting at `0xACE1` yields a highly predictable spawn sequence:
   - Tick 1 (seed=0xE270): Spawns monster Up.
   - Tick 2 (seed=0x7138): Spawns monster Up.
   - Ticks 3, 4, 5: Fails spawn check (no monster spawned).
   - This sequence is fully testable and assertable in E2E tests.
5. **Health Overflow**: Since `player_health` is a signed 16-bit integer and food adds 100 HP unconditionally, setting health to $32700$ and collecting food overflows health to $-32736$. In the same tick, the engine checks player survival (`player_health > 0`), finds it false, triggers player death, and resets the game to Level 0.

---

## 3. Caveats

- **ROM Bank Switching**: The compilation stub stubs out `SWITCH_ROM` as a no-op since all code is compiled into the same headless shared library. The E2E tests assume this behavior.
- **Rotor Index Collisions**: Since monsters and generators share the 16-tick rotor sparse grid scan, putting too many entities on the map on the same rotor grid lines can cause performance/tick alignment complexities. The designed tests use sparse placements to avoid unintended rotor tick collisions.

---

## 4. Conclusion

A comprehensive suite of **44 Tier 2 (Boundary & Corner Cases)** and **8 Tier 3 (Cross-Feature Interactions)** tests has been successfully designed. These tests cover all 10 core features (F-01 to F-10) with special emphasis on the hard limits, overflows, and subtle ordering side-effects identified in the C engine.

All test specifications have been written to the report at `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_e2e_m3_1_gen2/analysis.md`.

---

## 5. Verification Method

To verify the test suite design and ensure it is ready for implementation:
1. Review `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_e2e_m3_1_gen2/analysis.md` to confirm the presence and structure of all 52 test specifications.
2. Verify that each test case specifies both **C Globals** and **Mock HAL** assertions (Double-Assert Rule).
3. Confirm that the implementation of these tests in `dandy-gb/tests/test_tier2_tier3.py` (when written by the implementer) passes successfully by running:
   ```bash
   cd dandy-gb
   make test
   ```
   or by running the specific test file with Python's unittest module.
