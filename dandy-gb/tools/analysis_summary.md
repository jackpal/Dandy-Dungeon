# Dandy Dungeon Level Analysis Report

This report presents a rigorous statistical analysis of all 26 levels of Dandy Dungeon. The analysis is designed to identify redundancy and spatial structures to guide the design of an optimal custom 2D compression algorithm for the GameBoy port.

## 1. Tile Frequency Analysis

Total tiles analyzed across all 26 levels: **46,800** (26 levels × 60 columns × 30 rows).

| ID | Char | Name | Count | Percentage |
|----|------|------|-------|------------|
|  0 | ` ` (Space) | Space (Empty) | 24,609 | 52.583% |
|  1 | `*` | Wall | 15,069 | 32.199% |
|  2 | `D` | Door | 501 | 1.071% |
|  3 | `u` | Stairs Up | 26 | 0.056% |
|  4 | `d` | Stairs Down | 28 | 0.060% |
|  5 | `K` | Key | 151 | 0.323% |
|  6 | `F` | Food | 301 | 0.643% |
|  7 | `$` | Money | 2,804 | 5.991% |
|  8 | `i` | Bomb | 92 | 0.197% |
|  9 | `1` | Monster 1 | 1,027 | 2.194% |
| 10 | `2` | Monster 2 | 925 | 1.976% |
| 11 | `3` | Monster 3 | 409 | 0.874% |
| 12 | `m` | Heart (Extra Life) | 484 | 1.034% |
| 13 | `n` | Monster 4 (Ghost/Bat) | 146 | 0.312% |
| 14 | `o` | Monster 5 (Spider) | 151 | 0.323% |
| 15 | `p` | Monster 6 (Wizard) | 77 | 0.165% |

## 2. Edge Wall Elision Analysis

Inspecting the outer borders (row 0, row 29, column 0, column 59) of all 26 levels (176 border tiles per level):

- **Verification Result**: ✅ **100% of outer border tiles are Wall tiles (`*`, ID 1) across all 26 levels.**

### Storage Savings with Edge Wall Elision & 4-Bit Packing

- **Uncompressed level size**: 60 × 30 = 1,800 tiles.
- **Elided level size** (omitting 176 border walls): 1,624 tiles.
- **4-Bit Packing Baseline** (without elision): **900 bytes** per level.
- **4-Bit Packing with Border Elision**: **812 bytes** per level.
- **Savings per level**: **88 bytes**.
- **Database size (26 levels)**:
  - Baseline (No Elision): **23,400 bytes** (22.85 KB)
  - With Border Elision: **21,112 bytes** (20.62 KB)
  - Total savings: **2,288 bytes** (2.23 KB, **9.778%** reduction)

## 3. Spatial Repetition (Meta-tiles) Analysis

Analyzing non-overlapping, grid-aligned block frequencies. This is highly relevant for dictionary-based compression or block-based encoding.

### 3.1. Full 60x30 Map

#### 2x2 Meta-tiles (Full 60x30 Map)

- **Total Blocks**: 11,700
- **Unique Blocks**: 667 (out of 65,536 possible)

| Rank | Count | Percentage | Visual Grid | Hex ID String |
|------|-------|------------|-------------|---------------|
| 1 | 2,510 | 21.45% | `  `<br>`  ` | `00/00` |
| 2 | 1,022 | 8.73% | `**`<br>`  ` | `11/00` |
| 3 | 934 | 7.98% | `  `<br>`**` | `00/11` |
| 4 | 502 | 4.29% | `* `<br>`* ` | `10/10` |
| 5 | 486 | 4.15% | ` *`<br>` *` | `01/01` |
| 6 | 474 | 4.05% | `**`<br>`**` | `11/11` |
| 7 | 373 | 3.19% | `* `<br>` *` | `10/01` |
| 8 | 293 | 2.50% | `* `<br>`  ` | `10/00` |
| 9 | 269 | 2.30% | `**`<br>` *` | `11/01` |
| 10 | 229 | 1.96% | `* `<br>`**` | `10/11` |

#### 2x3 Meta-tiles (Full 60x30 Map)

- **Total Blocks**: 7,800
- **Unique Blocks**: 1,347 (out of 16,777,216 possible)

| Rank | Count | Percentage | Visual Grid | Hex ID String |
|------|-------|------------|-------------|---------------|
| 1 | 1,086 | 13.92% | `  `<br>`  `<br>`  ` | `00/00/00` |
| 2 | 487 | 6.24% | `**`<br>`  `<br>`  ` | `11/00/00` |
| 3 | 424 | 5.44% | `  `<br>`  `<br>`**` | `00/00/11` |
| 4 | 221 | 2.83% | `* `<br>`* `<br>`* ` | `10/10/10` |
| 5 | 216 | 2.77% | ` *`<br>` *`<br>` *` | `01/01/01` |
| 6 | 180 | 2.31% | `  `<br>`**`<br>`  ` | `00/11/00` |
| 7 | 172 | 2.21% | `**`<br>`**`<br>`**` | `11/11/11` |
| 8 | 122 | 1.56% | `**`<br>`**`<br>`  ` | `11/11/00` |
| 9 | 109 | 1.40% | `  `<br>`**`<br>`**` | `00/11/11` |
| 10 | 101 | 1.29% | `**`<br>`  `<br>`**` | `11/00/11` |

#### 4x4 Meta-tiles (Full 60x30 Map)

- **Total Blocks**: 2,730
- **Unique Blocks**: 1,785 (out of 18,446,744,073,709,551,616 possible)

