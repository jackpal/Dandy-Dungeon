## 2026-06-20T22:20:34Z
You are Explorer 3 (Milestone 4) in the E2E Testing Track for Dandy Dungeon.
Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_m4_3
Your focus is: Multiplayer & Camera Viewport Scenarios.

Task:
1. Analyze the core engine code in dandy-gb/src/dandy_core.c, dandy-gb/src/levels.c, and dandy-gb/tests/dandy_env.py.
2. Read the existing E2E tests under dandy-gb/tests/ (test_tier1.py, test_tier2.py, test_tier3.py).
3. Design at least 2 detailed E2E test scenarios focusing on multiplayer and viewport/camera mechanics:
   - Scenario A (Cooperative Play & Viewport): Two players join the game (dandy_join_player()). They move independently. Verify viewport camera behavior (centering on the local player, clamping to map boundaries).
   - Scenario B (Spectator Mode): Two players are in the game. Player 1 (local player) dies. Verify that Player 1 enters Spectator Mode and the camera dynamically updates to center on the remaining alive player (Player 2). If Player 2 also dies, verify game over.
4. Ensure the design complies with the Double-Assert Rule (globals + mock HAL logs).
5. Write your structured report in analysis.md in your working directory. Include the exact step-by-step action sequences, expected state, and assertion details. When done, send a handoff message to the parent.
