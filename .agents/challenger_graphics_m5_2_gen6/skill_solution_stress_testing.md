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

### Oracle Design

The oracle must be **obviously correct** — simplicity over speed.

- Use the naive O(N!) / O(2^N) / O(N³) algorithm
- Avoid optimizations — they introduce bugs that defeat the purpose

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

## Performance Testing (TLE/MLE Prevention)

### Max-Constraint Input Generation

Generate inputs at the **maximum** allowed size. Focus on:

- **Worst-case structure**: inputs that maximize the number of operations
- **Multiple distinct max cases**: generate 3–5 different max-size inputs

### Time Measurement

- Measure wall-clock time, not CPU time (judges use wall-clock)
- Run each test 3+ times to account for variance
- **Target**: solution should run in ≤ 50% of the time limit

### Memory Measurement

- Track peak memory (RSS), not just allocation
- Reserve margin: if ML = 256MB, target ≤ 200MB

## Edge Case Checklist

Manually construct and test these cases **before** running the fuzzer.

- **Minimal**: smallest N allowed by constraints
- **Maximum**: N at upper constraint bound
- **Degenerate**: all elements equal, sorted, reverse-sorted
- **Boundary values**: 0, -1, 1, INT_MAX, INT_MIN
- **Overflow triggers**: products of two large values

## Debugging Wrong Answers

When the fuzzer finds a failing case:

1. **Minimize** — reduce the failing input to the smallest case that still fails
2. **Trace** — run the solution with print/debug output on the minimal case
3. **Compare** — step through both solution and oracle on the same input
4. **Categorize** the bug
5. **Re-fuzz** after fixing
