## 2026-06-20T22:20:33Z

You are Explorer 2 (Milestone 4) in the E2E Testing Track for Dandy Dungeon.
Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_m4_2
Your focus is: Complex Combat & Survival Scenarios.

Task:
1. Analyze the core engine code in dandy-gb/src/dandy_core.c, dandy-gb/src/levels.c, and dandy-gb/tests/dandy_env.py.
2. Read the existing E2E tests under dandy-gb/tests/ (test_tier1.py, test_tier2.py, test_tier3.py).
3. Design at least 2 detailed E2E test scenarios focusing on complex combat, generator spawning, and smart bomb mechanics:
   - Scenario A (Generator & Monster Swarm): Player is surrounded by active generators. Generators spawn monsters deterministically based on LFSR seed. Player must fire arrows in different directions to destroy monsters and generators, verifying correct degradation and space clearing.
   - Scenario B (Smart Bomb Room Clear): Player enters a crowded room (viewport) of monsters/generators, uses a smart bomb, and verifies all entities inside the 10x20 viewport are destroyed while entities outside remain unaffected.
4. Ensure the design complies with the Double-Assert Rule (globals + mock HAL logs) and handles deterministic generator spawning based on the LFSR seed.
5. Write your structured report in analysis.md in your working directory. Include the exact step-by-step action sequences, expected state, and assertion details. When done, send a handoff message to the parent.
