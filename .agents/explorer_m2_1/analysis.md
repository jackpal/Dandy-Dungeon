# Dandy Dungeon — Level Data Analysis Report

## Executive Summary
This report provides a comprehensive analysis of the level data storage, format, and tile dictionary for the Dandy Dungeon implementations in the repository. We identified two primary families of level representations: a text-based representation in `dandy-js/levels.js` and a 4-bit packed binary representation used across compiled and python implementations, with minor gameplay-related tile adjustments in the C++/C#/360/Clojure implementations.

---

## 1. Level Data Storage & Format in `dandy-js/levels.js`

In `dandy-js/levels.js`, the level data is stored as a JavaScript array named `levels` containing **26 levels** (indices 0 to 25, representing Levels A to Z).

- **Structure**: An array of arrays of strings: `levels = [ [ "row0", "row1", ... ], ... ]`.
- **Dimensions**:
  - **Width**: Exactly **60 characters** per row.
  - **Height**: Exactly **30 rows** per level.
  - **Total Tiles**: 1,800 tiles per level.
- **Encoding String**:
  ```javascript
  const encoding = " *DudKF$i123mnop";
  ```
  Each character in the level string corresponds to a specific tile index based on its 0-indexed position in the `encoding` string.

---

## 2. Tile Dictionary (0–15)

The following table maps the 16 characters in the `encoding` string to their numeric IDs, constants, and gameplay meanings (derived from `dandy-js/dandy.js` and `dandy-c++/Dandy.cpp`):

| ID (Hex) | Char | Constant (JS) | Constant (C++) | Gameplay Meaning |
|---|---|---|---|---|
| **0** (0x0) | `' '` | `kSpace` | `kSpace` | **Walkable Space**: Empty floor that entities can move through. |
| **1** (0x1) | `'*'` | `kWall` | `kWall` | **Solid Wall**: Impassable boundary. |
| **2** (0x2) | `'D'` | `kDoor` | `kLock` | **Locked Door**: Opens by spending 1 key. JS triggers flood-fill to open connected doors. |
| **3** (0x3) | `'u'` | `kUp` | `kUp` | **Up Staircase**: Level entry. Player starts 1 tile directly above it. |
| **4** (0x4) | `'d'` | `kDown` | `kDown` | **Down Staircase**: Level exit. Moving here transitions to the next level. |
| **5** (0x5) | `'K'` | `kKey` | `kKey` | **Key**: Collectable item to unlock doors. |
| **6** (0x6) | `'F'` | `kFood` | `kFood` | **Food**: Collectable item that restores health (+100 health in JS). |
| **7** (0x7) | `'$'` | `kMoney` | `kMoney` | **Money/Treasure**: Collectable item that increases player score. |
| **8** (0x8) | `'i'` | `kBomb` | `kBomb` | **Smart Bomb**: Collectable item to clear all visible monsters/generators. |
| **9** (0x9) | `'1'` | `kMonster1` | `kGhost` | **Basic Monster**: Slowly chases player and deals low damage. |
| **10** (0xa) | `'2'` | `kMonster2` | `kSmiley` | **Intermediate Monster**: Chases player and deals medium damage. |
| **11** (0xb) | `'3'` | `kMonster3` | `kBig` | **Advanced Monster**: Chases player and deals high damage. |
| **12** (0xc) | `'m'` | `kHeart` | `kHeart` | **Heart**: Spawn egg; turns into a level 3 monster (`kMonster3`) when shot. |
| **13** (0xd) | `'n'` | `kGenerator1` | `kGen1` | **Basic Generator**: Spawns level 1 monsters in adjacent spaces. |
| **14** (0xe) | `'o'` | `kGenerator2` | `kGen2` | **Intermediate Generator**: Spawns level 2 monsters in adjacent spaces. |
| **15** (0xf) | `'p'` | `kGenerator3` | `kGen3` | **Advanced Generator**: Spawns level 3 monsters in adjacent spaces. |

*Note: Dynamically spawned entities like arrows (`16–23`) and players (`24–27`) are not stored in the level map files.*

---

## 3. The 4-Bit Packed Binary Format (900-Byte Files)

Across many implementations, levels are stored as individual binary files (representing Levels A to Z). Since there are 16 static tile types, each tile requires only **4 bits (1 nibble)** of data. Two tiles are packed into each byte of the file, resulting in:
$$\text{File Size} = \frac{60 \times 30}{2} = 900 \text{ bytes}$$

### Packing / Unpacking Scheme
The bytes are unpacked **low-nibble first**:
- **Left/First Tile**: `byte & 0x0F` (bits 0–3)
- **Right/Second Tile**: `byte >> 4` (bits 4–7)

This packing is explicitly defined in `dandy-c++/Dandy.cpp` and `dandy-py/src/map.py`:
```cpp
Cell[y*Width+x] = (BYTE) (inb & 0xf);
Cell[y*Width+x+1] = (BYTE) ((inb >> 4) & 0xf);
```

---

## 4. The Two Major Level Families in the Repository

Our cross-implementation analysis revealed **two distinct families of level data**:

### A. The JS/Python Family
- **Files**: `dandy-js/levels.js`, `dandy-ts/levels.ts`, and individual binary files `dandy-py/Media/levels/LEVEL.A` through `LEVEL.Z`.
- **Match**: The binary files in the Python version match `dandy-js/levels.js` **100% byte-for-byte** when unpacked.
- **Implementations**: `dandy-js`, `dandy-ts`, `dandy-py`, `dandy-clojurescript`, and the GameBoy (`dandy-gb`) port.

### B. The C++/C#/360/Clojure Family
- **Files**: Individual binary files `level.a` through `level.z` (lowercase) under `levels/`, `Media/levels/`, or `resources/levels/`.
- **Match**: These binary files are identical to each other but contain **slight gameplay-related differences** compared to the JS/Python family.
- **Key Differences**: A small number of tiles (mostly monsters, generators, and doors) have been replaced with empty floor tiles (`0x00`) to tweak gameplay and difficulty. For example, in Level A:
  - Byte 30 (tiles 60, 61): JS/Py has `0xa1` (`*2`); C++ has `0x01` (`* `). The monster at the second position is removed.
  - Byte 60 (tiles 120, 121): JS/Py has `0xa1` (`*2`); C++ has `0x01` (`* `).
  - Byte 388: JS/Py has `0x22` (two doors); C++ has `0x02` (one door, one space).
- **Implementations**: `dandy-c++`, `dandy-csharp`, `dandy-csharp12`, `dandy-csharp20`, `dandy-360`, and `dandy-clojure`.

---

## 5. Other Related Files & Scripts

- **`dandy-gb/tools/convert_levels.py`**:
  A Python utility that parses `dandy-js/levels.js` using regular expressions, converts characters to tile IDs, and compresses them using a custom Run-Length Encoding (RLE) scheme to fit into the GameBoy's ROM banks.
- **`dandy-py/src/map.py`**:
  Contains the python binary loading logic under `load(self, level)`, confirming the 900-byte low-nibble-first unpacking scheme.
- **`dandy-c++/Dandy.cpp`**:
  Contains the C++ binary loading logic and provides the definitions of tiles and player spawning rules.
