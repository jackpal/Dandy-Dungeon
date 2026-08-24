# Handoff Report

This report provides the self-contained forensic findings, logical reasoning, and independent verification methods for the final audit of the Milestone 3 deliverables.

## 1. Observation

- **C Engine Fix**:
  - In `dandy-gb/src/dandy_core.c` line 100:
    ```c
    static int16_t flood_stack_ptr = 0;
    ```
  - In `dandy-gb/src/dandy_core.c` lines 102-108:
    ```c
    static void flood_push(uint8_t x, uint8_t y) {
        if (flood_stack_ptr < FLOOD_STACK_SIZE) {
            flood_stack_x[flood_stack_ptr] = x;
            flood_stack_y[flood_stack_ptr] = y;
            flood_stack_ptr++;
        }
    }
    ```
- **Mock HAL Sprite OOB Check**:
  - In `dandy-gb/tests/mock_hal.c` lines 57-67:
    ```c
    void hal_set_sprite(uint8_t sprite_idx, uint8_t x, uint8_t y, uint8_t tile_id, uint8_t flags) {
        if (sprite_idx < 40) {
            mock_sprites[sprite_idx].x = x;
            mock_sprites[sprite_idx].y = y;
            mock_sprites[sprite_idx].tile_id = tile_id;
            mock_sprites[sprite_idx].flags = flags;
            mock_sprites[sprite_idx].active = true;
        } else {
            mock_sprite_oob_error = true;
        }
    }
    ```
  - In `dandy-gb/tests/mock_hal.c` lines 151-153:
    ```c
    bool mock_get_sprite_oob_error(void) {
        return mock_sprite_oob_error;
    }
    ```
  - In `dandy-gb/tests/dandy_env.py` lines 445-446:
    ```python
        def get_sprite_oob_error(self):
            return self._lib.mock_get_sprite_oob_error()
    ```
- **Double-Assert Conformance**:
  - Scanning the test suite (`tests/test_tier1.py`, `tests/test_tier2.py`, `tests/test_tier3.py`) revealed 10 core E2E tests out of 103 that only assert one layer (either C engine globals or Mock HAL state) instead of both.
  - Examples:
    - `test_f09_camera_centering` in `tests/test_tier1.py` lines 736-744 only asserts Mock HAL camera state:
      ```python
      cam_x, cam_y = self.env.get_camera()
      self.assertEqual(cam_x, 15)
      self.assertEqual(cam_y, 10)
      ```
    - `test_f10_game_over_clears_inventories_multiplayer` in `tests/test_tier1.py` lines 1160-1185 only asserts C globals (level, player health, score) and does not assert HAL state.
- **Cheating/Hardcoding**:
  - No imports of `unittest.mock`, `mock`, `MagicMock`, or `patch` were found in any of the test files.
  - No `try-except` blocks exist in any core E2E tests (`test_tier1.py`, `test_tier2.py`, `test_tier3.py`).
- **Test Execution**:
  - Running `make test` produced a test suite failure:
    ```
    Ran 112 tests in 4.159s
    FAILED (failures=3)
    make: *** [Makefile:115: test] Error 1
    ```
  - The 3 failures are:
    1. `TestInfraStress.test_robustness_out_of_bounds_level_crash` (exit code 0 instead of expected crash `< 0`).
    2. `TestInfraStress.test_robustness_out_of_bounds_player_y_corruption` (memory at 2314 remained 99, no corruption detected).
    3. `TestTier1.test_f10_next_level_clamps_at_max` (expected level 4, got 5).

## 2. Logic Chain

1. **Check 1: Engine Memory Safety (PASS)**
   - Observation: `flood_stack_ptr` is changed to `int16_t` (signed 16-bit) and is bounds-checked against `FLOOD_STACK_SIZE` (64).
   - Reasoning: A signed 16-bit integer will not overflow or wrap to negative when incremented up to 64, making the bounds-checking robust. Pop operations only happen when `flood_stack_ptr > 0`, preventing underflow. Thus, memory safety is guaranteed.

2. **Check 2: Mock HAL Sprite OOB Check (PASS)**
   - Observation: `hal_set_sprite` in `mock_hal.c` strictly checks if the sprite index is `< 40` (the physical limit of the GameBoy hardware). If it exceeds 40, it sets a global boolean flag `mock_sprite_oob_error` instead of performing an out-of-bounds array write. This flag is bound and exposed to Python in `dandy_env.py` as `get_sprite_oob_error()`.
   - Reasoning: This ensures that any out-of-bounds sprite registration is caught safely, preventing memory corruption and exposing an error state to the test runner.

