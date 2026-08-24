# Original User Request

## Initial Request — 2026-06-20T22:16:41Z

You are the Milestone 2 Sub-orchestrator (archetype: teamwork_preview_orchestrator) for the Dandy Dungeon custom 2D level compression project.

Your working directory is: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/sub_orch_m2
Your parent is: 6949b863-eafb-4fae-bca8-2c92c6ca9449 (the Project Orchestrator)
The global PROJECT.md is at: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/PROJECT.md

Your mission is to execute Milestone 2: Design 2D Compression.
1. Perform a rigorous analysis of the 26 levels from `dandy-js/levels.js`:
   a. **Tile Frequency Analysis**: Enumerate tile frequencies across all levels. Identify the most common tiles (e.g., spaces and walls) to evaluate variable-length coding.
   b. **Edge Wall Elision Analysis**: Quantify the storage savings of omitting the outer border walls (first/last rows and columns, saving 176 tiles per level) and reconstructing them on-the-fly.
   c. **4-Bit Tile Packing Evaluation**: Evaluate the baseline savings of packing 4-bit tile IDs (0-15) two-per-byte.
   d. **Spatial Repetition**: Measure occurrence rates of 2x2, 2x3, and 4x4 meta-tiles.
2. Conduct research and comparative analysis of candidate compression schemes:
   a. **Meta-Tile Dictionary + RLE**: Dictionary-based block indexing.
   b. **Modified Huffman (MH)**: 1D run-length encoding with Huffman codes for run lengths.
   c. **Modified READ (MR) & Modified Modified READ (MMR)**: 2D line-to-line delta-tracking schemes, encoding tile transition coordinates relative to the row directly above.
   d. **Variable-Bit-Width / Variable-Length Coding**: Encoding common tiles with 1-2 bits and rarer tiles with longer sequences.
3. Compile a **Comparative Compression Report** (saved in your workspace) evaluating:
   a. Compression ratio and total level database size.
   b. GBDK C decompressor code size.
   c. CPU execution overhead and complexity on the 8-bit Z80/GB CPU (e.g., bit-shifts, division, stack depth).
   d. Trade-offs and selection of the optimal scheme.
4. Design the selected optimal compression binary format and GBDK C decompressor algorithm.

Apply the Orchestrator Procedure:
- Assess the complexity. Decompose the milestone into sub-tasks (e.g. analysis script, comparative research, report compilation, format design) and spawn specialized subagents (explorers, workers, reviewers) to execute them.
- Author your own BRIEFING.md, SCOPE.md, progress.md, and plan.md in your working directory.
- Verify everything rigorously.
- When done, write handoff.md, publish the Comparative Compression Report, and send a completion message to the parent.

Please initialize your workspace and start immediately. Report back when you have initialized your plan.
