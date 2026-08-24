# Handoff Report — Level Exploration (M2.1)

## 1. Observation

We directly observed and analyzed the following files in the repository:
1. **`dandy-js/levels.js`**:
   - Contains a text-encoded representation of the game's levels as an array of 26 levels.
   - Quote: `const encoding = " *DudKF$i123mnop";` (line 783).
   - Dimensions: 30 rows of 60 characters each per level.
2. **`dandy-js/dandy.js`**:
   - Quote: `this.map[x + y * levelWidth] = encoding.indexOf(line.charAt(x));` (line 134).
   - Confirms that the index of each character in the 16-character `encoding` string maps to the numeric tile ID (0 to 15).
3. **`dandy-c++/Dandy.cpp`**:
   - Quote:
     ```cpp
     Cell[y*Width+x] = (BYTE) (inb & 0xf);
     Cell[y*Width+x+1] = (BYTE) ((inb >> 4) & 0xf);
     ```
     (lines 214-215).
   - Confirms the binary format: 900-byte files representing 60x30 levels, packed as two 4-bit nibbles per byte, unpacked **low-nibble first**.
4. **`dandy-py/src/map.py`**:
   - Quote:
     ```python
     self.data[i * 2] = b & 15
     self.data[i * 2 + 1] = (b >> 4) & 15
     ```
     (lines 82-83).
   - Confirms that Python uses the exact same low-nibble-first unpacking scheme.
5. **Cross-Implementation Level Files**:
   - In `dandy-py/Media/levels/`, files are named `LEVEL.A` through `LEVEL.Z` (size: 900 bytes).
   - In `dandy-c++/levels/`, files are named `level.a` through `level.z` (size: 900 bytes).
   - Comparing `dandy-py/Media/levels/LEVEL.A` and `dandy-c++/levels/level.a` showed a few byte differences:
     - Byte 30: Python is `0xa1` (`*2`); C++ is `0x01` (`* `).
     - Byte 60: Python is `0xa1` (`*2`); C++ is `0x01` (`* `).
     - Byte 388: Python is `0x22` (two doors); C++ is `0x02` (one door, one space).

---

## 2. Logic Chain

1. **Level Dimensions & Quantity**:
   - The array `levels` in `dandy-js/levels.js` contains 26 elements. Since each element contains exactly 30 strings of length 60, there are exactly 26 levels, each of dimension $60 \times 30$ (1,800 tiles).
2. **Tile Dictionary Mapping**:
   - The 16 characters in `encoding` correspond to indices 0 to 15. The `dandy.js` and `Dandy.cpp` code maps these indices to constants (e.g., `kSpace = 0`, `kWall = 1`, `kDoor = 2`, etc.).
   - This mapping covers the full range of static map tiles (0-15).
3. **Binary Packing Scheme**:
   - Since there are 16 static tile types, each tile requires exactly 4 bits (1 nibble).
   - A level of 1,800 tiles can therefore be packed into $\frac{1800 \times 4}{8} = 900$ bytes.
   - The loading routines in `Dandy.cpp` and `map.py` confirm that the low nibble (`b & 0x0F`) represents the first/left tile, and the high nibble (`b >> 4`) represents the second/right tile.
4. **Two Major Level Families**:
   - Running a byte-for-byte comparison of the unpacked Python levels against `levels.js` confirmed that they match **100% exactly** across all 26 levels.
   - However, comparing the C++ level files with the Python level files showed a small number of byte differences (e.g., 10 differing bytes in Level A).
   - Since the C# (`dandy-csharp`, `dandy-csharp12`, `dandy-csharp20`), XNA (`dandy-360`), and Clojure (`dandy-clojure`) binary files are byte-for-byte identical to the C++ files, the codebase has two level families:
     - **JS/Python family**: Matches `levels.js` exactly.
     - **C++/C#/360/Clojure family**: Contains gameplay-tweaking tile modifications (e.g. removing some monsters or doors).

---

## 3. Caveats

- **No Caveats**: The level dimensions, storage structures, tile dictionary, binary packing schemes, and level families have been fully analyzed and verified.

---

## 4. Conclusion

- **Format**: Levels are $60 \times 30$ grids of 4-bit tile indices (0-15).
- **Quantity**: 26 levels (Levels A to Z).
- **Unpacking**: Unpacked **low-nibble first** (low nibble is left tile, high nibble is right tile).
- **Tile Dictionary**: Maps indices 0-15 to Space, Wall, Door, Up, Down, Key, Food, Money, Bomb, Monsters (1-3), Heart, and Generators (1-3).
- **Level Families**: The repository contains two level families:
  - **JS/Python family**: Matches `levels.js` exactly.
  - **C++/C#/360/Clojure family**: Identical to each other but with minor gameplay adjustments compared to JS/Python.

---

## 5. Verification Method

To independently verify that the Python levels match `levels.js` exactly:
1. Run the following Python command from the repository root:
   ```bash
   python3 -c "
   import os, re
   with open('dandy-js/levels.js', 'r') as f:
       content = f.read()
   js_rows = [s for s in re.findall(r'\"([^\"]*)\"', content) if len(s) == 60]
   js_levels = [js_rows[i:i+30] for i in range(0, len(js_rows), 30)]
   encoding = ' *DudKF\$i123mnop'
   for idx in range(26):
       with open(f'dandy-py/Media/levels/LEVEL.{chr(65 + idx)}', 'rb') as f:
           py_data = f.read()
       py_unpacked = []
       for b in py_data:
           py_unpacked.extend([b & 15, b >> 4])
       js_tiles = [encoding.index(c) for row in js_levels[idx] for c in row]
       assert py_unpacked == js_tiles, f'Level {chr(65 + idx)} does not match!'
   print('Verification successful: All 26 Python levels match levels.js exactly!')
   "
   ```

To verify the differences between C++ and Python levels for Level A:
1. Run this Python command:
   ```bash
   python3 -c "
   with open('dandy-py/Media/levels/LEVEL.A', 'rb') as f1, open('dandy-c++/levels/level.a', 'rb') as f2:
       py_data, cpp_data = f1.read(), f2.read()
   diffs = [i for i in range(900) if py_data[i] != cpp_data[i]]
   print(f'Level A differs at {len(diffs)} bytes')
   for idx in diffs:
       print(f'Byte {idx:3d}: py={py_data[idx]:02x}, cpp={cpp_data[idx]:02x}')
   "
   ```
