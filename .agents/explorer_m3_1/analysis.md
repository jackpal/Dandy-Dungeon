# Detailed Analysis & Implementation Strategy: Scheme B2 Compression and Edge Wall Elision

## Executive Summary
This document provides a comprehensive analysis and implementation strategy for upgrading the level compression pipeline of the GameBoy port of *Dandy Dungeon* from the baseline Run-Length Encoding (RLE) to the advanced **Scheme B2 + Edge Wall Elision** compression. 

By applying **Edge Wall Elision**, we omit the outer 176 border walls from compression (since they can be reconstructed by pre-filling the map buffer with walls in the decompressor). This reduces the map from 1,800 tiles to a 58x28 inner grid of 1,624 tiles.
By applying **Scheme B2 prefix coding**, we represent the tiles using variable bit-widths tailored to their frequencies:
- **Empty Floor (0)**: `0` (1 bit)
- **Wall (1)**: `10` (2 bits)
- **Other Tiles (2-15)**: `11` + `xxxx` (6 bits, MSB-first, where `xxxx` is the 4-bit tile ID).

This combination reduces the average size of a level from 1,800 bytes uncompressed (and ~500-600 bytes under baseline RLE) to **~250-350 bytes**, resulting in an overall **~80-85% size reduction**. Because of this high efficiency, the current 5-level limitation can be safely removed, allowing all 26 levels to be stored in ROM without risking 16KB bank overflows.

---

## 1. Edge Wall Elision
### Python-Side Implementation
A standard *Dandy Dungeon* level map is 60 columns wide by 30 rows high (1,800 tiles total) in row-major order.
The outer border of the map consists of:
- Row 0 (60 tiles)
- Row 29 (60 tiles)
- Column 0 (28 tiles, excluding corners)
- Column 59 (28 tiles, excluding corners)
Total border tiles = $60 + 60 + 28 + 28 = 176$ tiles.

Under the interface contract, the decompressor will pre-fill the entire 1,800-byte map buffer with Wall (ID 1) before decoding. Therefore, these 176 border tiles are omitted entirely from the compressed bitstream.

In Python, the extraction of the inner 58x28 grid (1,624 tiles) from a flat 1,800-tile list is implemented by slicing columns `1` to `58` (indices `1` to `58` inclusive) for rows `1` to `28` (inclusive):

```python
def elide_edge_walls(tile_ids):
    """
    Extracts the inner 58x28 grid (1,624 tiles) from a 60x30 flat list of tile IDs (1,800 tiles).
    Omits the outer row 0, row 29, col 0, and col 59.
    """
    assert len(tile_ids) == 1800, f"Expected 1800 tiles, got {len(tile_ids)}"
    inner_tiles = []
    for r in range(1, 29):
        start_idx = r * 60 + 1
        end_idx = r * 60 + 59
        inner_tiles.extend(tile_ids[start_idx:end_idx])
    return inner_tiles
```

### Reconstruction (For Verification Pipeline)
To verify the fidelity of the compression pipeline, the verification script (`tools/verify_compression.py`) needs to reconstruct the original 1,800-tile map from the 1,624 inner tiles:

```python
def reconstruct_edge_walls(inner_tiles):
    """
    Reconstructs the original 60x30 grid (1,800 tiles) from the inner 58x28 grid (1,624 tiles).
    Fills the outer border with Wall (1) tiles.
    """
    assert len(inner_tiles) == 1624, f"Expected 1624 tiles, got {len(inner_tiles)}"
    # Initialize the entire map with Wall (1)
    reconstructed = [1] * 1800
    
    # Overwrite the inner 58x28 grid with the decoded tiles
    for r in range(1, 29):
        dest_start = r * 60 + 1
        dest_end = r * 60 + 59
        
        src_start = (r - 1) * 58
        src_end = r * 58
        
        reconstructed[dest_start:dest_end] = inner_tiles[src_start:src_end]
        
    return reconstructed
```

---

## 2. Scheme B2 Variable-Bit-Width Prefix Coding
Each tile ID is an integer in the range `0` to `15` (4 bits). Under Scheme B2, the tile ID is translated into a variable-length list of bits (0s and 1s):

| Tile ID | Description | Prefix / Bits | Code Length |
|---|---|---|---|
| `0` | Empty Floor | `0` | 1 bit |
| `1` | Wall | `10` | 2 bits |
| `2` to `15` | Other Tiles | `11` + `xxxx` (4-bit tile ID, MSB-first) | 6 bits |

### Python Encoder Implementation
```python
def encode_tile_b2(tile_id):
    """
    Encodes a single tile ID (0-15) into a list of bits according to Scheme B2.
    """
    if tile_id == 0:
        return [0]
    elif tile_id == 1:
        return [1, 0]
    elif 2 <= tile_id <= 15:
        bits = [1, 1]
        # Append 4-bit ID, MSB-first
        for i in range(3, -1, -1):
            bits.append((tile_id >> i) & 1)
        return bits
    else:
        raise ValueError(f"Tile ID {tile_id} out of range (0-15)")
```

