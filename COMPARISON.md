# Renee Framework: Worktree Comparison Report

## Overview

Both **renee-codex** and **renee-claude** are parallel implementations of the Renee AI-native turn-based game framework, developed from the same `DESIGN.md` specification. Despite sharing the same design document, they have diverged significantly in implementation philosophy, completeness, and architectural decisions.

| Worktree | Path | Self-Assessment |
|----------|------|-----------------|
| **renee-codex** | `workspace/renee-codex` | Partial implementation (~70%), honest about gaps |
| **renee-claude** | `workspace/renee-claude` | Claims "fully implemented" with 195 tests |

---

## Executive Summary

| Aspect | renee-codex | renee-claude |
|--------|-------------|--------------|
| **Claimed Status** | Partially Implemented (many 🟨) | Fully Implemented (all ✅) |
| **Test Count** | Not specified | 195 tests across 8 files |
| **Architecture** | Event-sourced, pipeline-centric | Orchestrator-centric (Game class) |
| **CLI Framework** | argparse (stdlib) | typer + rich (required deps) |
| **Pydantic** | Core dep, fast runtime | Core dep |
| **Game Loop** | No central orchestrator | Full Game class with lifecycle hooks |
| **Error Handling** | Structured ReneeError class | Standard Python exceptions |
| **Package Exports** | Rich (9 types) | Minimal (3 types) |

### Winner by Category

| Category | Winner | Reason |
|----------|--------|--------|
| **Event-Sourced Architecture** | renee-codex | Event appliers, replay support, multiplayer sync |
| **Game Orchestration** | renee-claude | Full Game class with real-time/turn-based loops |
| **Rule System Introspection** | renee-claude | `to_json()`, `get_summary()`, intent support |
| **Multiplayer** | renee-codex | Complete TCP server/client with NDJSON |
| **CLI Tooling** | renee-claude | More commands (new, run, validate, simulate) |
| **ECS Features** | renee-claude | Templates, bulk ops, clone, serialization |
| **Error Handling** | renee-codex | Structured errors with codes, hints, context |
| **Rule Decorators** | renee-codex | `@rule` decorator as specified in DESIGN.md |

---

## 1. Structural Differences

### Dependencies (pyproject.toml)

```
renee-codex                          | renee-claude
-------------------------------------|-------------------------------------
pydantic>=2.0                        | pydantic>=2.0
pyyaml>=6.0                          | pyyaml>=6.0
                                     | typer>=0.9.0 (REQUIRED)
                                     | rich>=13.0.0 (REQUIRED)
                                     |
[optional-dependencies]              |
cli = ["rich>=13.0", "typer>=0.9"]   | graphics = ["pygame>=2.5.0"]
pygame = ["pygame>=2.0"]             |
                                     |
Entry: renee.cli.main:main           | Entry: renee.cli.main:app
```

**Key Difference**: renee-codex treats rich/typer as optional; renee-claude requires them.

### Directory Layout

| Directory | renee-codex | renee-claude |
|-----------|-------------|--------------|
| `render/` vs `rendering/` | `rendering/` | `render/` |
| `game.py` | Not present | 576 lines, full orchestrator |
| `errors.py` | Structured error system | Not present |
| `examples/` | In `src/renee/examples/` | At project root |
| `impact/` | Dedicated module | Part of `simulation/` |
| `repl/` | Dedicated module | Part of `cli/` |
| Module docs | Minimal | Extensive per-module READMEs |

### Package Exports (__init__.py)

```python
# renee-codex (rich exports - 9 types)
__all__ = [
    "ActionPipeline", "EventBus", "Grid", "RuleEngine",
    "SchemaRegistry", "TurnManager", "World",
    "EntityId", "Position", "__version__",
]

# renee-claude (minimal exports - 3 types)
__all__ = [
    "World", "EntityId", "Position", "__version__",
]
```

**Philosophy**: Codex exposes framework primitives directly; Claude centralizes access through the Game orchestrator class.

---

## 2. Core System Comparisons

### 2.1 ECS World

