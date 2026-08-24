# Test Coverage Audit Playbook

Adversarial audit of a test suite's feature coverage.
Your job is to find what the tests **don't** test — then write
tests that expose those gaps.

## Audit Procedure

### Phase 1: Feature Matrix Extraction
Build a comprehensive checklist of every feature the product supports using Spec, Implementation, and Existing tests.

### Phase 2: Feature-to-Test Mapping
Determine which features are covered (at least one test would fail if the implementation is broken).

### Phase 3: Gap Report
For each uncovered feature, assess severity.

### Phase 4: Adversarial Test Generation
Write adversarial tests (`adv_` prefix) targeting gaps.

### Phase 5: Validation
Run tests, record pass/fail, verify against reference if available.
