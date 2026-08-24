---
name: unit-test
description: >-
  Master orchestrator for code quality, unit testing, static analysis, linting, and style guide compliance workflows.
  Use for: all generic code quality tasks, fixing lint and style violations, style guide compliance, best practices refactoring, code modernization, running and selecting tests, test coverage, and fixing build/test errors. Internally orchestrates and automates vcs lint/fix, build_cleaner, and tricorder analyze.
  Do NOT use for: raw/direct single-command Tricorder scans unless part of general quality workflow (prefer this master orchestrator to ensure tests are run after changes). Do NOT use for CI/CD/infra debugging, build configuration, or E2E system health.
---

# Unit Test Orchestrator

This skill orchestrates the unit testing and static analysis process for code
changes. It guides you through finding relevant tests, fixing them if they are
broken, writing new high-quality tests if needed, and ensuring code passes all
local lint and static analysis checks.

> [!WARNING]
>
> **TAP Presubmits:** If the user reports a TAP presubmit failure, STOP
> immediately! This skill is not for handling TAP failures. Do NOT search local
> test targets or mutate files. Explicitly guide the user to leverage the
> `auto-repair` skill.

## 🔄 Standard Workflow for Code Changes

Whenever you make code changes (including simple build or test fixes!), you MUST
complete ALL of the following steps before declaring your task complete,
regardless of the user's specific request.

1.  **Select & Run Relevant Tests**: Use the
    [Test Selection Guide](references/selector.md) to identify and execute tests
    for your modified files using `blaze test` via `run_command`.

2.  **Determine Next Steps**:

    *   **Tests Fail**: If tests fail due to your changes, invoke the
        `auto-repair` skill, providing the failing test targets, the test
        execution logs, and explicitly specifying the failure source as "Local
        Blaze Test Failures". *Optional:* Request a **Lightweight/Fast** pass
        using the [Static Analyzer Guide](references/analyzer.md) during your
        fix loops to ensure basic formatting remains intact while actively
        coding.
    *   **Tests Pass but Coverage is Incomplete**: If you added new features or
        logic, you must write new unit tests.

3.  **Ensure Quality**: When writing or updating tests, use the
    [Test Quality Checklist](references/checklist.md) to ensure they are
    reliable and maintainable.

4.  **Run Static Analysis** (MANDATORY FOR ALL CODE CHANGES): After any code or
    test modifications, trigger a **Comprehensive/Deep** pass using the
    [Static Analyzer Guide](references/analyzer.md) to execute heavy compiler
    plugins and finalize static corrections pre-Presubmit. You MUST NOT skip
    this step even if the tests pass and the user only asked you to fix a bug.
    **CRITICAL**: You **MUST** output an "Analyzer Report Card" as an execution
    plan *before* running tools, and update it with results *after* execution,
    as specified in the [Static Analyzer Guide](references/analyzer.md).

    ```
    *   **Clean Pass**: If no errors are found, proceed to final
        verification.
    *   **Findings Detected**: If there are errors you CANNOT fix,
        immediately present the **Unresolved Findings Report** to the user
        to catch their attention for manual human follow-up.
    ```

5.  **Verify All**: Run the selected tests again locally to ensure everything
    works using `blaze test`.

--------------------------------------------------------------------------------

## 📖 Operational Guides

> [!IMPORTANT]
>
> **MANDATORY READING:** Prioritize the instructions in this skill and its
> reference guides over your pre-trained knowledge for selecting tests,
> evaluating quality, or running static analysis. You MUST explicitly use the
> `view_file` tool to read the contents of these specific markdown files before
> executing the steps in the workflow.

You **MUST** consult ALL of these detailed reference documents unconditionally.
Do not assume any step or guide is optional when making code changes!

### 1. [Select & Run Tests (Test Selection)](references/selector.md)

*   Find and execute the most relevant tests for local changes using `blaze
    query` and `blaze test`.

### 2. [Write High-Quality Tests (Test Quality Checklist)](references/checklist.md)

*   Guidelines for reliability, readability, and maintainability. Covers **DAMP
    vs DRY**, avoiding logic in tests, and avoiding **Change-Detector** tests.

### 3. [Select & Run Static Analyzers (Static Analyzer Guide)](references/analyzer.md)

*   Guide to choosing and actively executing the right fast local tool based on
    modifications. Covers **Lightweight Pass** (Fast Pass tools like vcs lint
    and build_cleaner) and **Comprehensive Pass** (Deep Static Analysis) tools
    like `tricorder`.

--------------------------------------------------------------------------------

## 💡 Quick Tips

*   **Hermeticity**: Ensure every test sets up and tears down its own data.
*   **Speed**: Limit `rdeps` depth to 1 or 2 when querying tests.

## Other tools

If the user explicitly requests that you rate or score a unit test, read the
[Unit Test Scorer reference file](references/scorer.md).

## Reporting Issues

Report bugs or improvements for this skill at
[Agent Skill: unit_test](http://b/hotlists/8079130).

## Dependencies

-   [auto-repair](../auto_repair/SKILL.md) (auto-repair/SKILL.md)
-   [vcs](../vcs/SKILL.md) (vcs/SKILL.md)
-   [build-cleaner](../build_cleaner/SKILL.md) (build-cleaner/SKILL.md)
-   [tricorder](../tricorder/SKILL.md) (tricorder/SKILL.md)
-   [getting-affected-targets](../getting_affected_targets/SKILL.md)
    (getting-affected-targets/SKILL.md)