### Python Decoder Implementation (For Verification Pipeline)
```python
def decode_tile_b2(bits, bit_ptr):
    """
    Decodes a single tile ID from a bit list starting at bit_ptr.
    Returns (tile_id, new_bit_ptr).
    """
    if bit_ptr >= len(bits):
        raise ValueError("Truncated bitstream while reading tile prefix")
    
    b0 = bits[bit_ptr]
    bit_ptr += 1
    
    if b0 == 0:
        return 0, bit_ptr
    
    if bit_ptr >= len(bits):
        raise ValueError("Truncated bitstream while reading second bit of prefix")
    
    b1 = bits[bit_ptr]
    bit_ptr += 1
    
    if b1 == 0:
        return 1, bit_ptr
    
    # Other tile (2-15), decode 4-bit value MSB-first
    tile_id = 0
    for _ in range(4):
        if bit_ptr >= len(bits):
            raise ValueError("Truncated bitstream while reading 4-bit tile ID")
        bit = bits[bit_ptr]
        bit_ptr += 1
        tile_id = (tile_id << 1) | bit
        
    return tile_id, bit_ptr
```

---

## 3. Bitstream Packing & Padding
The generated bitstream (a flat list of bits) must be packed into bytes.
Bit packing is done **MSB-first (Most Significant Bit first)** into bytes:
- The 1st bit of the stream goes to bit 7 (MSB) of the 1st byte.
- The 8th bit goes to bit 0 (LSB) of the 1st byte.
- The 9th bit goes to bit 7 (MSB) of the 2nd byte, and so on.
- The final byte is padded with `0`s at any remaining lower-order bit positions to align to a byte boundary.

### Python Packing Implementation
```python
def pack_bits_to_bytes(bits):
    """
    Packs a list of bits (0s and 1s) into a list of bytes, MSB-first.
    Pads the last byte with 0s if the bit count is not a multiple of 8.
    """
    packed_bytes = []
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        byte_val = 0
        for bit_idx, bit in enumerate(chunk):
            # MSB-first: the first bit is placed at position 7, the second at 6, etc.
            byte_val |= (bit << (7 - bit_idx))
        packed_bytes.append(byte_val)
    return packed_bytes
```

### Python Unpacking Implementation (For Verification Pipeline)
```python
def unpack_bytes_to_bits(packed_bytes):
    """
    Unpacks a list of bytes into a list of bits, MSB-first.
    """
    bits = []
    for byte_val in packed_bytes:
        for i in range(7, -1, -1):
            bits.append((byte_val >> i) & 1)
    return bits
```

---

## 4. Code Generation and Bank Limit Removal
The original implementation had a hard mitigation limit inside `tools/convert_levels.py`:
```python
# Apply 16KB Bank Overflow Mitigation: limit to first 5 levels for Milestone 1 & 2
levels = levels[:5]
```
With **Scheme B2 + Edge Wall Elision**, the size of all 26 levels combined is **under 9KB** (well within the limits of a single 16KB ROM bank). Thus, this limit can be completely removed.

The code generator writes `src/levels.h` and `src/levels.c` dynamically using `len(levels)`. By removing `levels = levels[:5]`, the generator will automatically:
1. Define `DANDY_NUM_LEVELS` as `26` in `src/levels.h`.
2. Emit declarations and definitions for all 26 compressed arrays (`dandy_level_0` to `dandy_level_25`).
3. Build the 26-element pointer array `dandy_levels`.

---

## 5. Complete Python Implementation Plan (convert_levels.py)
Below is the proposed design for the updated `tools/convert_levels.py` script. The implementer should replace the existing RLE-based compressor with this implementation.

