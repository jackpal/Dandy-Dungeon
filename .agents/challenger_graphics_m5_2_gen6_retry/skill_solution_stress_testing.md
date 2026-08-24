# Solution Stress Testing Playbook

Pre-submission verification methodology. The goal is to find bugs
**before** the judge does. This skill is for anyone verifying a
solution: the implementer, a critic, or a dedicated challenger.

## Testing Strategy Selection

Pick the right testing approach based on the problem type:

| Problem Type                    | Primary Test          | Secondary Test             |
| ------------------------------- | --------------------- | -------------------------- |
| Single correct answer           | Differential (oracle) | Edge case enumeration      |
| Multiple valid answers          | Validator-based       | Property checking          |
| Optimization (min/max)          | Bound verification    | Differential (if feasible) |
| Interactive                     | Protocol simulation   | Adversarial interactor     |
| Special judge (custom checker)  | Replicate checker     | Differential               |
| Constructive (output any valid) | Validator-based       | Edge case enumeration      |

## Differential Testing (Correctness Fuzzing)

The most powerful technique. Compare an optimized solution against a
slow-but-obviously-correct oracle on thousands of random inputs.

### Three-Component Pattern

Every differential test needs three components:

1. **Generator** — produces random valid inputs
2. **Oracle** — brute-force solver (correct by simplicity, not speed)
3. **Harness** — orchestrates: generate → run both → compare → report

### Generator Design

Generators are the hardest part. Bad generators miss bugs.

**Sizing strategy** — start small, scale up:

- Phase 1: exhaustive enumeration (all inputs with N ≤ 4–5)
- Phase 2: random small inputs (N = 5–20, 1000+ cases)
- Phase 3: random medium inputs (N = 100–500, 100+ cases)
- Phase 4: adversarial inputs targeting suspected weak spots

> These sizes are **guidelines, not absolutes** — calibrate to the problem.
> If the oracle is O(2^N), N=20 is already too large for Phase 2; use N=10–12.
> If the oracle is O(N³), N=200 may be fine for Phase 3. Always ensure each
> phase completes in reasonable time (seconds, not hours).

**Input distribution matters**:

- Uniform random often misses bugs. Bias toward extremes:
  - Values at 0, 1, -1, MAX, MIN, boundaries of constraint ranges
  - Degenerate structures: linear chains, stars, complete graphs, all-same arrays
  - Near-boundary: N exactly at constraint limit minus 1
- For graph problems: generate both sparse (M ≈ N) and dense (M ≈ N²) graphs
- For geometry: collinear points, coincident points, degenerate triangles
- For string problems: all-same characters, palindromes, alternating patterns

**Parameterize constraints**: the generator should accept N_max as an argument
so you can quickly sweep different sizes.

### Oracle Design

The oracle must be **obviously correct** — simplicity over speed.

- Use the naive O(N!) / O(2^N) / O(N³) algorithm
- Avoid optimizations — they introduce bugs that defeat the purpose
- If the problem has multiple valid answers, the oracle must either:
  - Produce a canonical answer (sorted, lexicographically smallest), OR
  - Be paired with a validator instead of direct output comparison
- For floating-point answers: compare with tolerance (typically 1e-9)

### Harness Execution

The harness loop should:

```
for i in 1..NUM_ITERATIONS:
    input = generator(seed=i, n_max=N_MAX)
    expected = oracle(input)
    actual = solution(input)
    if expected != actual:
        save input, expected, actual to failing_case file
        report mismatch and STOP
report "passed NUM_ITERATIONS cases"
```

**Minimum iteration counts** (adjust based on runtime per case):

- Exhaustive (N ≤ 5): enumerate ALL inputs (often only hundreds)
- Random small (N ≤ 20): ≥ 1000 iterations
- Random medium (N ≤ 200): ≥ 100 iterations

These are starting points. If each case takes 1s, 1000 iterations = 15min;
reduce N or iteration count to keep total fuzz time under a few minutes.

**Critical rule**: always save the failing input to a file. Random
generators with seeds may not reproduce if code changes.

### When Differential Testing Is Not Feasible

Some problems resist oracle construction:

- Optimization problems where the oracle is as hard as the solution
- Problems with extremely large output (e.g., construct a graph)
- Interactive problems

Fallback: **property-based testing** — verify properties of the output:

- Does the output satisfy all constraints?
- Is the claimed cost/value actually achievable?
- Does the output parse correctly?

## Performance Testing (TLE/MLE Prevention)

### Max-Constraint Input Generation

Generate inputs at the **maximum** allowed size. Focus on:

