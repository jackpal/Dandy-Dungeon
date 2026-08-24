## 2026-06-21T00:43:27Z

You are a read-only exploration agent (`teamwork_preview_explorer`) tasked with designing the software architecture and test/validation plan for the mathematical downscaling tool.

Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_graphics_m2_3/
Your identity: Explorer 3 (Milestone 2 - Tool Architecture & Test Design)

Objectives:
1. Design the software architecture for the downscaling compiler tool (e.g., `dandy-gb/tools/downscale_sprites.py` or similar).
2. Specify the CLI interface:
   - Inputs (path to `strike_original.png` or individual tiles).
   - Outputs (path to generated 8x8 sprites or a visual grid).
   - Parameters (arguments to tune outline thickness, contrast thresholds, or algorithm selection).
3. Design a visual and programmatic validation plan:
   - How to visually inspect the downscaled tiles side-by-side with the original 16x16 sprites (integrating with or extending `verify_graphics.py`).
   - Programmatic assertions to verify aspect ratios, pixel counts, or symmetry constraints.
4. Design the test suite and adversarial test cases to verify the robustness of the downscaling script (e.g., handling corrupted files, missing CLI flags, extreme parameter values).
5. Write your detailed architectural design and test plan to `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_graphics_m2_3/analysis.md`.
6. Write your handoff report to `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_graphics_m2_3/handoff.md` following the 5-component handoff structure.

Remember: You are a read-only agent. Do NOT modify any source code or run any build commands. Only read files and write to your designated directory.
