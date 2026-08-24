# Greenfield Development Playbook

## Context

You are building a new module or package. Your inputs are:

-   **Task specification** — What to build, target directory, interface
    constraints, and success criteria. Your task may reference files containing
    detailed architecture or scope information — read them.
-   **Existing source** (if any) — Other modules you must integrate with.

Your job: produce a working, tested module that satisfies the specification and
integrates cleanly with the rest of the project.

## Code Layout Convention

All code you produce must follow the layout specified in your orchestrator's
`PROJECT.md` (under `## Code Layout`). If no layout is specified, follow these
defaults:

### Mode A — Existing Codebase

If the project modifies an existing codebase, respect its existing directory
structure. Do NOT reorganize files unless explicitly instructed. Before writing
any code, identify the existing conventions by examining:

-   Directory structure and naming patterns
-   Where tests are placed relative to source
-   BUILD file organization

### Mode B — Greenfield (New Code)

For new projects with no existing codebase, use this canonical layout:

```
<project_root>/
├── src/                          # All source code
│   └── <module>/                 # One directory per module
│       ├── BUILD
│       ├── <module>.h            # Header
│       ├── <module>.cc           # Implementation
│       └── <module>_test.cc      # Unit tests (co-located)
├── tests/                        # Integration / functional tests
│   ├── testcases/                # Test input files
│   ├── run_tests.sh              # Test runner
│   └── README.md
└── docs/                         # Design documents (optional)
```

**Rules**:

1.  Source code goes in `src/<module>/`. Never place source files at the project
    root.
2.  Unit tests co-locate with their source (`<module>_test.cc` next to
    `<module>.cc`).
3.  Integration/functional tests go in `tests/`. These test the system
    end-to-end, not individual modules.
4.  Each module has its own `BUILD` file.
5.  Agent working directories (`.agents/`) live at the project root and are NOT
    source code — never put implementation files there.

## Phase 0: Assess Current State

Before doing anything, check what already exists in your target directory:

| What You Find                     | Start From                            |
| --------------------------------- | ------------------------------------- |
| Empty directory (nothing exists)  | Phase 1 → Phase 2 → Phase 3           |
| Scaffold exists (BUILD, stubs, no | Phase 1 → Phase 3                     |
| logic)                            |                                       |
| Partial implementation (some      | Phase 1 → resume Phase 3 at the first |
| functions done)                   | unfinished function                   |
| Everything implemented but tests  | Phase 1 → Phase 4 — diagnose and fix  |
| failing                           |                                       |

> Always start with Phase 1 regardless of directory state. Even if code exists,
> you need to understand the interfaces before touching anything.

## Phase 1: Understand Before You Build

1.  **Understand your task** — Read your task description. Identify what needs
    to be built, the public interfaces, and the success criteria.
2.  **Read the project specification** — If your task references a project index
    or specification file (e.g., architecture, milestones, interface contracts),
    read it first. This is your primary source of truth for module boundaries
    and integration constraints.
3.  **Read modules you depend on** — If your module imports from or is imported
    by other modules, read their public interfaces. Do NOT assume — verify by
    reading the source.
4.  **Read existing code in your target directory** — If partial work exists
    from a previous attempt, understand what's done vs. what remains.
5.  **Identify external dependencies** — Search `//third_party` and existing
    BUILD files for libraries you'll need.

> Do NOT start coding until you understand your interfaces. Premature
> implementation wastes effort when interface assumptions are wrong.

## Phase 2: Scaffold First

Build the skeleton before filling in logic:

1.  **Create directory structure** — Follow the **Code Layout Convention**
    above. Check `PROJECT.md` for project-specific layout, otherwise use the
    canonical greenfield layout.
2.  **Create BUILD file** — Define library, binary, and test targets. Use
    auto-generators (`build_cleaner`, `glaze`, etc.) for deps.
3.  **Write interface stubs** — Public functions/classes with docstrings, type
    signatures, and placeholder bodies (no real logic yet).
4.  **Verify the scaffold builds** — Run `blaze build` immediately. Fix any
    import or dependency issues before writing real logic.

```
# Scaffold verification — do this BEFORE writing any logic
blaze build //path/to/your:target
```

## Phase 3: Implement Incrementally

Implement in increments rather than writing everything at once:

-   **Build frequently** — Run `blaze build` after meaningful changes. A red
    build means stop and fix before continuing.
-   **Write tests alongside implementation** — Do not defer testing to the end.
    Write tests as you implement, not after.

## Phase 4: Integration

Once your module passes its own tests:

1.  **Verify interface conformance** — Does your implementation match the
    specified interface signatures exactly?
2.  **Run dependent tests** — `blaze test` for packages that import your module
3.  **Check for missing edge cases** — Empty inputs, error paths, boundary
    values
4.  **Document** — Update module-level docstrings and any relevant docs

> Always use auto-generators for BUILD `deps`. Only add a dep manually if the
> auto-generator demonstrably cannot resolve it.

## Testing Strategy

For greenfield code, you define the test strategy. Ensure:

-   Unit tests for every public function and key internal logic
-   Edge case coverage (empty inputs, error paths, boundary values)
-   Integration tests if your module interacts with others

## Anti-Patterns

| Anti-Pattern            | Why It's Bad           | Do Instead                |
| ----------------------- | ---------------------- | ------------------------- |
| Write everything, test  | Too many bugs to debug | Implement and test        |
| at the end              | at once                | incrementally             |
| Copy-paste from other   | Creates hidden         | Write from spec,          |
| modules                 | coupling, wrong        | reference as needed       |
|                         | assumptions            |                           |
| Skip BUILD file         | Cannot verify anything | Create BUILD targets in   |
| creation                | builds                 | Phase 2                   |
| Change shared           | Breaks downstream      | Flag interface issues and |
| interfaces unilaterally | consumers              | get approval first        |

## Completion Checklist

Before reporting your work as done:

-   [ ] All public interfaces match the specification
-   [ ] `blaze build` passes for all targets
-   [ ] `blaze test` passes for all targets
-   [ ] Thorough test coverage for public functions (prioritize critical paths
    and edge cases)
-   [ ] No placeholder stubs remaining
-   [ ] Module-level docstring explains purpose and usage
