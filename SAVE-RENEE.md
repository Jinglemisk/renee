# SAVE-RENEE: Gap Analysis & Resolution Guide

**Status:** renee-merged implements ~55% of design.md. This document tracks what's missing and how to fix it.

---

## PART 1: ARCHITECTURAL DECISIONS (RESOLVED)

These conflicts between renee-claude and renee-codex have been decided:

### 1. Rule Priority Direction
**Decision:** Lower priority executes first (10 → 20)
- Matches Python's natural sort order
- Aligns with AI training corpus expectations
- **Action:** Update `rules/engine.py` to remove `reverse=True` from sort

### 2. Action/Context Structure
**Decision:** Decomposed primitives wrapped in ActionContext
- Actions as data: `(action: str, actor: EntityId, params: dict)`
- Context provides `ctx.cancel()`, `ctx.modify()` methods
- **Action:** Current merged implementation is correct, document the pattern

### 3. Event Model
**Decision:** Structural events (`type: str` + `payload: dict`)
- Enables clean JSON serialization for `--json` output
- Simple string-based history queries
- **Action:** Current merged implementation is correct

### 4. Renderer Interface
**Decision:** Protocol with `is_running()`
- Structural typing (no ABC inheritance required)
- Add `is_running() -> bool` method from renee-claude
- **Action:** Update `render/renderer.py` to add `is_running`

### 5. InputState Scope
**Decision:** Minimal core, optional extensions
- Core: `keys_pressed`, `mouse_pos`, `mouse_buttons`
- Optional: controllers, scroll (for games that need them)
- **Action:** Current merged implementation is acceptable

### 6. Module Naming
**Decision:** `render/` (not `rendering/`)
- Matches design.md terminology
- **Action:** Already correct in merged

### 7. Multiplayer Focus
**Decision:** Persistence-first with NDJSON event logging
- Event sourcing enables local, network, and async modes
- Layer session abstractions on top
- **Action:** Port `multiplayer/session.py`, `local.py`, `async_session.py` from claude

### 8. World Lifecycle Hooks
**Decision:** Opt-in hooks, events for major operations only
- Events: spawn, destroy, add_component, remove_component
- No automatic events on field mutations
- **Action:** Current merged implementation is correct

### 9. Snapshot Mechanism
**Decision:** Both named snapshots AND transient dataclass
- `world.save_snapshot("name")` for named storage
- `WorldSnapshot` dataclass for serialization
- Include `intents` in snapshot
- **Action:** Current merged has both, verify intents included

### 10. Simulation Scope
**Decision:** Scenario-based with statistical output
- AI needs N iterations → win rates, averages, distributions
- Not generic functions
- **Action:** Port full simulation system from claude (~1,900 lines)

### 11. Turns System Features
**Decision:** Include all 5 turn orders and all phase traits
- Orders: Alternating, Clockwise, Initiative, Simultaneous, Custom
- Traits: Skippable, Mandatory, Timed, Unlimited, Single-action
- **Action:** Port `turns/structure.py` and `turns/order.py` from claude

---

## PART 2: MISSING FEATURES (BY PRIORITY)

### CRITICAL (Core AI-Native Features)

| Feature | Status | Source | Lines |
|---------|--------|--------|-------|
| Simulation Engine | Stub only | `renee-claude/src/renee/simulation/` | ~1,900 |
| Intent Validation | Missing | Design.md requirement | — |
| Impact Analysis | Stub only | `renee-claude/src/renee/simulation/impact.py` | ~530 |

**Investigation:** Compare `renee-merged/src/renee/simulation/` (38 lines) vs `renee-claude/src/renee/simulation/` (1,900 lines)

### HIGH (Game Development Essentials)

| Feature | Status | Source | Lines |
|---------|--------|--------|-------|
| InputHandler | Missing | `renee-claude/src/renee/input/handler.py` | ~150 |
| Area Queries | Missing | `renee-claude/src/renee/spatial/area.py` | ~260 |
| Advanced Pathfinding | Partial | `renee-claude/src/renee/spatial/pathfinding.py` | ~260 |
| Visibility System | Partial | `renee-claude/src/renee/spatial/visibility.py` | ~150 |
| Turn Order Strategies | Missing | `renee-claude/src/renee/turns/order.py` | ~290 |
| Time Structure | Missing | `renee-claude/src/renee/turns/structure.py` | ~230 |
| Asset Loader | Missing | `renee-claude/src/renee/assets/loader.py` | ~290 |
| Asset Manifest | Missing | `renee-claude/src/renee/assets/manifest.py` | ~260 |

