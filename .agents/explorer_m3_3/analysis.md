# Detailed Analysis & Integration Strategy: Compression Verification Pipeline

This report presents an analysis of `tools/verify_compression.py` and the Dandy Dungeon E2E/compilation pipeline. It outlines the strategy to integrate **Edge Wall Elision (EWE)** and **Scheme B2 (Variable-Bit-Width Prefix Coding)** into the automated verification pipeline for Milestone 3.

---

## 1. How `tools/verify_compression.py` Currently Operates

The current script acts as a gatekeeper to ensure that level compression preserves correctness and the compiled ROM satisfies hardware constraints. It performs four distinct stages:

### A. Level Parsing & Verification Setup (Lines 48–78, 170–195)
- **Extraction**: Reads `dandy-js/levels.js` and uses a regular expression to capture all double-quoted strings of length 60 (`re.findall(r'"([^"]*)"', content)`).
- **Grouping**: Groups every 30 rows of length 60 into a single level, forming a flat list of 1,800 elements.
- **Encoding**: Translates level characters (such as ` ` and `*`) into 4-bit integer Tile IDs using the static mapping:
  `ENCODING = " *DudKF$i123mnop"` (where Space is `0`, Wall `*` is `1`, Door `D` is `2`, etc.).
- **Fidelity Assertion**: Compresses and decompresses each level using Python-based implementations and asserts that `decompressed == raw_tiles`.

### B. ROM Compilation (Lines 199–220)
- Executes shell commands `make clean` and `make` using `subprocess.run` inside the `dandy-gb` directory.
- Checks the return code of both commands to verify that compilation succeeds without compiler or linker errors.

### C. ROM File Size Assertion (Lines 224–243)
- Checks the file size of the compiled ROM (`bin/dandy.gb`) via `os.path.getsize()`.
- Asserts that the size is **exactly 32,768 bytes** (32KB flat, matching the non-MBC single-bank ROM limit).

### D. Linker Map Segment Analysis (Lines 247–330)
- Parses the linker map file `bin/dandy.map` to calculate active memory footprints.
- Uses the regular expression:
  ```python
  area_pattern = re.compile(
      r'^\s*([_A-Za-z0-9]+)\s+([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+=\s+(\d+)\.?\s+bytes',
      re.MULTILINE
  )
  ```
  to match segments such as `_CODE`, `_DATA`, `_GSINIT`, etc., extracting their starting addresses and sizes.
- **Memory Classification**: Evaluates the starting address (incorporating 16-bit bank offset resolution) to classify segments:
  - **ROM**: `addr < 0x8000` OR (`offset < 0x8000` and `addr >= 0x10000`).
  - **VRAM**: `0x8000 <= addr < 0xA000` OR (`0x8000 <= offset < 0xA000` and `addr >= 0x10000`).
  - **WRAM**: `0xC000 <= addr < 0xE000` OR (`0xC000 <= offset < 0xE000` and `addr >= 0x10000`).
  - **HRAM**: `0xFF80 <= addr <= 0xFFFE` OR (`0xFF80 <= offset <= 0xFFFE` and `addr >= 0x10000`).
- **Footprint Budget Assertion**: Sums up all ROM segments and asserts that the total active ROM segment footprint is **under 28,672 bytes (28KB)**, leaving at least 4KB of padding to fit safely under the 32KB hardware boundary.

---

## 2. Integration of Edge Wall Elision & Scheme B2

In Milestone 3, the placeholder Run-Length Encoding (RLE) is replaced entirely by **Edge Wall Elision (EWE)** and **Scheme B2 Prefix Coding**. The Python round-trip pipeline in `verify_compression.py` must be updated to match.

### A. Core Algorithmic Components

#### 1. Edge Wall Elision (`elide_edge_walls`)
Only the inner $58 \times 28$ grid (1,624 tiles) is compressed. The outer boundaries (Row 0, Row 29, Column 0, Column 59) are omitted.
```python
def elide_edge_walls(tile_ids):
    """Extracts the inner 58x28 grid (1624 tiles) from a flat 60x30 map (1800 tiles)."""
    if len(tile_ids) != 1800:
        raise ValueError(f"Expected 1800 tiles, got {len(tile_ids)}")
    elided = []
    for y in range(1, 29):
        for x in range(1, 59):
            idx = y * 60 + x
            elided.append(tile_ids[idx])
    return elided
```