- **Worst-case structure**: inputs that maximize the number of operations
  - Sorted/reverse-sorted arrays for algorithms with quadratic worst-case
  - Complete graphs for graph algorithms
  - Adversarial inputs for hash maps (anti-hash tests)
  - Deep recursion chains for DFS-based solutions (stack overflow risk)
- **Multiple distinct max cases**: generate 3–5 different max-size inputs
  to test different structural worst-cases

### Time Measurement

- Measure wall-clock time, not CPU time (judges use wall-clock)
- Run each test 3+ times to account for variance
- **Target**: solution should run in ≤ 50% of the time limit
  - If TL = 2s, solution should finish in ≤ 1s on worst case
  - 50% margin accounts for judge machine speed variation
- If close to the limit: profile to find the bottleneck

### Memory Measurement

- Track peak memory (RSS), not just allocation
- Reserve margin: if ML = 256MB, target ≤ 200MB
- Common memory traps:
  - STL containers have overhead (vector: 24 bytes base, map node: ~64 bytes)
  - Recursive DFS on N=10⁶ can use 40MB+ of stack
  - String copies in loops

### Common TLE Causes (Language-Agnostic)

| Cause                   | Symptom                    | Fix                                         |
| ----------------------- | -------------------------- | ------------------------------------------- |
| Hidden quadratic        | TLE on large N             | Re-examine algorithm complexity             |
| Slow I/O                | TLE despite fast algorithm | Use fast I/O (see below)                    |
| Unnecessary copies      | TLE + high memory          | Pass by reference, avoid string concat      |
| Map instead of array    | 10x slowdown               | Use array/vector when keys are small ints   |
| Redundant computation   | TLE                        | Memoize or precompute                       |
| Cache-unfriendly access | 2–5x slowdown              | Iterate in row-major order, use flat arrays |

### Fast I/O by Language

- **C++**: `ios::sync_with_stdio(false); cin.tie(nullptr);` + `'\n'` not `endl`
- **Python**: `sys.stdin.readline()`, or read all at once with `sys.stdin.read().split()`
- **Java**: `BufferedReader` + `StreamTokenizer`, not `Scanner`
- **Rust**: `BufReader` + manual parsing
- **General**: for N > 10⁵, always use buffered I/O

## Edge Case Checklist

Manually construct and test these cases **before** running the fuzzer.
**Read the problem constraints carefully** — only test cases that are valid
under the problem's guarantees (e.g., if the problem guarantees a connected
graph, don't test disconnected; if N ≥ 2, don't test N=1).

- **Minimal**: smallest N allowed by constraints (often N=1, but check)
- **Maximum**: N at upper constraint bound
- **Degenerate**: all elements equal, sorted, reverse-sorted
- **Boundary values**: 0, -1, 1, INT_MAX, INT_MIN, MOD-1, MOD
- **Overflow triggers**: products of two large values, sums near 2⁶³
- **Empty structures**: empty string, graph with no edges (if allowed)
- **Disconnected**: graph with multiple components (only if not guaranteed connected)
- **Self-loops / multi-edges**: only if not explicitly excluded by problem
- **Special modular cases**: N divisible by block size, N = prime, N = power of 2
- **Constraint boundary interactions**: when multiple constraints interact
  (e.g., N=10⁵ with all values = 10⁹, or M = N-1 exactly)

## Debugging Wrong Answers

When the fuzzer finds a failing case:

1. **Minimize** — reduce the failing input to the smallest case that still fails
2. **Trace** — run the solution with print/debug output on the minimal case
3. **Compare** — step through both solution and oracle on the same input
4. **Categorize** the bug:
   - Off-by-one (most common)
   - Integer overflow
   - Wrong initial value (e.g., `INF` too small)
   - Unhandled edge case
   - Algorithm correctness error (rare but serious — go back to proof)
5. **Re-fuzz** after fixing — the fix may introduce new bugs

## Verification Checklist (Pre-Submission Gate)

- [ ] All sample test cases pass
- [ ] Manual edge cases pass (N=1, N=max, degenerate inputs)
- [ ] Differential fuzzing passed ≥ 1000 small random cases (N ≤ 20)
- [ ] Differential fuzzing passed ≥ 100 medium random cases (N ≤ 200)
- [ ] No integer overflow in intermediate computations (verified)
- [ ] Max-constraint inputs finish within 50% of time limit
- [ ] Memory usage within limit on max-constraint inputs
- [ ] Multi-test cleanup verified (global state reset between cases)
- [ ] Compilation flags match judge environment
- [ ] Solution file is self-contained (no external dependencies)