3. **Check 3: Double-Assert Conformance (FAIL)**
   - Observation: 10 core E2E tests only assert either C-side variables or Mock HAL side-effects, but not both.
   - Reasoning: The Double-Assert Rule requires validating that the C internal state matches the hardware emulator's state. Since these 10 tests omit assertions on one of the layers, they fail to conform to this rule.

4. **Check 4: No Cheating / Hardcoding (PASS)**
   - Observation: No Python mock frameworks or try-except blocks are used in Tiers 1-3, and the C mock HAL maintains a genuine state log of all operations.
   - Reasoning: The tests are authentic, stateful, and run directly against the compiled C engine. They do not fake passing status.

5. **Check 5: Compile and Execute (FAIL)**
   - Observation: Running `make test` fails with 3 failures.
   - Reasoning:
     - `test_f10_next_level_clamps_at_max` fails because `convert_levels.py` compiled 6 levels, whereas the test case was written assuming 5 levels (clamping at level 4).
     - The two out-of-bounds stress tests fail because they assert undefined C behavior (a crash or a specific memory corruption address), which is compiler-dependent and did not happen under this GCC layout.
   - Conclusion: Because tests fail to pass, the work product cannot be certified as clean.

## 3. Caveats

- We assumed that the 9 infrastructure/stress tests are exempt from the Double-Assert Rule, since they test the ctypes harness/isolation rather than game E2E behavior. Even if they were subject to it, the 10 core E2E tests are definitive violations.
- We did not modify any code, as we are strictly in an audit-only role.

## 4. Conclusion

The final verdict is **INTEGRITY VIOLATION** (due to Double-Assert Rule non-conformance and test execution failures).
- The C engine memory safety fix and mock HAL OOB checks are implemented perfectly.
- There is no cheating or fabrication.
- However, 10 core tests violate the Double-Assert Rule, and the test suite has 3 failures.
- The work product must be rejected until these issues are addressed.

## 5. Verification Method

To independently verify this audit:
1. **Double-Assert Conformance**:
   Run the following Python AST analysis command from the `dandy-gb` directory to list the non-conforming tests:
   ```bash
   python3 -c "
   import ast, glob
   c_globals_indicators = {'dandy_map', 'current_level', 'monster_rotor', 'local_player_idx', 'is_dirty', 'get_player_x', 'get_player_y', 'get_player_health', 'get_player_score', 'get_player_bombs', 'get_player_keys', 'get_player_dir', 'get_player_move_timer', 'is_player_joined', 'get_player', 'get_arrow_x', 'get_arrow_y', 'get_arrow_dir', 'player_x', 'player_y', 'player_health', 'player_score', 'player_bombs', 'player_keys', 'get_tile', 'assert_outer_border_walls'}
   mock_hal_indicators = {'get_draws', 'mock_get_draws', 'get_draw_count', 'mock_get_draw_count', 'get_sprites', 'mock_get_sprites', 'mock_get_sprite', 'get_sprites_dict', 'get_sounds', 'mock_get_sounds', 'mock_get_sound_count', 'get_camera', 'mock_get_viewport_camera', 'get_hud_update_count', 'mock_get_hud_update_count', 'get_sprite_oob_error', 'mock_get_sprite_oob_error'}
   class TestAnalyzer(ast.NodeVisitor):
       def __init__(self):
           self.has_c_global = False
           self.has_mock_hal = False
       def visit_Attribute(self, node):
           if node.attr in c_globals_indicators: self.has_c_global = True
           elif node.attr in mock_hal_indicators: self.has_mock_hal = True
           self.generic_visit(node)
       def visit_Name(self, node):
           if node.id in c_globals_indicators: self.has_c_global = True
           elif node.id in mock_hal_indicators: self.has_mock_hal = True
           self.generic_visit(node)
   files = ['tests/test_tier1.py', 'tests/test_tier2.py', 'tests/test_tier3.py']
   for f in files:
       tree = ast.parse(open(f).read(), filename=f)
       for class_node in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
           for method_node in [m for m in class_node.body if isinstance(m, ast.FunctionDef) and m.name.startswith('test_')]:
               analyzer = TestAnalyzer()
               analyzer.visit(method_node)
               if not (analyzer.has_c_global and analyzer.has_mock_hal):
                   print(f'{f}:{class_node.name}.{method_node.name} violates Double-Assert Rule!')
   "
   ```
2. **Compile and Run**:
   Run the following commands in the `dandy-gb` directory and observe the 3 failures:
   ```bash
   make test_lib
   make test
   ```