| Feature | renee-codex | renee-claude |
|---------|-------------|--------------|
| **Lines of Code** | ~270 | ~463 |
| **Snapshot Type** | `WorldSnapshot` frozen dataclass | UUID string (internal storage) |
| **Intent Fields** | `set_intent()`, `get_intent()` | Not implemented |
| **Entity Templates** | Not implemented | `register_template()`, `spawn_from_template()` |
| **Bulk Operations** | Limited | `destroy_all()`, `destroy_by_tag()`, `clone_entity()` |
| **Query by Tag** | Via `query(..., tags=set)` | Dedicated `query_by_tag(tag)` |
| **Lifecycle Hooks** | Private: `_on_spawn`, `_on_destroy` | Public: 4 hooks including component events |
| **EventBus Integration** | Optional bus for lifecycle events | No event bus integration |
| **Serialization** | No `to_dict()` | `to_dict()`, `from_dict()` |
| **Spawn Method** | `spawn(components, tags, intent)` | Not available |

**renee-codex World** - Event-integrated, intent-aware:
```python
def __init__(self, *, event_bus: EventBus | None = None):
    self._intents: dict[EntityId, str] = {}

def spawn(self, components, *, tags=(), intent=None) -> EntityId:
    # Creates entity, adds components/tags/intent, emits event

def snapshot(self) -> WorldSnapshot:  # Returns frozen dataclass
```

**renee-claude World** - Template-focused, self-contained:
```python
def __init__(self):
    self._templates: dict[str, dict] = {}
    self._snapshots: dict[str, dict[str, Any]] = {}  # UUID-keyed
    self.on_entity_created: list[Callable]  # Public hooks

def spawn_from_template(self, name: str, overrides: dict) -> EntityId
def clone_entity(self, entity: EntityId) -> EntityId
def snapshot(self) -> str:  # Returns UUID
def to_dict(self) -> dict
```

### 2.2 Action Pipeline

| Feature | renee-codex | renee-claude |
|---------|-------------|--------------|
| **Constructor** | Requires world, optional bus/schemas/rules/turns | No parameters |
| **Turn Validation** | Built-in player turn checking | Must implement externally |
| **Event Appliers** | `EventApplierRegistry` for replays | Not present |
| **Schema Coercion** | Auto-coerces params via schema | Uses manual validators |
| **Return Type** | `ActionResult` dataclass with events tuple | `ActionResult` with factory methods |
| **Event Emission** | Automatic via context | Returns events for caller to emit |
| **Replay Support** | `apply_event()` for sync/replay | Not supported |

**renee-codex Pipeline** - Integrated event-sourcing:
```python
class ActionPipeline:
    def __init__(self, *, world, bus, schemas, rules, turns, appliers): ...

    def execute(self, action, *, actor, params) -> ActionResult:
        # 1. Turn validation
        # 2. Schema coercion
        # 3. Pre-rules
        # 4. Handler + flush events through appliers
        # 5. Post-rules
        # 6. Emit completion event + turn.sync

    def apply_event(self, event_type, payload, *, strict=True) -> bool:
        # For replay/multiplayer sync
```

**renee-claude Pipeline** - Standalone:
```python
class ActionPipeline:
    def __init__(self):
        self._handlers: dict[str, ActionHandler] = {}
        self._validators: dict[str, ActionValidator] = {}
        self._pre_rules: dict[str, list[_RuleEntry]] = {}

    def execute(self, action: Action, world: World) -> ActionResult:
        # 1. Check handler exists
        # 2. Run validator
        # 3. Pre-rules
        # 4. Handler
        # 5. Post-rules
        # 6. Return result
```

### 2.3 Rule Engine

| Feature | renee-codex | renee-claude |
|---------|-------------|--------------|
| **Lines of Code** | ~73 | ~251 |
| **Decorator Support** | `@rule(phase="pre", priority=10)` | Must register Rule objects manually |
| **Rule Storage** | `__renee_rule__` attribute | Full Rule dataclass |
| **Priority Order** | Higher priority first | Lower priority first |
| **Filtering** | By phase only, uses `when` predicate | By `action_types` list and phase |
| **Introspection** | `rules(phase=)` | `list_rules()`, `get_rule()`, `get_summary()`, `to_json()` |
| **Intent Support** | Not on rules | Rules have optional `intent` field |
| **Unregister** | Not supported | `unregister(rule_name)` |

**renee-codex Rules** - Functional decorators (per DESIGN.md):
```python
@rule(phase="pre", priority=10, when=lambda ctx: ctx.action == "attack")
def range_check(ctx: ActionContext):
    if too_far:
        ctx.cancel("Out of range")

# RuleEngine.run(): Higher priority first
```

