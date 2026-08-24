## 2026-06-20T22:18:59Z

You are a Level Analysis Programmer (archetype: teamwork_preview_worker).
Your task is to write a Python script that performs a rigorous statistical analysis of all 26 levels of Dandy Dungeon.

Please follow these steps:
1. Write a Python script at `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/analyze_levels_rigorous.py`.
2. The script must:
   a. Parse `dandy-js/levels.js` to extract all 26 levels. Use the encoding string `encoding = " *DudKF$i123mnop"` to map characters to numeric tile IDs (0-15).
   b. **Tile Frequency Analysis**: Count the frequency (occurrences and percentage) of each of the 16 tile types across all 26 levels combined.
   c. **Edge Wall Elision Analysis**:
      - Inspect the outer border of all 26 levels (row 0, row 29, column 0, and column 59).
      - Verify if the outer border is 100% composed of Wall tiles (ID 1, character '*'). If there are any non-wall tiles on the border, report their coordinates and level indices.
      - Calculate the exact storage savings in bytes and percentage of omitting these 176 border tiles per level (reconstructing them on-the-fly) when combined with 4-bit packing.
   d. **4-Bit Packing Evaluation**: Compute the baseline size of the level database if we simply pack 4-bit tile IDs two-per-byte (both with and without edge wall elision).
   e. **Spatial Repetition (Meta-tiles)**:
      - Scan all 26 levels for 2x2, 2x3, and 4x4 sub-grids (meta-tiles). Note: they can be overlapping or non-overlapping (please analyze non-overlapping grid alignment as it is more relevant for compression block dictionaries). Let's compute both or focus on non-overlapping grid-aligned blocks (i.e., splitting the 60x30 map into 30x15 blocks of 2x2, or 20x10 blocks of 3x3, etc. For 2x3, it would be 20x10 blocks of 2x3, or similar. Wait, for 2x3, width is 2, height is 3, so a 60x30 map divides into 30x10 non-overlapping blocks. For 4x4, since 60 is divisible by 4 and 30 is not (30/4 = 7.5), we can only align 4x4 blocks up to row 28, or if we elide the border walls, the inner map is 58x28. 58 is not divisible by 4, but 28 is. Please analyze how non-overlapping block alignment would work, and count the frequencies of the most common meta-tiles).
      - Enumerate the number of unique meta-tiles for 2x2, 2x3, and 4x4 sizes.
      - List the top 10 most common meta-tiles for each size and their percentage of the total blocks.
3. The script must write its raw outputs to `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/analysis_results.json` and a human-readable Markdown summary to `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/analysis_summary.md`.
4. Run the script and verify that it executes successfully, producing correct results.
5. In your handoff, include the absolute paths to the script and its outputs, along with a summary of the findings.

Use the `software-engineering` domain skill to guide your implementation:
`/google/src/files/head/depot/google3/research/omega/teamwork/playbooks/software_engineering/SKILL.md`

MANDATORY INTEGRITY WARNING: DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## 2026-06-20T22:20:17Z

You are a Compression Modeler (archetype: teamwork_preview_worker).
Your task is to write a Python simulation script to model and compare the compression performance of the candidate compression schemes on all 26 levels of Dandy Dungeon.

Please follow these steps:
1. Write a Python script at `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/model_compression_schemes.py`.
2. The script must load the 26 levels (using the parser from `dandy-gb/tools/analyze_levels_rigorous.py` or reading `dandy-js/levels.js`).
3. Modeled Schemes:
   - **Scheme A: 4-Bit Packing with Edge Wall Elision (Baseline)**:
     - Omit the 176 border walls. Pack the remaining 1624 tiles as 4-bit nibbles (812 bytes per level).
   - **Scheme B: Variable-Bit-Width (VBW) / Huffman Coding**:
     - Model a custom prefix code. For example, calculate the optimal Huffman code based on the global tile frequencies of the inner 1624 tiles.
     - Also model a simplified hand-crafted VBW code:
       - Space (ID 0): `0` (1 bit)
       - Wall (ID 1): `10` (2 bits)
       - Other 14 tiles: `11` followed by 4-bit tile ID (6 bits total).
     - Calculate the exact compressed size in bits/bytes for each level, including padding to byte boundaries at the end of each level.
   - **Scheme C: Meta-Tile 2x2 Dictionary with Escape Coding**:
     - Extract non-overlapping 2x2 blocks from the inner 58x28 map.
     - Model dictionaries of size $N = 64, 128, 256$ most frequent 2x2 blocks.
     - Compression scheme:
       - If a 2x2 block is in the dictionary, represent it as 1 byte (the dictionary index, e.g., 0 to $N-1$).
       - If not in the dictionary, represent it as an escape byte (e.g., 0xFF or $N$, depending on $N$) followed by 4 nibbles (2 bytes) containing the 4 raw tile IDs.
       - Calculate the total compressed size per level, plus the ROM overhead of the dictionary itself ($N \times 2$ bytes, since each 2x2 block of 4-bit tiles is 2 bytes).
   - **Scheme D: 2D Predictor / Copy-Neighbor Coding**:
     - For each tile in the inner 58x28 map (scanning row-by-row, left-to-right):
       - Check if it matches the tile directly above (y-1).
       - Check if it matches the tile to the left (x-1).
       - Otherwise, it is a new tile.
     - Model a prefix code for these operations:
       - Copy Above: `0` (1 bit)
       - Copy Left: `10` (2 bits)
       - Write New Tile: `11` followed by 4-bit tile ID (6 bits total).
       - Note: For the first row, "Copy Above" is invalid, so we only use Copy Left or New. For the first column of each row, "Copy Left" is invalid.
     - Compute the exact compressed size in bits/bytes per level.
   - **Scheme E: 1D Run-Length Encoding (4-Bit RLE)**:
     - Run-length encoding of 4-bit tile runs. For example:
       - A run of length $L$ of tile $T$:
         - If $L \le 2$, encode as $L$ raw tiles (each 4 bits).
         - If $L > 2$, encode as a special run marker (e.g., 4-bit value 0xF or similar) followed by length (4 bits) and tile ID (4 bits).
         - Or model the RLE scheme currently in `convert_levels.py` but operating on 4-bit nibbles.
4. The script must run the simulations, compile the results, and write a comprehensive Markdown comparative report to `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/modeling_results.md`.
5. The report must include a table comparing:
   - Scheme Name
   - Average Compressed Level Size (Bytes)
   - Total Database Size for 26 Levels (Bytes, including dictionary/tables)
   - Compression Ratio (relative to 1800-byte raw map and 900-byte packed map)
   - Estimated Decompressor C Code Size (in bytes, based on code complexity)
   - Estimated Z80 CPU Execution Overhead (Low/Medium/High, explaining bit-shifting/memory-read requirements)
   - Overall Rank / Recommendation.
6. Verify that the script executes correctly and produces accurate mathematical results.

Use the `software-engineering` domain skill:
`/google/src/files/head/depot/google3/research/omega/teamwork/playbooks/software_engineering/SKILL.md`

MANDATORY INTEGRITY WARNING: DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