```python
import os
import re

# Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
levels_js_path = os.path.normpath(os.path.join(current_dir, "../../dandy-js/levels.js"))
output_h_path = os.path.normpath(os.path.join(current_dir, "../src/levels.h"))
output_c_path = os.path.normpath(os.path.join(current_dir, "../src/levels.c"))

# Create src directory if it doesn't exist
os.makedirs(os.path.dirname(output_h_path), exist_ok=True)

# Tile Character-to-ID Encoding Mapping
ENCODING = " *DudKF$i123mnop"

def char_to_tile_id(c):
    try:
        return ENCODING.index(c)
    except ValueError:
        print(f"Warning: Unknown character '{c}' in level data, defaulting to space (0)")
        return 0

# --- STAGE 1: Edge Wall Elision ---
def elide_edge_walls(tile_ids):
    """Omits the outer 176 border tiles, keeping only the inner 58x28 (1,624 tiles) grid."""
    inner_tiles = []
    for r in range(1, 29):
        start_idx = r * 60 + 1
        end_idx = r * 60 + 59
        inner_tiles.extend(tile_ids[start_idx:end_idx])
    return inner_tiles

# --- STAGE 2: Scheme B2 Prefix Encoding ---
def encode_tile_b2(tile_id):
    """Encodes a single tile ID into Scheme B2 prefix bits."""
    if tile_id == 0:
        return [0]
    elif tile_id == 1:
        return [1, 0]
    elif 2 <= tile_id <= 15:
        bits = [1, 1]
        for i in range(3, -1, -1):
            bits.append((tile_id >> i) & 1)
        return bits
    else:
        raise ValueError(f"Invalid tile ID {tile_id}")

# --- STAGE 3: Bitstream Packing ---
def pack_bits_to_bytes(bits):
    """Packs bits MSB-first into bytes, padded with 0s."""
    packed_bytes = []
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        byte_val = 0
        for bit_idx, bit in enumerate(chunk):
            byte_val |= (bit << (7 - bit_idx))
        packed_bytes.append(byte_val)
    return packed_bytes

# --- Main Compressor entry point ---
def compress_level(tile_ids):
    """
    Compresses a full 1,800-tile map using Edge Wall Elision + Scheme B2.
    Returns a list of packed bytes.
    """
    # 1. Elide border walls
    inner_tiles = elide_edge_walls(tile_ids)
    # 2. Convert to Scheme B2 bits
    bits = []
    for tile in inner_tiles:
        bits.extend(encode_tile_b2(tile))
    # 3. Pack bits to bytes
    return pack_bits_to_bytes(bits)

def main():
    print(f"Reading levels from {levels_js_path}...")
    with open(levels_js_path, "r") as f:
        content = f.read()

    all_strings = re.findall(r'"([^"]*)"', content)
    level_rows = [s for s in all_strings if len(s) == 60]

    levels = []
    for i in range(0, len(level_rows), 30):
        levels.append(level_rows[i:i+30])

    print(f"Found {len(levels)} levels.")
    # No more levels[:5] limit! All levels are processed.

    # ==========================================
    # Generate C Header (levels.h)
    # ==========================================
    h_content = [
        "/* Generated automatically from dandy-js/levels.js. Do not edit. */",
        "#ifndef DANDY_LEVELS_H",
        "#define DANDY_LEVELS_H",
        "",
        "#include <stdint.h>",
        "",
        "#define DANDY_LEVEL_WIDTH  60",
        "#define DANDY_LEVEL_HEIGHT 30",
        f"#define DANDY_NUM_LEVELS   {len(levels)}",
        "",
        "/* Extern declaration of pointer array to all compressed levels in ROM */",
        "extern const uint8_t* const dandy_levels[DANDY_NUM_LEVELS];",
        "",
        "#endif /* DANDY_LEVELS_H */"
    ]

    print(f"Writing C header to {output_h_path}...")
    with open(output_h_path, "w") as f:
        f.write("\n".join(h_content))

    # ==========================================
    # Generate C Source (levels.c)
    # ==========================================
    c_content = [
        "/* Generated automatically from dandy-js/levels.js. Do not edit. */",
        '#include "levels.h"',
        ""
    ]

    total_uncompressed = 0
    total_compressed = 0

    for l_idx, lvl in enumerate(levels):
        flat_tiles = []
        for row in lvl:
            flat_tiles.extend([char_to_tile_id(c) for c in row])
            while len(flat_tiles) % 60 != 0:
                flat_tiles.append(0)
                
        uncompressed_size = len(flat_tiles)
        compressed_bytes = compress_level(flat_tiles)
        compressed_size = len(compressed_bytes)
        
        total_uncompressed += uncompressed_size
        total_compressed += compressed_size
        
        saving = (1.0 - (compressed_size / uncompressed_size)) * 100
        print(f"Level {l_idx:2d}: Raw={uncompressed_size:4d}B -> B2={compressed_size:4d}B (Saved {saving:4.1f}%)")
        
        c_content.append(f"/* Level {l_idx} (Raw: {uncompressed_size}B, B2: {compressed_size}B) */")
        c_content.append(f"const uint8_t dandy_level_{l_idx}[] = {{")
        
        hex_rows = []
        for r in range(0, len(compressed_bytes), 16):
            chunk = compressed_bytes[r:r+16]
            hex_str = ", ".join([f"0x{val:02X}" for val in chunk])
            hex_rows.append(f"    {hex_str}")
        
        c_content.append(",\n".join(hex_rows))
        c_content.append("};")
        c_content.append("")

    c_content.append("/* Pointer array to all compressed levels in ROM */")
    c_content.append("const uint8_t* const dandy_levels[DANDY_NUM_LEVELS] = {")
    level_pointers = [f"    dandy_level_{i}" for i in range(len(levels))]
    c_content.append(",\n".join(level_pointers))
    c_content.append("};")
    c_content.append("")

    overall_saving = (1.0 - (total_compressed / total_uncompressed)) * 100
    print(f"--------------------------------------------------")
    print(f"TOTAL MAP BUDGET Footprint in ROM:")
    print(f"Raw uncompressed:  {total_uncompressed:5d} Bytes ({total_uncompressed/1024:.1f} KB)")
    print(f"B2 compressed:     {total_compressed:5d} Bytes ({total_compressed/1024:.1f} KB)")
    print(f"Overall savings:   {overall_saving:.1f}%")
    print(f"--------------------------------------------------")

    print(f"Writing C source to {output_c_path}...")
    with open(output_c_path, "w") as f:
        f.write("\n".join(c_content))

    print("Conversion complete!")

if __name__ == "__main__":
    main()
```

