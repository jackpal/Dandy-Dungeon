# Greenfield Development Playbook

## Code Layout Convention
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
```
Note: If the project modifies an existing codebase, respect its existing directory structure.

## Phases
- Phase 0: Assess Current State
- Phase 1: Understand Before You Build
- Phase 2: Scaffold First
- Phase 3: Implement Incrementally
- Phase 4: Integration
