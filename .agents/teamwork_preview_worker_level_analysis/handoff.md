# Handoff Report: Dandy Dungeon Compression Modeling & Analysis

## 1. Observation
- **Level Source File**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-js/levels.js`
- **Simulation Script**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/model_compression_schemes.py`
- **Comparative Report**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/modeling_results.md`
- **Raw JSON Results**: `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/modeling_results.json`
- **Verbatim Tool Output from Simulation Run**:
  ```
  Reading levels from /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-js/levels.js...
  Successfully parsed 26 levels.
  Global Huffman Codes:
    Tile  0: 1 (1 bits)
    Tile  1: 01 (2 bits)
    Tile  2: 001011 (6 bits)
    ...
    Tile 15: 0011110111 (10 bits)
  Successfully wrote raw results to /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/modeling_results.json
  Successfully wrote Markdown report to /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/modeling_results.md
  ```

## 2. Logic Chain
- **Step 1**: The statistical tile frequency analysis from Milestone 2.1 showed that Space (Empty, ID 0) at 52.583% and Wall (ID 1) at 32.199% account for **84.78%** of the map tiles in Dandy Dungeon.
- **Step 2**: Since these two tiles dominate the map, we designed Scheme B2 (Hand-crafted Variable-Bit-Width Coding) to assign extremely short prefix codes: Space gets 1 bit (`0`), Wall gets 2 bits (`10`), and all other 14 tiles get 6 bits (`11` + 4-bit ID).
- **Step 3**: The simulation script `model_compression_schemes.py` was developed to rigorously evaluate the mathematical compressed sizes of the candidate schemes across all 26 levels under the GameBoy port constraints (e.g., 32KB flat ROM, < 28KB active footprint).
- **Step 4**: The simulation results proved that:
  - **Scheme B2 (Hand-crafted VBW)** achieves a total database size of **11,050 bytes** (10.79 KB) for all 26 levels. This is only 956 bytes larger than the mathematically optimal Global Huffman (B1: 10,094 bytes) but requires **zero bytes of table/dictionary ROM overhead** and avoids Z80 bit-by-bit tree traversal delays.
  - **Scheme D (2D Predictor)** achieves 12,041 bytes, but its high decompressor complexity (coordinate tracking, 2D neighbor lookups) and CPU overhead make it sub-optimal for the GameBoy's Z80.
  - **Scheme C (2x2 Meta-tile Dictionary)** achieves 12,046 bytes at $N=256$, but incurs a 512-byte ROM table overhead and has high coordinate C logic complexity.
  - **Scheme E (4-bit RLE)** achieves 13,388 bytes, which is sub-optimal compared to VBW.
  - **Scheme A (4-bit Packing Baseline)** achieves 21,112 bytes, which is too large, leaving only ~6.9 KB for the entire game engine.
  - **Traditional 8-bit RLE (Scheme E3)** achieves 27,752 bytes, which completely exhausts the 28KB active ROM budget by itself, proving that a custom 2D/entropy scheme is mandatory.

## 3. Caveats
- The C decompressor sizes and CPU overheads are **estimates** based on the architectural complexity of the algorithms and Z80 instruction set behavior (e.g., absence of barrel shifter, expensive division/multiplication, pointer arithmetic vs lookup tables). These must be verified during C implementation in Milestone 3.
- All compression size models assume that levels are aligned to byte boundaries (meaning padding bits at the end of each level are counted). This is a safe and realistic assumption for GameBoy level loading.

## 4. Conclusion
- **Scheme B2: Hand-crafted Variable-Bit-Width (VBW) Coding** is the **unambiguous recommendation**.
- It compresses all 26 levels into **11,050 bytes** (10.79 KB), leaving a huge ROM headroom of over **17 KB** for the GameBoy engine, graphics, and sound driver, making the flat 32KB ROM target highly feasible and safe.
- It is highly optimized for the 8-bit Z80 because ~85% of tiles take the fast 1-bit or 2-bit decoding paths with zero memory lookup overhead for tree nodes.

## 5. Verification Method
1. **Execution Check**: Run the simulation script on the command line:
   ```bash
   python3 dandy-gb/tools/model_compression_schemes.py
   ```
   Verify that it exits successfully with `0` and prints out the parsed levels count and global Huffman codes.
2. **Output Verification**:
   - Inspect the comparative report at `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/modeling_results.md` to verify the table of results and detailed analysis.
   - Inspect the JSON results at `/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/dandy-gb/tools/modeling_results.json` to verify the raw calculated byte sizes for each level.
