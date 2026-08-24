# Original Request

You are an Explorer agent (archetype: teamwork_preview_explorer).
Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/teamwork_preview_explorer_play_2
Your task is to design the Tier 4 E2E Play Scenarios (Milestone 4) for the Dandy Dungeon project.

Relevant Files:
- Global PROJECT.md: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/PROJECT.md
- Scope document: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/sub_orch_e2e/SCOPE.md
- Master Test Infra Reference: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/TEST_INFRA.md
- Test environment wrapper: dandy-gb/tests/dandy_env.py
- Existing tests: dandy-gb/tests/test_tier1.py, test_tier2.py, test_tier3.py

Your Objectives:
1. Review the existing test files and `TEST_INFRA.md` to understand the test runner API and the 10 core features.
2. Design at least **5 distinct, complex, multi-step real-world playthrough scenarios** representing typical game runs. You must cover the following scenarios:
   - **Scenario 1: Full Level 0 Playthrough**: Player starts at the entrance, navigates a maze, collects keys, unlocks doors, defeats a monster, collects food, and steps onto the stairs to advance to Level 1.
   - **Scenario 2: Cooperative Multiplayer Playthrough**: Two players join, navigate separate paths, share/split items (keys, score), and coordinate to reach the stairs.
   - **Scenario 3: Game Over Reset Playthrough**: Players take damage from monsters and generators until they die, and the test asserts that the game resets to Level 0, wiping all inventories and scores.
   - **Scenario 4: Combative Maze Scenario**: Player navigates a corridor packed with monsters and generators, utilizing strategic shooting (arrows) and smart bombs to clear the path.
   - **Scenario 5: Viewport Scrolling & Boundary Scenario**: Player moves from one corner of the 60x30 map to another, verifying that the camera viewport scrolls correctly, clamps at borders, and dynamic sprite rendering works.
3. For each designed scenario, provide:
   - The map layout (whether using a real level index from `levels.c` or a custom-defined layout string/array).
   - The exact sequence of player inputs (list of button masks) to inject tick-by-tick.
   - The step-by-step logic of what happens (e.g. at tick 12 player collects key, at tick 24 unlocks door).
   - The precise assertions to execute at key checkpoints and at the end of the run, following the **Double-Assert Rule** (globals + mock HAL side-effects like sounds, draws, sprites, camera scroll).
   - Validation checks for the **Edge Wall Elision** (asserting borders are always reconstructed as walls).

Constraints:
- You are read-only. DO NOT write or modify any source files or test files. Only write your analysis and designs to your handoff report (`analysis.md`) in your working directory.
- Ensure your designs are completely opaque-box and requirement-driven, supporting testing of game rules and mechanics.

Output:
Write a detailed report `analysis.md` in your working directory containing the complete step-by-step designs and input sequences for the 5 play scenarios, and a verification plan.

When done, write the report and send a message to your parent (conversation ID: c0a07f4a-93da-4e5b-b8e5-dd519af9093b).