**renee-claude Rules** - Object-oriented with introspection:
```python
@dataclass
class Rule:
    name: str
    phase: str
    priority: int  # Lower = earlier
    action_types: list[str]
    condition: Callable | None
    handler: Callable
    intent: str | None

class RuleEngine:
    def to_json(self, indent=None) -> str
    def get_summary(self) -> dict  # Statistics
```

### 2.4 Event Bus

| Feature | renee-codex | renee-claude |
|---------|-------------|--------------|
| **Event Type** | Generic with `type: str` field | Typed event classes |
| **Metadata** | `EventMeta` (id, timestamp, turn, actor) | `EventMetadata` (event_id, timestamp, turn) |
| **Wildcard** | `on("*", handler)` | `subscribe_wildcard(handler)` |
| **Query API** | `history(type, turn, actor, since_id, until_id, predicate)` | `query(type, turn)`, `get_history(start_turn)` |
| **Built-in Events** | action_completed, action_cancelled, entity_spawned, turn.sync | Typed: EntityCreated, ComponentAdded, TurnStart, GameEnd, etc. |

### 2.5 Game Orchestrator

| Feature | renee-codex | renee-claude |
|---------|-------------|--------------|
| **Central Game Class** | Not present | Full 576-line Game class |
| **Lifecycle Hooks** | N/A | `@game.on_start`, `@game.on_update`, `@game.on_render`, `@game.on_shutdown` |
| **Game Loop** | User-implemented | Built-in real-time and turn-based modes |
| **Config Loading** | N/A | `GameConfig.from_yaml()` |
| **State Export** | N/A | `export_state()`, `export_state_json()` |
| **RNG Seeding** | User-implemented | Built-in from config |
| **Subsystem Init** | Manual | `init_turn_manager()`, `init_renderer()`, etc. |

**This is the most significant architectural divergence.**

---

## 3. CLI Comparison

### renee-codex (argparse)

```
renee --version
renee --json

renee schemas list --path FILE [--kind]
renee schemas show --path FILE --kind KIND --name NAME
renee assets scan --root DIR [--manifest] [--constants]
renee demo local [--renderer]
renee demo server [--host] [--port]
renee demo client [--host] [--port] [--renderer]
renee impact schema --path FILE --kind KIND --name NAME
renee repl demo
```

### renee-claude (typer)

```
renee --json

renee new NAME [--template] [--path]
renee run [--project] [--headless]
renee validate [--project]
renee schema [NAME] [--list] [--type]
renee query [--entity] [--component] [--tag]
renee simulate SCENARIO [--runs] [--seed]
renee impact CHANGE
renee repl [--project] [--json-mode]
```

**Key Difference**: renee-claude has more "project-oriented" commands (new, run, validate); renee-codex focuses on introspection and demos.

---

## 4. Multiplayer Architecture

| Feature | renee-codex | renee-claude |
|---------|-------------|--------------|
| **Server** | `MultiplayerServer` (TCP, authoritative) | `GameServer` with lobby/rooms |
| **Client** | `MultiplayerClient` (connects + syncs) | `NetworkServer` abstraction |
| **Protocol** | NDJSON (newline-delimited JSON) | Protocol abstraction |
| **Sync Model** | Event-sourced (broadcasts events) | Event-based |
| **Join Snapshot** | Sends world + turn state | Documented |
| **Event Log** | NDJSON persistence | async_session.py |
| **Async Mode** | EventLog replay | Documented |
| **Hidden Info** | Not implemented | Claimed complete |

**Key Difference**: renee-codex has working TCP implementation; renee-claude has more abstract session layer.

---

## 5. Error Handling

### renee-codex: Structured Errors (AI-Friendly)

```python
@dataclass(frozen=True, slots=True)
class ErrorPayload:
    code: str
    message: str
    hint: str | None = None
    context: Mapping[str, Any] | None = None

class ReneeError(Exception):
    def to_dict(self) -> dict[str, Any]

# CLI usage:
if args.json:
    print(json.dumps({"ok": False, "error": e.to_dict()}))
else:
    print(f"Error: {e.payload.message}")
    print(f"Hint: {e.payload.hint}")
```

### renee-claude: Standard Exceptions

Uses `ValueError`, `KeyError`, etc. with descriptive messages but no structured error type.

---

## 6. Semantic Types

| Type | renee-codex | renee-claude |
|------|-------------|--------------|
| **Position** | `manhattan_distance`, `chebyshev_distance`, `__add__`, `__sub__` | Same + `euclidean_distance`, `neighbors()` |
| **DiceRoll** | `parse()`, `roll(rng)` | String-based |
| **Formula** | Safe AST evaluation with functions | String-based |
| **Direction** | Not explicit | Full enum with constants |
| **Range** | Not explicit | Custom type |