| Rank | Count | Percentage | Visual Grid | Hex ID String |
|------|-------|------------|-------------|---------------|
| 1 | 127 | 4.65% | `    `<br>`    `<br>`    `<br>`    ` | `0000/0000/0000/0000` |
| 2 | 72 | 2.64% | `****`<br>`    `<br>`    `<br>`    ` | `1111/0000/0000/0000` |
| 3 | 54 | 1.98% | `    `<br>`****`<br>`****`<br>`    ` | `0000/1111/1111/0000` |
| 4 | 46 | 1.69% | `*   `<br>`*   `<br>`*   `<br>`*   ` | `1000/1000/1000/1000` |
| 5 | 36 | 1.32% | `   *`<br>`   *`<br>`   *`<br>`   *` | `0001/0001/0001/0001` |
| 6 | 31 | 1.14% | `*   `<br>`1* *`<br>`*   `<br>`  $ ` | `1000/9101/1000/0070` |
| 7 | 27 | 0.99% | `*   `<br>`3* *`<br>`*   `<br>`  $ ` | `1000/b101/1000/0070` |
| 8 | 22 | 0.81% | `    `<br>`****`<br>`    `<br>`    ` | `0000/1111/0000/0000` |
| 9 | 22 | 0.81% | `$$$$`<br>`$$$$`<br>`$$$$`<br>`$$$$` | `7777/7777/7777/7777` |
| 10 | 18 | 0.66% | `*   `<br>`2* *`<br>`*   `<br>`  $ ` | `1000/a101/1000/0070` |

### 3.1. Inner 58x28 Map (Border Elided)

#### 2x2 Meta-tiles (Inner 58x28 Map (Border Elided))

- **Total Blocks**: 10,556
- **Unique Blocks**: 626 (out of 65,536 possible)

| Rank | Count | Percentage | Visual Grid | Hex ID String |
|------|-------|------------|-------------|---------------|
| 1 | 2,979 | 28.22% | `  `<br>`  ` | `00/00` |
| 2 | 509 | 4.82% | `  `<br>`**` | `00/11` |
| 3 | 457 | 4.33% | `**`<br>`**` | `11/11` |
| 4 | 447 | 4.24% | `**`<br>`  ` | `11/00` |
| 5 | 404 | 3.83% | `* `<br>` *` | `10/01` |
| 6 | 326 | 3.09% | ` *`<br>` *` | `01/01` |
| 7 | 310 | 2.94% | `* `<br>`* ` | `10/10` |
| 8 | 301 | 2.85% | `* `<br>`  ` | `10/00` |
| 9 | 288 | 2.73% | `  `<br>` *` | `00/01` |
| 10 | 263 | 2.49% | `$$`<br>`$$` | `77/77` |

#### 2x3 Meta-tiles (Inner 58x28 Map (Border Elided))

- **Total Blocks**: 6,786
- **Unique Blocks**: 1,203 (out of 16,777,216 possible)

| Rank | Count | Percentage | Visual Grid | Hex ID String |
|------|-------|------------|-------------|---------------|
| 1 | 1,303 | 19.20% | `  `<br>`  `<br>`  ` | `00/00/00` |
| 2 | 243 | 3.58% | `  `<br>`  `<br>`**` | `00/00/11` |
| 3 | 201 | 2.96% | `**`<br>`  `<br>`  ` | `11/00/00` |
| 4 | 190 | 2.80% | `  `<br>`**`<br>`  ` | `00/11/00` |
| 5 | 150 | 2.21% | `$$`<br>`$$`<br>`$$` | `77/77/77` |
| 6 | 117 | 1.72% | ` *`<br>` *`<br>` *` | `01/01/01` |
| 7 | 109 | 1.61% | `* `<br>`* `<br>`* ` | `10/10/10` |
| 8 | 99 | 1.46% | `  `<br>`  `<br>` *` | `00/00/01` |
| 9 | 99 | 1.46% | `* `<br>` *`<br>`* ` | `10/01/10` |
| 10 | 97 | 1.43% | `**`<br>`**`<br>`  ` | `11/11/00` |

#### 4x4 Meta-tiles (Inner 58x28 Map (Border Elided))

- **Total Blocks**: 2,548
- **Unique Blocks**: 1,604 (out of 18,446,744,073,709,551,616 possible)

| Rank | Count | Percentage | Visual Grid | Hex ID String |
|------|-------|------------|-------------|---------------|
| 1 | 191 | 7.50% | `    `<br>`    `<br>`    `<br>`    ` | `0000/0000/0000/0000` |
| 2 | 70 | 2.75% | `****`<br>`****`<br>`    `<br>`    ` | `1111/1111/0000/0000` |
| 3 | 46 | 1.80% | `* *3`<br>`   *`<br>` $  `<br>`   *` | `101b/0001/0700/0001` |
| 4 | 36 | 1.41% | `$$$$`<br>`$$$$`<br>`$$$$`<br>`$$$$` | `7777/7777/7777/7777` |
| 5 | 29 | 1.14% | `* *1`<br>`   *`<br>` $  `<br>`   *` | `1019/0001/0700/0001` |
| 6 | 22 | 0.86% | `    `<br>`    `<br>`****`<br>`    ` | `0000/0000/1111/0000` |
| 7 | 20 | 0.79% | `* * `<br>` * *`<br>`* * `<br>` * *` | `1010/0101/1010/0101` |
| 8 | 19 | 0.75% | `    `<br>`****`<br>`    `<br>`    ` | `0000/1111/0000/0000` |
| 9 | 18 | 0.71% | `* *2`<br>`   *`<br>` $  `<br>`   *` | `101a/0001/0700/0001` |
| 10 | 17 | 0.67% | `****`<br>`    `<br>`    `<br>`    ` | `1111/0000/0000/0000` |
