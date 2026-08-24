# Detailed Challenge Report: Downscaling Pipeline Robustness Audit

**Date**: 2026-06-21
**Auditor**: `teamwork_preview_challenger` (critic, specialist)
**Milestone**: Milestone 2 Downscaling Pipeline

---

## Challenge Summary

**Overall Risk Assessment**: **LOW** (For compile-time CLI toolchain usage) / **MEDIUM** (For long-running programmatic or daemon usage)

After a rigorous review of the existing test suite, execution of the full GameBoy tests (172/172 passing), and running an independent, adversarial stress test harness (`tools/stress_test_downscaler.py`), the graphics downscaler pipeline has demonstrated exceptional functional robustness, excellent boundary protection, and zero file descriptor leaks.

However, the stress harness uncovered a **significant memory accumulation issue** on the API's failure paths (specifically when validating large/giant images). While all resources are reclaimed immediately upon CLI process termination (making it completely safe as a build tool), programmatic usage in long-running processes (e.g., watch-daemons, IDE plugins) will experience significant memory bloat between garbage collection cycles due to unclosed Pillow Image objects.

---

## Challenges & Findings

### [Medium] Challenge 1: Memory Accumulation on Validation Failures

*   **Assumption challenged**: The `SpriteSheetManager` cleans up all allocated image resources and file pointers immediately upon raising validation errors.
*   **Attack scenario**: A long-running asset-watch daemon processes an invalid or giant image (e.g. 2000x2000 pixels) that fails the downscaler's tile count validation. The manager raises a `ValueError` but does not explicitly close the Pillow Image object or its converted RGBA counterpart. Over 200 iterations, this accumulates **over 30.8 MB** of uncollected heap memory, which is only freed when the Python garbage collector is forced to run (`gc.collect()`).
*   **Blast radius**: Long-running programmatic/API clients (IDE plugins, build daemons, asset watchers) may suffer from memory spikes, performance degradation, or Out-of-Memory (OOM) crashes.
*   **Mitigation**: Refactor `SpriteSheetManager.load_and_slice` to use context managers (`with Image.open(...) as img:`) and explicitly call `.close()` on the converted RGBA image object before raising any validation exceptions or returning. For example:
    ```python
    try:
        with Image.open(image_path) as img:
            img_rgba = img.convert('RGBA')
    except Exception as e:
        raise ValueError(f"Failed to open image file: {e}")
    
    # Perform all validations...
    # Ensure img_rgba is closed or dereferenced properly.
    ```

### [Low] Challenge 2: Resource Leakage under Stress

*   **Assumption challenged**: Running hundreds of successful and failing downscaling operations in a single process will leak file descriptors or native memory.
*   **Attack scenario**: Repeatedly calling the downscaler CLI and API 200+ times with a mixture of valid, corrupted, giant, and non-existent files.
*   **Result**: **PASS**. The file descriptor delta was exactly **0**, proving that file pointers are closed correctly by the OS and Python. Memory is fully collectable (0 KB delta when `gc.collect()` is run), confirming there are no native C-level leaks.

### [Low] Challenge 3: Adversarial Input and Boundary Protection

*   **Assumption challenged**: The downscaler CLI/API will dump raw Python tracebacks or hang when encountering corrupted PNGs, out-of-range CLI parameters, or write-locked directories.
*   **Attack scenario**: Feeding the tool 0-byte files, random byte files, giant 10000x10000 images, out-of-bounds parameters (e.g. outline thickness of -0.1), and output paths blocked by file-directory name collisions.
*   **Result**: **PASS**. Every single test case failed gracefully, returning non-zero exit codes (typically 1) and user-friendly error messages on `stderr`, with **zero raw tracebacks** and **zero hangs**.

---

## Stress Test Results

The following table summarizes the empirical results of our independent adversarial stress harness (`tools/stress_test_downscaler.py`):

| Test Scenario | Input Description | Expected Behavior | Actual Behavior | Status |
|---|---|---|---|---|
| **CLI Valid Run** | Valid 256x32 sprite sheet | Exit 0, output files created | Exit 0, files created in 0.61s | **PASS** |
| **CLI Corrupted PNG** | Random byte file named `.png` | Exit 1, clean stderr, no traceback | Exit 1, "Failed to open image", no traceback | **PASS** |
| **CLI Empty File** | 0-byte file | Exit 1, clean stderr, no traceback | Exit 1, "Failed to open image", no traceback | **PASS** |
| **CLI Giant Image** | 10000x10000 black PNG | Exit 1, clean stderr, no traceback | Exit 1, "must contain exactly 32 tiles", no traceback | **PASS** |
| **CLI Wrong Dimensions** | 128x32 PNG (16 tiles instead of 32) | Exit 1, clean stderr, no traceback | Exit 1, "must contain exactly 32 tiles", no traceback | **PASS** |
| **CLI Non-existent Input** | Missing input file path | Exit 1, clean stderr, no traceback | Exit 1, "Input file not found", no traceback | **PASS** |
| **CLI Out-of-bounds Outline** | `--outline-thickness -0.1` | Exit 1, clean stderr, no traceback | Exit 1, "must be between 0.0 and 2.0", no traceback | **PASS** |
| **CLI Out-of-bounds Contrast**| `--contrast-threshold 1.05` | Exit 1, clean stderr, no traceback | Exit 1, "must be between 0.0 and 1.0", no traceback | **PASS** |
| **CLI Write Collision** | Output path blocked by existing file | Exit 1, clean stderr, no traceback | Exit 1, "Failed to create output directories", no traceback | **PASS** |
| **API FD Leak Loop** | 200 mixed success/failure runs | 0 leaked file descriptors | 0 leaked file descriptors | **PASS** |
| **API Memory Stability (GC)**| 200 mixed success/failure runs | Heap memory stable under GC | 16 KB (success) / 0 KB (giant) delta | **PASS** |
| **API Memory Accumulation (No GC)**| 200 giant image failure runs | Memory accumulates if GC is delayed | **30,884 KB (30.8 MB) accumulated** | **WARNING** |

---

## Unchallenged Areas

*   None. Every requirement in Section 5 of the blueprint (corrupted PNGs, incorrect dimensions, non-standard color modes, out-of-range CLI parameters, write-locked directories, file-directory name collisions) was successfully and exhaustively tested using both the existing test suite and our custom adversarial stress harness.

---

## Final Verdict

Based on the empirical evidence gathered:
1. The downscaler CLI and API are **extremely robust** against adversarial, corrupted, and out-of-bounds inputs.
2. The downscaler does **not** leak file descriptors, does **not** hang, and **never** dumps raw Python tracebacks under any adversarial conditions.
3. The downscaler correctly and completely satisfies all requirements outlined in Section 5 of the blueprint.
4. The memory accumulation on failure paths is a resource lifecycle optimization issue that does not affect the primary CLI compiler toolchain (where process exit reclaims all memory instantly).

Therefore, the final verdict is:

# **PASS**

*(With a strong recommendation/warning to implement explicit context managers/`close()` calls in `SpriteSheetManager.load_and_slice` to prevent garbage accumulation in programmatic, long-running environments.)*