---

## 7. Render System

| Command | renee-codex | renee-claude |
|---------|-------------|--------------|
| `ClearCommand` | Yes | Yes |
| `DrawRectCommand` | Yes | Yes |
| `DrawTextCommand` | Yes | Yes |
| `DrawSpriteCommand` | Yes | Yes |
| `DrawImageCommand` | Yes | No |
| `DrawTilemapCommand` | No | Yes |
| `DrawLineCommand` | No | Yes |
| `DrawCircleCommand` | No | Yes |
| **Layer Sorting** | Not explicit | `layer` field on all commands |

---

## 8. Testing

| Metric | renee-codex | renee-claude |
|--------|-------------|--------------|
| **Test Files** | 11 files | 8 files |
| **Total Tests** | Not specified | 195 tests |
| **Framework** | pytest | pytest |
| **Coverage Report** | Available | Detailed breakdown by module |

---

## 9. AI-Native Features Comparison

| Feature | renee-codex | renee-claude |
|---------|-------------|--------------|
| `--json` Flag | Exists but inconsistent | Full coverage |
| Intent Fields | In World only | In schemas, rules |
| Schema Introspection | Basic | Full |
| Impact Analysis | Minimal (schema refs only) | Full with scenarios |
| Simulation Engine | Generic stats runner | Integrated |
| REPL | Dedicated module | In CLI |
| Structured Errors | Yes (ReneeError) | No |

---

## 10. Implementation Philosophy

### renee-codex Philosophy

- **Event-Sourced Core**: Actions produce events, events modify state through appliers
- **Composable Primitives**: User assembles World + Pipeline + Rules + Turns
- **Decorator-Based Rules**: `@rule` decorator as specified in DESIGN.md
- **Multiplayer-Ready Pipeline**: Turn validation and event appliers built into pipeline
- **Demo-Driven**: Includes working grid_walk example
- **Honest Assessment**: STATUS.md clearly shows what's missing

### renee-claude Philosophy

- **Orchestrator-Centric**: Central Game class manages everything
- **Lifecycle Hooks**: Decorator-based game lifecycle (`@game.on_start`, etc.)
- **Rich Introspection**: Every system has `to_json()`, `to_dict()`, `get_summary()`
- **Documentation-Heavy**: Extensive docstrings and per-module docs
- **Fully Complete (claimed)**: 195 tests, all systems marked complete

---

## 11. Missing Features by Worktree

### renee-codex Missing

From DESIGN.md requirements:
- Game project loader (game.yaml, entity templates, scenes)
- Scenes/Maps as first-class structures
- Hidden information for multiplayer
- CLI parity (typer/rich not used by default)
- Intent validation in simulation/impact
- Full render command set (tilemaps, particles)
- Central game orchestrator

### renee-claude Missing

From observed implementation:
- `@rule` decorator (uses manual registration)
- Intent fields on World entities
- Structured error system
- Working demo/example game in src
- EventBus integration in World lifecycle
- Event appliers for replay/sync

---

## 12. Summary & Recommendations

### When to Use renee-codex

- Building multiplayer games where event-sourcing is critical
- Want decorator-based rules (`@rule`)
- Need a working example to learn from (grid_walk)
- Prefer composing primitives over orchestrated frameworks
- Building headless/backend game logic
- Need structured, AI-parseable error handling

### When to Use renee-claude

- Need a complete, tested framework out of the box
- Want lifecycle hooks (`@game.on_start`, etc.)
- Building games with real-time and turn-based modes
- Need rich AI introspection (`to_json()` everywhere)
- Prefer central orchestration over manual composition
- Want entity templates and bulk operations

### Merge Potential

The worktrees could be merged by combining:
1. renee-codex's `@rule` decorator + event appliers + structured errors
2. renee-claude's Game orchestrator + templates + introspection

| Take From codex | Take From claude |
|-----------------|------------------|
| `@rule` decorator | Game class |
| Event appliers | Entity templates |
| Structured errors | Rule introspection |
| NDJSON multiplayer | Bulk operations |
| Intent in World | CLI commands |
| Working demo | Per-module docs |

---

*Report generated: December 2024*
*Comparing: renee-codex vs renee-claude worktrees from DESIGN.md v3.0*
