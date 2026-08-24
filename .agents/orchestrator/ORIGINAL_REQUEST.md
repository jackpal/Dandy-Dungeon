# Original User Request

## Initial Request — 2026-06-20T21:48:05Z

You are the Project Orchestrator (archetype: teamwork_preview_orchestrator) for the Dandy Dungeon custom 2D level compression project.

Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/orchestrator
The verbatim user request is recorded at: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/ORIGINAL_REQUEST.md

Your responsibilities:
1. Decompose this project into logical, sequential milestones.
2. Author your initial plan (plan.md), progress tracker (progress.md), and project context (context.md) inside your working directory.
3. Spawn and dispatch tasks to specialized subagents (e.g., explorers, implementers, reviewers) to execute each milestone.
4. Continuously monitor subagent progress, update plan.md and progress.md, and coordinate the team.
5. When all milestones are complete and fully verified, write a final handoff/completion report in your directory and report victory to the parent (Project Sentinel).

Please start by reading the ORIGINAL_REQUEST.md, creating your directory files (plan.md, progress.md, context.md), and formulating your execution plan. Notify the parent once your initial plan is ready.

## Follow-up — 2026-06-20T22:11:34Z

The user has provided critical architectural directives and constraints that must guide our compression research and implementation in Milestone 2. You must immediately update the project plans, scope, and instruct your explorer/worker teams to incorporate these findings:

1. Deep Research into Traditional Fax Compression (MH, MR, MMR):
   - Do not rush to implement the meta-tile dictionary scheme without a thorough comparative analysis.
   - Specifically research and evaluate traditional Fax machine compression algorithms:
     - MH (Modified Huffman): 1D run-length encoding of runs of pixels, using Huffman codes for run lengths.
     - MR (Modified READ) & MMR (Modified Modified READ): 2D run-length/delta schemes that encode the positions of color transitions (changes) relative to a "reference line" immediately above the current "coding line".
   - Evaluate how we can adapt these 2D line-to-line delta-tracking ideas (encoding horizontal changes relative to the previous row) for our 4-bit tile grid.

2. 4-Bit Tile Packing:
   - Dungeon map tiles only use IDs 0 to 15, which fit exactly within 4 bits.
   - Any compression scheme should operate on 4-bit nibbles rather than 8-bit bytes as the raw data unit. Packing two tiles per byte must be a baseline consideration.

3. Edge Wall Elision:
   - Every single level map (60x30) has a solid "wall" (tile 1) entirely surrounding the outer edges of the map (first row, last row, first column, last column).
   - We can completely omit storing these outer border tiles in the compressed ROM stream. The decompressor can automatically write wall tiles into the border coordinates of `dandy_map` on load, saving exactly 176 tiles (88 bytes raw) of storage per level before compression even begins!

4. Tile Frequency Analysis:
   - Perform a rigorous frequency analysis of tiles across all 26 levels.
   - Spaces (0) and walls (1) make up the vast majority of the map.
   - Design and evaluate variable-length coding (Huffman-like or variable-bit-width) where very common tiles (like space and wall) are encoded with very few bits (e.g., 1 or 2 bits), while rarer entities use longer bit sequences.

Please update your PROJECT.md, plan.md, and instruct your explorer teams to compile a comprehensive comparative report on these compression schemes, taking into account decompressor code size and CPU overhead on the 8-bit GameBoy.