#### 2. Edge Wall Reconstruction (`reconstruct_edge_walls`)
Reconstructs the original $60 \times 30$ grid by pre-filling the entire 1,800-byte buffer with Wall tiles (ID 1) and writing the 1,624 decoded tiles to the inner grid.
```python
def reconstruct_edge_walls(elided_tiles):
    """Reconstructs the 60x30 map from 1624 inner tiles, pre-filling borders with Wall (ID 1)."""
    if len(elided_tiles) != 1624:
        raise ValueError(f"Expected 1624 elided tiles, got {len(elided_tiles)}")
    reconstructed = [1] * 1800  # Pre-fill entire map with Wall (ID 1)
    elided_idx = 0
    for y in range(1, 29):
        for x in range(1, 59):
            map_idx = y * 60 + x
            reconstructed[map_idx] = elided_tiles[elided_idx]
            elided_idx += 1
    return reconstructed
```

#### 3. Scheme B2 Prefix Compression (`scheme_b2_compress`)
Encodes the 1,624 tiles into a bitstream using variable-bit-width prefix codes and packs them MSB-first:
- Space (ID 0) $\to$ `0` (1 bit)
- Wall (ID 1) $\to$ `10` (2 bits)
- Others (IDs 2–15) $\to$ `11` + `xxxx` (6 bits), where `xxxx` is the 4-bit tile ID.
```python
def scheme_b2_compress(tile_ids):
    """Compresses tile IDs using Scheme B2 prefix coding and packs them MSB-first into bytes."""
    bit_str = ""
    for tile in tile_ids:
        if tile == 0:
            bit_str += "0"
        elif tile == 1:
            bit_str += "10"
        elif 2 <= tile <= 15:
            bit_str += "11" + f"{tile:04b}"
        else:
            raise ValueError(f"Invalid tile ID: {tile}")
            
    compressed_bytes = []
    for i in range(0, len(bit_str), 8):
        byte_chunk = bit_str[i:i+8]
        if len(byte_chunk) < 8:
            # Pad the final byte with 0s to byte boundary
            byte_chunk = byte_chunk + "0" * (8 - len(byte_chunk))
        compressed_bytes.append(int(byte_chunk, 2))
        
    return compressed_bytes
```

#### 4. Scheme B2 Prefix Decompression (`scheme_b2_decompress`)
Unpacks and decodes the packed bytes back into exactly 1,624 tile IDs.
```python
def scheme_b2_decompress(compressed_bytes):
    """Decompresses packed bytes back into 1624 tile IDs using Scheme B2."""
    bit_str = "".join(f"{b:08b}" for b in compressed_bytes)
    tile_ids = []
    i = 0
    while len(tile_ids) < 1624 and i < len(bit_str):
        if bit_str[i] == '0':
            tile_ids.append(0)
            i += 1
        elif bit_str[i:i+2] == '10':
            tile_ids.append(1)
            i += 2
        elif bit_str[i:i+2] == '11':
            if i + 6 > len(bit_str):
                raise ValueError("Truncated bitstream during tile decoding")
            tile_id = int(bit_str[i+2:i+6], 2)
            tile_ids.append(tile_id)
            i += 6
        else:
            raise ValueError(f"Malformed bitstream prefix at bit index {i}")
            
    if len(tile_ids) < 1624:
        raise ValueError(f"Incomplete bitstream: only decoded {len(tile_ids)}/1624 tiles")
        
    return tile_ids
```

### B. Integrating with the Pipeline
In `verify_compression.py`, the existing RLE functions will be replaced. The `compress_pipeline` and `decompress_pipeline` will be redefined to orchestrate EWE and Scheme B2:

