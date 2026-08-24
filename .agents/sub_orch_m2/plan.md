# Milestone 2 Plan: Design 2D Compression

This plan outlines the steps for executing Milestone 2: Design 2D Compression.

## Phase 1: Level Analysis
- **Goal**: Rigorously analyze the 26 levels from `dandy-js/levels.js` to gather data for compression modeling.
- **Steps**:
  1. Locate and examine `dandy-js/levels.js` to understand its structure.
  2. Write a Python script to parse `dandy-js/levels.js` and compute:
     - Tile frequency distribution.
     - Savings from edge wall elision.
     - Savings from 4-bit tile packing.
     - Spatial repetition (2x2, 2x3, 4x4 meta-tiles).
  3. Execute the analysis script and capture the results.
- **Verification**: Cross-check total tile counts (should be 26 * 60 * 30 = 46,800 tiles) and ensure boundary conditions are correct.

## Phase 2: Compression Scheme Modeling & Research
- **Goal**: Research and model the compression ratio, decompressor code size, and CPU overhead for the candidate schemes.
- **Candidate Schemes**:
  1. Meta-Tile Dictionary + RLE.
  2. Modified Huffman (MH) (1D RLE + Huffman).
  3. Modified READ (MR) & Modified Modified READ (MMR) (2D line-to-line delta).
  4. Variable-Bit-Width / Variable-Length Coding.
- **Steps**:
  1. Research/simulate the compression performance of each scheme on the level dataset.
  2. Analyze the GBDK C decompressor complexity on the GameBoy's Z80-like 8-bit CPU (cycles, bit shifts, memory access, stack depth).
  3. Compare total ROM footprint (compressed data + decompressor code).
- **Verification**: Reviewer checks the modeling logic, ensures all candidate schemes are fully evaluated, and validates Z80 CPU overhead assertions.

## Phase 3: Comparative Compression Report Compilation
- **Goal**: Synthesize findings and select the optimal scheme.
- **Steps**:
  1. Compile a detailed Comparative Compression Report under `.agents/sub_orch_m2/`.
  2. Evaluate trade-offs (compression ratio, CPU cycles, RAM overhead, code size).
  3. Justify the selection of the optimal compression scheme.
- **Verification**: Peer review of the report.

## Phase 4: Format and Decompressor Algorithm Design
- **Goal**: Design the byte-level binary format and decompressor algorithm.
- **Steps**:
  1. Define the exact bit-level and byte-level layout of the compressed stream.
  2. Design the GBDK C decompressor algorithm (pseudo-code / C interface) that decodes the stream directly into the `dandy_map` RAM buffer.
- **Verification**: Reviewer checks the decompressor for buffer overflows, efficiency, and integration compatibility with `dandy_load_level`.
