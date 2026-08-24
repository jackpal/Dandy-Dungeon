---
name: test-coverage-audit
description: >-
  Adversarial test coverage audit. Analyzes the specification and
  existing test suite to find untested features, then generates
  adversarial test cases to expose the gaps. Optionally reads
  implementation source for deeper whitebox analysis.
use_for: >-
  Auditing test suite completeness, finding untested features, or
  generating adversarial test cases.
dont_use_for: >-
  Writing the initial test suite, stress testing, or opaque-box test design.
---

# Test Coverage Audit Playbook

Adversarial audit of a test suite's feature coverage.
Your job is to find what the tests **don't** test — then write
tests that expose those gaps.

## Audit Modes

This playbook operates in two modes depending on available inputs:

- **Opaque-box** (spec + tests only): Audit coverage against the
  specification. Use when implementation source is not available
  or when testing must be requirement-driven.
- **Whitebox** (spec + tests + source): Additionally analyze
  implementation code to find untested code paths and potential
  bugs. Use when you have access to the implementation source.

## Prerequisites

You need access to:

1. **Specification** — `ORIGINAL_REQUEST.md`, `PROJECT.md`, or any
   document listing what the product must do
2. **Existing test suite** — the tests you are auditing
3. **Implementation source code** (whitebox mode only) — the product
   being tested. Enables Source B analysis in Phase 1.
4. **Reference implementation** (if available) — an oracle to verify
   your adversarial tests produce the correct output

## Audit Procedure

### Phase 1: Feature Matrix Extraction

Build a comprehensive checklist of every feature the product supports.
Use **three sources** (any missing source = lower confidence):

**Source A — Specification** (most authoritative):
Read `ORIGINAL_REQUEST.md` or equivalent. Extract every capability
the product claims to support — including **implicit features**
that the specification entails but does not explicitly enumerate.
For example, a specification that says "implement standard X" implies
all features defined by that standard; you must expand these into
concrete, testable items. For each, create a row:

```
| Feature | Source | Category |
|---------|--------|----------|
| JSON array parsing | Spec §4.2 | Input handling |
| Graceful shutdown on SIGTERM | Spec §7.1 | Lifecycle |
```

**Source B — Implementation** (whitebox mode only):
Analyze the source code and development artifacts to identify
additional attack surfaces. Look for:

- Code paths that no existing test exercises
- Worker-reported caveats, known weaknesses, or TODO comments (in their `handoff.md`)
- Complex branching logic (switch/case, type dispatch) with
  partial test coverage
- Potential bugs visible from code inspection (off-by-one,
  missing error handling, unvalidated inputs)
- Line-level coverage data from `blaze coverage` (Google mode) —
  use uncovered lines as a starting point for identifying
  untested code paths

Compare against Source A to find features present in code but absent
from spec (or vice versa). Skip this source in opaque-box mode.

**Source C — Existing test suite** (catches features only known to tests):
Scan test file names and test code. If a test exercises a feature
not in your matrix, add it.

**Merge**: Combine all sources. Each feature should appear
once. Mark which sources mention it.

### Phase 2: Feature-to-Test Mapping

For each feature in the matrix, find whether the existing test suite
exercises it:

```
| Feature | Test File(s) | Covered? |
|---------|--------------|----------|
| Nested object parsing | (none) | ❌ No |
| Flat object parsing | `parse_basic_test` | ✅ Yes |
| Graceful shutdown | (none) | ❌ No |
```

**How to determine coverage**:

- A feature is covered if at least one test would **fail** when
  the feature's implementation is broken
- A test that uses the feature incidentally (e.g., a helper that
  always takes the happy path) does NOT count as coverage
- When in doubt, trace: if I deleted the code handling this
  feature, which test would break?

### Phase 3: Gap Report

For each uncovered feature, assess:

| Feature               | Severity | Why it matters                                    |
| --------------------- | -------- | ------------------------------------------------- |
| Nested object parsing | Medium   | Only flat objects tested — recursion path skipped |
| Graceful shutdown     | High     | No test verifies resource cleanup on signal       |

**Severity criteria** (determines priority, not whether to test):

- **High**: Core feature, commonly used, likely to have bugs
- **Medium**: Secondary feature, moderate usage, may have edge cases
- **Low**: Rare feature or edge case, low probability of bug

All severity levels must be addressed. Severity only controls the
order in which adversarial tests are generated.

### Phase 4: Adversarial Test Generation

For each gap (prioritized by severity), write a test case designed
to make the product under test fail.

**Design principles**:

- **Targeted**: Focus on exercising the untested feature. If
  whitebox analysis revealed a potential bug, craft a test that
  directly triggers it.
- **Adversarial**: Combine features in ways the original test
  author likely didn't consider (e.g., deeply nested structures
  combined with edge-case inputs)
- **Self-verifying**: The test must produce a deterministic,
  verifiable output (exit code, stdout, or file output)
- **Oracle-verified**: If a reference implementation exists, verify
  that your test produces the expected output on it before reporting

**Naming convention**: Prefix adversarial tests with `adv_` to
distinguish from the original suite.

### Phase 5: Validation

1. Run every adversarial test against the **reference
   implementation** (if available). All must pass.
2. Run against the **product under test**. Record pass/fail.
3. Any failure confirms the gap was real. Report the failure with
   expected vs. actual output.
4. Any adversarial test that also fails on the reference
   implementation is a **bad test** — fix or discard it.

## Output Format

Let's follow the standard format in `handoff.md` and `gaps.md`.