```python
def compress_pipeline(raw_tiles):
    # 1. Edge Wall Elision (1800 -> 1624 tiles)
    elided_tiles = elide_edge_walls(raw_tiles)
    # 2. Scheme B2 Compression
    compressed_data = scheme_b2_compress(elided_tiles)
    return compressed_data

def decompress_pipeline(compressed_data):
    # 1. Scheme B2 Decompression (bits -> 1624 tiles)
    elided_tiles = scheme_b2_decompress(compressed_data)
    # 2. Edge Wall Reconstruction (1624 -> 1800 tiles)
    reconstructed_tiles = reconstruct_edge_walls(elided_tiles)
    return reconstructed_tiles
```

---

## 3. Compilation, Sizing, & E2E Testing Commands

To run and verify the entire pipeline, the following exact shell commands must be executed in the `dandy-gb` directory:

### A. ROM Compilation
```bash
make clean && make
```
- **Action**: Cleans previous object files and ROM, converts levels from `dandy-js/levels.js` to `src/levels.c`/`src/levels.h` using `tools/convert_levels.py`, compiles C sources (`main.c`, `dandy_core.c`, `gameboy_hal.c`, `levels.c`) using GBDK-2020 (`lcc`), and links them into a single ROM.

### B. ROM Size and Segment Verification
- **ROM Size Check**:
  ```bash
  stat -c %s bin/dandy.gb
  ```
  *(Must return exactly `32768` bytes).*
- **Active Segment Footprint Check**:
  Review `bin/dandy.map` or run the verification script to verify that the active ROM footprint is $\le 28,672$ bytes.

### C. E2E Offline Testing
To execute the host-side E2E tests:
```bash
make test_lib && make test
```
- **`make test_lib`**: Compiles `libdandy_test.so` using `gcc` on the host, linking `src/dandy_core.c`, `src/levels.c`, and `tests/mock_hal.c` with mock GBDK headers.
- **`make test`**: Runs the Python `unittest` framework to execute the 117+ E2E test cases across all Tiers.

---

## 4. Verification Pass/Fail Conditions

The automated verification script `tools/verify_compression.py` will yield a single binary **PASS** or **FAIL** result based on five conditions:

| # | Check Type | Pass Condition | Fail Condition |
|---|---|---|---|
| **1** | **Round-Trip Fidelity** | Every one of the 26 levels yields `decompressed == raw_tiles` under Python EWE/Scheme B2. | Any single tile discrepancy or truncated stream exception. |
| **2** | **ROM Compilation** | Both `make clean` and `make` commands return exit code `0`. | Non-zero exit code (syntax errors, linker errors, missing headers). |
| **3** | **ROM File Size** | File size of `bin/dandy.gb` is exactly `32,768` bytes. | File size $< 32,768$ or $> 32,768$ bytes. |
| **4** | **Active ROM Footprint** | Sum of all ROM segment sizes in `bin/dandy.map` is $\le 28,672$ bytes (28KB). | Active ROM segment footprint exceeds `28,672` bytes. |
| **5** | **E2E Test Execution** | `make test` command returns exit code `0` (all 117+ E2E tests pass). | Any E2E test case fails or crashes. |

---

## 5. E2E Test Pipeline Integration Design
To fully satisfy the Milestone 3 requirements, `tools/verify_compression.py` should be updated to execute the E2E tests automatically. This guarantees that any changes to the C decompressor in `src/dandy_core.c` are fully validated against the E2E suite before the build is declared green.

### Proposed Integration Code:
```python
def run_e2e_tests():
    print_header("5. Running E2E Test Suite (make test_lib && make test)")
    
    # 1. Compile Test Library
    print("Compiling test library...")
    lib_res = subprocess.run(["make", "test_lib"], cwd=dandy_gb_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if lib_res.returncode != 0:
        print_failure("make test_lib failed:")
        print(lib_res.stderr.decode())
        return False
        
    # 2. Run E2E Tests
    print("Running E2E tests...")
    test_res = subprocess.run(["make", "test"], cwd=dandy_gb_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(test_res.stdout.decode())
    if test_res.returncode != 0:
        print_failure("E2E tests failed:")
        print(test_res.stderr.decode())
        return False
        
    print_success("All E2E tests passed successfully.")
    return True
```
This function will be added to the main runner of `verify_compression.py` as the final stage of verification.