**Investigation:**
- Spatial: `renee-merged/src/renee/spatial/` vs `renee-claude/src/renee/spatial/`
- Turns: `renee-merged/src/renee/turns/` vs `renee-claude/src/renee/turns/`
- Assets: `renee-merged/src/renee/assets/` vs `renee-claude/src/renee/assets/`

### MEDIUM (Multiplayer & Polish)

| Feature | Status | Source |
|---------|--------|--------|
| Local Multiplayer (Hot-Seat) | Missing | `renee-claude/src/renee/multiplayer/local.py` |
| Async Multiplayer | Missing | `renee-claude/src/renee/multiplayer/async_session.py` |
| Session Abstraction | Missing | `renee-claude/src/renee/multiplayer/session.py` |
| Hidden Information Filtering | Missing | Design.md requirement |
| Reconnection/Resync | Missing | Design.md requirement |
| Rule Decorators (@pre_rule, @post_rule) | Missing | `renee-claude/src/renee/rules/decorators.py` |

**Investigation:** `renee-merged/src/renee/multiplayer/` vs `renee-claude/src/renee/multiplayer/`

### LOW (File Format & CLI)

| Feature | Status | Source |
|---------|--------|--------|
| Entity Templates from YAML | Missing | Design.md requirement |
| Scenes/Levels from YAML | Missing | Design.md requirement |
| CLI validate command | Stub | Design.md requirement |
| CLI simulate command | Stub | Design.md requirement |
| CLI context command | Missing | Design.md requirement |
| DrawParticlesCommand | Missing | Design.md requirement |
| DrawImageCommand (parallax) | Missing | Design.md requirement |

**Investigation:** `renee-merged/src/renee/cli/main.py`

---

## PART 3: TEST COVERAGE GAP

| Test File | Claude | Merged | Gap |
|-----------|--------|--------|-----|
| test_rules.py | 727 | 0 | Port entire file |
| test_input.py | 337 | 0 | Port entire file |
| test_cli.py | 286 | 0 | Port entire file |
| test_schema.py | 595 | 62 | Port 533 lines |
| test_events.py | 381 | 32 | Port 349 lines |
| test_actions.py | 372 | 104 | Port 268 lines |

**Investigation:** `renee-claude/tests/` vs `renee-merged/tests/`

---

## PART 4: DOCUMENTATION TO PORT

From renee-codex:
- `ROADMAP.md` (1,143 lines) — Development phases
- `CLAUDE.md` — AI development context
- `launch.md` (443 lines) — Verification checklist

From renee-claude:
- 13 example scripts in `examples/`
- 12 per-module READMEs

---

## PART 5: IMPLEMENTATION ORDER

```
Phase 1: Fix Conflicts
├── rules/engine.py          # Priority direction
└── render/renderer.py       # Add is_running()

Phase 2: Port Simulation (AI-Native Core)
├── simulation/simulator.py
├── simulation/scenario.py
├── simulation/statistics.py
└── simulation/impact.py

Phase 3: Port Spatial Algorithms
├── spatial/area.py
├── spatial/pathfinding.py   # Enhance existing
└── spatial/visibility.py    # Enhance existing

Phase 4: Port Turns System
├── turns/structure.py
└── turns/order.py

Phase 5: Port Assets System
├── assets/loader.py
└── assets/manifest.py

Phase 6: Port Input System
└── input/handler.py

Phase 7: Port Multiplayer Extensions
├── multiplayer/session.py
├── multiplayer/local.py
└── multiplayer/async_session.py

Phase 8: Port Tests
└── tests/test_*.py

Phase 9: Complete CLI
└── cli/main.py              # Implement stubs
```

---

## Quick Reference: Directory Comparison

| System | Merged | Claude | Codex |
|--------|--------|--------|-------|
| Simulation | `simulation/` (38 LOC) | `simulation/` (1,900 LOC) | `simulation/` (38 LOC) |
| Spatial | `spatial/` (~200 LOC) | `spatial/` (~670 LOC) | `spatial/` (~200 LOC) |
| Turns | `turns/` (~120 LOC) | `turns/` (~520 LOC) | `turns/` (~120 LOC) |
| Assets | `assets/` (~130 LOC) | `assets/` (~550 LOC) | `assets/` (~130 LOC) |
| Input | `input/` (~100 LOC) | `input/` (~250 LOC) | `input/` (~100 LOC) |
| Multiplayer | `multiplayer/` (~400 LOC) | `multiplayer/` (~600 LOC) | `multiplayer/` (~400 LOC) |
| Tests | `tests/` (~830 LOC) | `tests/` (~3,000 LOC) | — |

**Total gap: ~4,800 lines of production code + ~2,200 lines of tests**
