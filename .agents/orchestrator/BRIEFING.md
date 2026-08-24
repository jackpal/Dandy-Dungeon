# BRIEFING — 2026-06-20T21:48:50Z

## Mission
Research, design, and implement a custom 2D compression algorithm for Dandy Dungeon's 26 levels to compile the entire game into a single flat 32KB GameBoy ROM (no-MBC) with active code+data segment size < 28KB.

## 🔒 My Identity
- Archetype: teamwork_preview_orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/orchestrator
- Original parent: parent
- Original parent conversation ID: 228afcff-0ed3-488d-9ee7-5d438382e793

## 🔒 My Workflow
- **Pattern**: Project Pattern
- **Scope document**: /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/PROJECT.md
1. **Decompose**: Broken down into 5 sequential milestones (M1: Build Revert, M2: Compression Design, M3: Implement C/Py, M4: Size Tuning, M5: Adversarial & Audit). Dual track with E2E Testing track running in parallel.
2. **Dispatch & Execute** (pick ONE):
   - **Delegate (sub-orchestrator)**: Spawn sub-orchestrators for milestones, and an E2E Testing Orchestrator for the testing track.
3. **On failure** (in this order):
   - Retry: nudge stuck agent or re-send task
   - Replace: spawn fresh agent with partial progress
   - Skip: proceed without (only if non-critical)
   - Redistribute: split stuck agent's remaining work
   - Redesign: re-partition decomposition
   - Escalate: report to parent (sub-orchestrators only, last resort)
4. **Succession**: Self-succeed when cumulative spawns >= 16 and all subagents are complete. Write handoff.md, spawn successor, kill timers.
- **Work items**:
  1. Milestone 1: Build Revert & Verification Foundation [pending]
  2. Milestone 2: Design 2D Compression & E2E Test Harness [pending]
  3. Milestone 3: Implement 2D Compressor & Decompressor [pending]
  4. Milestone 4: Integration & Size Optimization [pending]
  5. Milestone 5: Adversarial Hardening & Final Audit [pending]
- **Current phase**: 1
- **Current focus**: Milestone 1 & E2E Testing Track setup

## 🔒 Key Constraints
- Flat 32KB ROM (no-MBC, Bank 0 and Bank 1 only).
- Active code and data segments in linker map file must sum to < 28,672 bytes (28 KB).
- Zero dynamic RAM allocations (malloc/free), operating within 8KB WRAM limit.
- 100% bit-for-bit level decompression fidelity.
- Development integrity mode: zero tolerance for cheating/hardcoding.
- Never reuse a subagent after it has delivered its handoff.

## Current Parent
- Conversation ID: 228afcff-0ed3-488d-9ee7-5d438382e793
- Updated: not yet

## Key Decisions Made
- Decomposed the project into 5 sequential milestones under the Project Pattern.
- Determined that the core C engine's platform-independent design allows for an offline, mock-HAL E2E test runner for opaque-box testing.

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| E2E Testing Orchestrator | teamwork_preview_orchestrator | E2E Testing Track | completed | 4cdfadfb-6fb3-407c-93f5-8ddbf8005b56 |
| Milestone 1 Sub-orchestrator | teamwork_preview_orchestrator | Milestone 1 | completed | d19ba90e-d592-45d6-ae8c-e012f1351c9e |
| Milestone 2 Sub-orchestrator | teamwork_preview_orchestrator | Milestone 2 | completed | 909da888-11bb-42a5-8a02-a0b8cd3900ef |
| Milestone 3 Sub-orchestrator | teamwork_preview_orchestrator | Milestone 3 | completed | d1f31846-5dd2-4d37-aeb0-b69a2dcd8a16 |
| Milestone 5 Sub-orchestrator | teamwork_preview_orchestrator | Milestone 5 | in-progress | 57415878-8f23-4ebd-8268-2bb9ef066e62 |

## Succession Status
- Succession required: no
- Spawn count: 5 / 16
- Pending subagents: 57415878-8f23-4ebd-8268-2bb9ef066e62
- Predecessor: none
- Successor: not yet spawned

## Active Timers
- Heartbeat cron: task-41
- Safety timer: none
- On succession: kill all timers before spawning successor
- On context truncation: run `manage_task(Action="list")` — re-create if missing

## Artifact Index
- /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/PROJECT.md — Global project architecture, milestones, and contracts
- /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/orchestrator/plan.md — Detailed plan and verification gates
- /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/orchestrator/progress.md — Liveness heartbeat and milestone tracker
- /usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/orchestrator/context.md — Project context and technical background