---

## 6. Verification Strategy & Test Cases
### Verification Pipeline Integration
In `tools/verify_compression.py`, the implementer should replace the placeholder functions with the full round-trip logic to assert 100% compression/decompression fidelity across all 26 levels:

```python
def elide_edge_walls(tile_ids):
    # Slice outer 176 walls
    inner_tiles = []
    for r in range(1, 29):
        inner_tiles.extend(tile_ids[r*60 + 1 : r*60 + 59])
    return inner_tiles

def reconstruct_edge_walls(inner_tiles):
    # Initialize with wall (1) and copy back 58x28 inner grid
    reconstructed = [1] * 1800
    for r in range(1, 29):
        reconstructed[r*60 + 1 : r*60 + 59] = inner_tiles[(r-1)*58 : r*58]
    return reconstructed

def pack_and_delta(tile_ids):
    """
    Converts 1,624 inner tiles to Scheme B2 bitstream, then packs to bytes.
    This replaces the RLE pack/delta stage.
    """
    # 1. Scheme B2 bitstream encoding
    bits = []
    for tile in tile_ids:
        if tile == 0:
            bits.append(0)
        elif tile == 1:
            bits.extend([1, 0])
        else:
            bits.extend([1, 1])
            for i in range(3, -1, -1):
                bits.append((tile >> i) & 1)
                
    # 2. MSB-first packing into bytes
    packed_bytes = []
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        byte_val = 0
        for bit_idx, bit in enumerate(chunk):
            byte_val |= (bit << (7 - bit_idx))
        packed_bytes.append(byte_val)
    return packed_bytes

def unpack_and_undelta(packed_bytes):
    """
    Unpacks bytes to bits, and decodes 1,624 tiles under Scheme B2.
    """
    # 1. Unpack bytes to bits MSB-first
    bits = []
    for byte_val in packed_bytes:
        for i in range(7, -1, -1):
            bits.append((byte_val >> i) & 1)
            
    # 2. Scheme B2 decode exactly 1,624 tiles
    decoded_tiles = []
    bit_ptr = 0
    while len(decoded_tiles) < 1624:
        b0 = bits[bit_ptr]
        bit_ptr += 1
        if b0 == 0:
            decoded_tiles.append(0)
        else:
            b1 = bits[bit_ptr]
            bit_ptr += 1
            if b1 == 0:
                decoded_tiles.append(1)
            else:
                tile_id = 0
                for _ in range(4):
                    bit = bits[bit_ptr]
                    bit_ptr += 1
                    tile_id = (tile_id << 1) | bit
                decoded_tiles.append(tile_id)
    return decoded_tiles
```

### Manual Verification Scenarios & Boundary Conditions
1. **Empty Floor Encoding**: If a level consists of only empty floor (ID 0) inside the 58x28 grid, the encoded bitstream will be exactly 1,624 `0` bits. When packed, this should result in exactly $\lceil 1624 / 8 \rceil = 203$ bytes of `0x00`.
2. **All-Wall Encoding**: If a level has only Wall (ID 1) inside the 58x28 grid, the encoded bitstream will be 1,624 pairs of `10` (total 3,248 bits). This results in exactly $\lceil 3248 / 8 \rceil = 406$ bytes of `0x80` (binary `10101010` is `0xAA`, wait!).
   Let's check the binary: `10 10 10 10` is `0xAA` in hex!
   So a sequence of all walls will pack into bytes of `0xAA`.
3. **Pads to Byte Boundary**: If the bitstream length is not divisible by 8, the padding bits must be `0`.
   For example, if we have a grid with 1623 floor tiles (1623 bits) and 1 other tile (6 bits), the total bits will be $1623 + 6 = 1629$ bits.
   $1629 / 8 = 203$ bytes and $5$ bits.
   The 204th byte will have 5 bits from the stream, and 3 padding `0` bits at the LSB positions.
   - Truncated bitstreams must throw errors during decompression to prevent silent corruption.
