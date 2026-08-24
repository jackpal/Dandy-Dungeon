---
name: software-engineering
description: >-
  Software engineering methodology for modifying, refactoring, and extending
  large production codebases. Covers call chain analysis, side effect
  assessment, change strategy selection, and build/test verification.
  Use when modifying existing code, performing cross-file refactors,
  changing APIs, or adding features. Don't use for algorithmic puzzles
  or competitive programming.
use_for: >-
  Modifying existing code, performing cross-file refactors, changing APIs,
  or adding features.
dont_use_for: Algorithmic puzzles or competitive programming.
---

# Software Engineering Playbook

## Codebase Understanding Priority

Before making changes, understand the context in this order:

1. **Read the failing test or requirement** — understand WHAT needs to change
2. **Trace the call chain** — find all callers and callees of the target code
3. **Check dependencies** — what does this code depend on? What depends on it?
4. **Read recent changes** — understand recent evolution (blame, CL history)
5. **Identify invariants** — what assumptions does the surrounding code make?

## Side Effect Analysis

For every proposed change, answer:

- **Direct effects**: What behavior changes in the modified file?
- **Transitive effects**: What callers are affected? Do any tests break?
- **Implicit contracts**: Does this change violate any undocumented assumptions?
- **Dependency direction**: Does this change create a new dependency cycle?

## Change Strategy

| Change Scope | Strategy |
|-------------|----------|
| Single function fix | Minimal edit, verify callers unaffected |
| Cross-file refactor | Map all affected files first, change in dependency order |
| API change | Check all call sites, update callers before changing the API |
| New feature | Add behind a flag or in a new file to minimize blast radius |

## Verification Checklist

- [ ] `blaze build` passes for all affected targets
- [ ] `blaze test` passes for all affected targets
- [ ] No unintended side effects on callers (verified via call chain analysis)
- [ ] Code follows project style conventions
- [ ] BUILD dependencies are auto-generated (not manually edited)
- [ ] New code has adequate test coverage
- [ ] Documentation updated if public API changed
