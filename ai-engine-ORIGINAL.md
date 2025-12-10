# AI_ENGINE_NAME: Design Document

## An AI-Native Framework for Turn-Based Games

---

# Executive Summary

**AI_ENGINE_NAME** is a turn-based game framework designed from the ground up for AI-assisted development. Unlike traditional game engines that assume human developers reading documentation and clicking through GUIs, AI_ENGINE_NAME assumes your co-developer is an AI coding agent like Claude Code.

### What "AI-Native" Means

Traditional engines are hostile to AI agents:
- Binary formats AI can't read
- GUI-configured values not in code
- Implicit state scattered across files
- Documentation written for humans who can "explore"

AI_ENGINE_NAME inverts this:
- **Everything is text** — YAML configs, Python code, JSON state
- **Everything is introspectable** — Query schemas, state, history at runtime
- **Everything is declarative** — Describe *what*, not *how*
- **Everything is predictable** — Rigid conventions, explicit patterns

### Technology Stack

| Layer | Technology | Why |
|-------|------------|-----|
| **Language** | Python 3.11+ | AI fluency (largest training corpus), rich ecosystem, strong typing |
| **Type System** | dataclasses, pydantic | Schema validation, IDE support, runtime type checking |
| **CLI** | typer + rich | Beautiful, typed command-line interface |
| **Data** | pyyaml, tomli | Native YAML/TOML parsing for all configuration |
| **Testing** | pytest + custom DSL | Flexible test approaches for different needs |
| **Rendering** | pygame (primary) | Simple, well-documented, battle-tested |
| **Distribution** | pyinstaller, nuitka | Single executable output for easy sharing |

### Flagship Features

| Feature | What It Does | Why AI Loves It |
|---------|--------------|-----------------|
| **Schema Registry** | Runtime-queryable type definitions | AI asks "what fields does a Monster have?" and gets an answer |
| **Intent Fields** | Natural language descriptions on entities | AI compares implementation against stated goals |
| **`--json` on Everything** | Machine-parseable output from all commands | AI reliably parses structured responses |
| **Impact Analysis** | `ai_engine impact` shows change effects | AI knows what breaks before making changes |
| **What-If Simulation** | Test hypothetical changes without committing | AI experiments with balance safely |
| **Snapshot/Rollback** | First-class state snapshots | AI tries, evaluates, undoes freely |
| **Context Generation** | Token-aware, task-specific file selection | AI gets exactly the context it needs |
| **REPL with JSON Mode** | Interactive game manipulation | AI experiments, observes, iterates |
| **Event Sourcing** | Complete history of everything that happened | AI debugs by reading the past |
| **Static Type Hints** | Full typing on all APIs | AI understands signatures and types |
| **Rule Engine** | Game logic as Python decorators (not DSL) | AI writes rules in familiar Python |
| **Render Commands** | Abstract output, pluggable renderers | AI tests games without graphics |

### Deferred Features (Build Later If Needed)

| Feature | Status | Why Deferred |
|---------|--------|--------------|
| Custom rule DSL | Phase 5 | Python predicates work; DSL adds complexity |
| SQL-like queries | Phase 5 | Method chaining is sufficient |
| Test DSL | Phase 5 | pytest works fine for AI |
| Multiple renderers | Phase 5 | One renderer is enough to start |
| Semantic diff | Phase 5 | Nice-to-have, not essential |

### The Core Promise

An AI agent can:
1. **Understand** any part of your game by reading text files
2. **Query** the framework to learn what's valid
3. **Experiment** in the REPL to test ideas
4. **Extend** the game using documented patterns
5. **Verify** changes with declarative tests
6. **Debug** issues by inspecting event history

No guessing. No grep-and-hope. No "I think this might work."

---

# Part 1: Architecture Overview

## High-Level Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                     Game Definition (Text Files)                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Entities │ │ Systems  │ │  Scenes  │ │  Rules   │           │
│  │  (YAML)  │ │ (Python) │ │  (YAML)  │ │  (YAML)  │           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
└───────┼────────────┼────────────┼────────────┼─────────────────┘
        │            │            │            │
        ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI_ENGINE_NAME Runtime                       │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Schema    │  │    ECS      │  │    Event    │             │
│  │  Registry   │  │   World     │  │    Bus      │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │    Rule     │  │    Turn     │  │   Query     │             │
│  │   Engine    │  │   Manager   │  │   Engine    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   State     │  │   Replay    │  │    REPL     │             │
│  │   Store     │  │   System    │  │  Interface  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│                          │                                      │
│                          ▼                                      │
│                 ┌─────────────────┐                            │
│                 │ Render Commands │                            │
│                 │    (Output)     │                            │
│                 └────────┬────────┘                            │
└──────────────────────────┼──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│    Pygame    │  │   Terminal   │  │     Web      │
│   Renderer   │  │   Renderer   │  │   Renderer   │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Key Architectural Decisions

### 1. Headless Core, Pluggable Renderers

The framework produces **render commands**, not pixels:

```python
# The framework outputs this (data):
render_commands = [
    {"type": "clear", "color": "#1a1a2e"},
    {"type": "draw_sprite", "id": "goblin_1", "sprite": "goblin_idle", "x": 320, "y": 240},
    {"type": "draw_sprite", "id": "player", "sprite": "knight_walk_2", "x": 160, "y": 240},
    {"type": "draw_text", "text": "Player's Turn", "x": 10, "y": 10, "size": 16},
    {"type": "draw_rect", "x": 10, "y": 30, "w": 100, "h": 10, "color": "red"},  # health bar
]

# A renderer consumes this and draws actual pixels
```

**Why this matters:**
- AI can run games without any graphics (headless testing)
- Same game runs on desktop, terminal, web, mobile
- Framework focuses purely on game logic
- Render commands are inspectable (AI can verify "is the goblin being drawn?")

### 2. Entity-Component-System (ECS)

Entities are IDs. Components are data. Systems are logic.

```python
# Entity is just a number
player_id = 1
goblin_id = 2

# Components are pure data attached to entities
components = {
    1: {  # player
        "Position": {"x": 5, "y": 3},
        "Health": {"current": 100, "max": 100},
        "Combat": {"attack": 15, "defense": 5},
        "Inventory": {"items": ["sword", "potion"]},
    },
    2: {  # goblin
        "Position": {"x": 7, "y": 3},
        "Health": {"current": 20, "max": 20},
        "Combat": {"attack": 8, "defense": 2},
        "AI": {"behavior": "aggressive"},
    }
}

# Systems process entities with specific components
def combat_system(world, attacker_id, defender_id):
    attacker = world.get_components(attacker_id, ["Combat"])
    defender = world.get_components(defender_id, ["Health", "Combat"])

    damage = max(0, attacker["Combat"]["attack"] - defender["Combat"]["defense"])
    defender["Health"]["current"] -= damage

    return {"type": "damage_dealt", "amount": damage, "target": defender_id}
```

**Why this matters for AI:**
- Flat structure (no deep inheritance to trace)
- Components are readable data (not hidden in object state)
- Systems are isolated (modify one without understanding others)
- Easy to query ("find all entities with Health below 50%")

### 3. Event Sourcing

The game is a sequence of events, not mutable state:

```python
event_log = [
    {"turn": 1, "type": "game_started", "players": [1, 2]},
    {"turn": 1, "type": "turn_started", "player": 1},
    {"turn": 1, "type": "action_move", "entity": 1, "from": [0,0], "to": [1,0]},
    {"turn": 1, "type": "tile_entered", "entity": 1, "tile": "trap", "effect": "damage"},
    {"turn": 1, "type": "damage_dealt", "target": 1, "amount": 5, "source": "trap"},
    {"turn": 1, "type": "turn_ended", "player": 1},
    {"turn": 2, "type": "turn_started", "player": 2},
    # ...
]
```

**Why this matters for AI:**
- Complete history is always available
- Debugging = "find the event that caused bad state"
- Replay by re-processing events
- AI can ask "what happened on turn 5?"

### 4. Declarative Rules

Game logic expressed as data, not imperative code:

```yaml
# rules/combat_modifiers.yaml
rules:
  - id: flanking_bonus
    description: "Bonus when ally adjacent to target"
    when:
      - "action.type == 'melee_attack'"
      - "count(allies_adjacent_to(action.target)) >= 1"
    then:
      - modify: "action.damage"
        add: 2

  - id: high_ground_advantage
    description: "Bonus when attacking from elevation"
    when:
      - "action.type == 'melee_attack'"
      - "tile_elevation(action.source) > tile_elevation(action.target)"
    then:
      - modify: "action.damage"
        multiply: 1.25
```

**Why this matters for AI:**
- Rules are readable without tracing code
- AI can add rules without touching systems
- Rules can be queried ("what rules affect melee attacks?")
- Balance changes are data changes, not code changes

---

# Part 2: Project Structure

## Directory Layout

```
my_game/
├── game.yaml                    # Project manifest (single source of truth)
├── schemas/                     # Type definitions (AI can query these)
│   ├── components.yaml          # Component schemas
│   ├── events.yaml              # Event type definitions
│   └── actions.yaml             # Valid action definitions
├── entities/                    # Entity templates (one file per type)
│   ├── _templates/              # Canonical examples for AI to copy
│   │   ├── basic_enemy.yaml
│   │   ├── collectible.yaml
│   │   └── npc.yaml
│   ├── player.yaml
│   ├── goblin.yaml
│   └── treasure_chest.yaml
├── systems/                     # Game logic (Python)
│   ├── combat.py
│   ├── movement.py
│   ├── inventory.py
│   └── ai_behavior.py
├── rules/                       # Declarative rules (YAML)
│   ├── combat_modifiers.yaml
│   ├── tile_effects.yaml
│   └── win_conditions.yaml
├── scenes/                      # Level/map definitions
│   ├── level_1.yaml
│   ├── level_1.test.yaml        # Tests for this scene
│   └── level_2.yaml
├── state/                       # State configuration
│   ├── schema.yaml              # What state exists (global, scene, entity)
│   └── initial.yaml             # Starting state
├── assets/                      # Asset references (not binary files)
│   └── manifest.yaml            # Maps asset IDs to file paths
├── .ai/                         # AI-assist configuration
│   ├── context.yaml             # What files to include in AI context
│   ├── tasks/                   # Task-specific prompts
│   │   ├── add_entity.md
│   │   ├── add_rule.md
│   │   └── balance_combat.md
│   └── templates/               # Output templates
│       ├── entity.yaml.template
│       └── system.py.template
├── .claude/                     # Claude Code integration
│   └── commands/
│       ├── add-monster.md       # /add-monster slash command
│       ├── balance-check.md     # /balance-check slash command
│       └── playtest.md          # /playtest slash command
├── tests/                       # Test scenarios
│   ├── combat.test.yaml
│   ├── movement.test.yaml
│   └── integration.test.yaml
└── docs/                        # Documentation
    ├── ARCHITECTURE.md
    ├── API.md
    └── PATTERNS.md              # Common patterns for AI to follow
```

## File Naming Conventions

| Pattern | Meaning | Example |
|---------|---------|---------|
| `*.yaml` | Data definition | `goblin.yaml` |
| `*.py` | Logic/behavior | `combat.py` |
| `*.test.yaml` | Test scenarios | `level_1.test.yaml` |
| `*.md` | Documentation/prompts | `add_entity.md` |
| `_templates/` | Canonical examples | `_templates/basic_enemy.yaml` |
| `_` prefix | Internal/private | `_helpers.py` |

**Why rigid conventions matter:**
AI agents pattern-match. "To add a monster, create a file in `entities/`" works because the convention is absolute. No exceptions, no special cases.

---

# Part 3: Core Systems

## 3.1 Schema Registry

The Schema Registry stores type definitions and validates data at runtime. This is the foundation of AI-nativeness — the framework can describe itself.

### Schema Definition Format

```yaml
# schemas/components.yaml

Position:
  description: "Location on the game board"
  fields:
    x:
      type: integer
      description: "Horizontal tile coordinate"
    y:
      type: integer
      description: "Vertical tile coordinate"
  required: [x, y]

Health:
  description: "Entity's health pool"
  fields:
    current:
      type: integer
      min: 0
      description: "Current health points"
    max:
      type: integer
      min: 1
      description: "Maximum health points"
  required: [current, max]
  invariants:
    - "current <= max"

Combat:
  description: "Combat statistics for fighting entities"
  fields:
    attack:
      type: integer
      min: 0
      default: 1
      description: "Base damage dealt"
    defense:
      type: integer
      min: 0
      default: 0
      description: "Damage reduction"
    attack_range:
      type: integer
      min: 1
      default: 1
      description: "Tiles away this entity can attack"
  required: [attack]

Inventory:
  description: "Items carried by entity"
  fields:
    items:
      type: array
      items: string
      default: []
      description: "List of item IDs"
    capacity:
      type: integer
      min: 1
      default: 10
      description: "Maximum items"
  invariants:
    - "len(items) <= capacity"
```

### Runtime Introspection API

```python
from ai_engine import schema

# Get schema for a component type
position_schema = schema.get("Position")
print(position_schema)
# {
#   "description": "Location on the game board",
#   "fields": {
#     "x": {"type": "integer", "description": "Horizontal tile coordinate"},
#     "y": {"type": "integer", "description": "Vertical tile coordinate"}
#   },
#   "required": ["x", "y"]
# }

# List all registered schemas
all_schemas = schema.list()
print(all_schemas)
# ["Position", "Health", "Combat", "Inventory", "AI", ...]

# Validate data against schema
is_valid, errors = schema.validate("Health", {"current": 50, "max": 100})
print(is_valid)  # True

is_valid, errors = schema.validate("Health", {"current": 150, "max": 100})
print(is_valid)   # False
print(errors)     # ["Invariant failed: current <= max (150 <= 100)"]

# Get default values
defaults = schema.defaults("Combat")
print(defaults)
# {"attack": 1, "defense": 0, "attack_range": 1}
```

### Implementation with Pydantic

The Schema Registry can be implemented using pydantic for robust validation:

```python
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional

class Health(BaseModel):
    current: int
    max: int

    @field_validator('max')
    @classmethod
    def max_must_be_positive(cls, v):
        if v < 1:
            raise ValueError('max must be at least 1')
        return v

    @model_validator(mode='after')
    def current_not_exceed_max(self):
        if self.current > self.max:
            raise ValueError(f'current ({self.current}) cannot exceed max ({self.max})')
        return self

class Combat(BaseModel):
    attack: int = 1
    defense: int = 0
    attack_range: int = 1

class Position(BaseModel):
    x: int
    y: int

# Usage
goblin_health = Health(current=20, max=20)  # Valid
broken = Health(current=150, max=100)       # Raises ValidationError
```

This provides:
- **Type safety** at runtime
- **Clear error messages** when validation fails
- **IDE autocomplete** for component fields
- **JSON serialization** built-in

### CLI Access

```bash
$ ai_engine schema list
Position
Health
Combat
Inventory
AI
...

$ ai_engine schema show Health
Health:
  description: "Entity's health pool"
  fields:
    current: integer (required) - Current health points
    max: integer (required) - Maximum health points
  invariants:
    - current <= max

$ ai_engine schema validate entities/goblin.yaml
Validating entities/goblin.yaml...
  ✓ Position: valid
  ✓ Health: valid
  ✓ Combat: valid
  ✓ AI: valid
All components valid.

$ ai_engine schema validate entities/broken.yaml
Validating entities/broken.yaml...
  ✗ Health: Invariant failed: current <= max (150 <= 100)
  ✗ Combat: Missing required field: attack
2 errors found.
```

---

## 3.2 Entity-Component-System (ECS)

### Entity Definition Format

```yaml
# entities/goblin.yaml

name: Goblin
description: "A weak but numerous enemy that attacks in groups"
intent: |
  A basic melee enemy for early game encounters.
  - Should be defeatable by a starting player in 2-3 hits
  - Deals low but consistent damage
  - No special abilities, just basic attack
  - Often spawns in groups of 2-3

tags: [enemy, creature, melee, early_game]

components:
  Position:
    # No defaults - set when spawned

  Health:
    current: 20
    max: 20

  Combat:
    attack: 8
    defense: 2
    attack_range: 1

  AI:
    behavior: aggressive
    detection_range: 5

  Sprite:
    idle: goblin_idle
    attack: goblin_attack
    hurt: goblin_hurt
    death: goblin_death

# What happens when this entity is spawned
on_spawn:
  - emit: {event: "enemy_spawned", data: {type: "goblin"}}

# What happens when this entity dies
on_death:
  - emit: {event: "enemy_killed", data: {type: "goblin"}}
  - chance: 0.3
    spawn: {type: "Collectible/GoldCoin", at: "self.position"}
```

### The `intent` Field

This is a critical AI-native feature. The `intent` field describes what this entity is *supposed* to do in natural language.

When an AI agent is asked "the goblin seems too hard", it can:
1. Read the `intent`: "defeatable in 2-3 hits by starting player"
2. Check player's starting attack (15) and goblin's health (20)
3. Calculate: 15 damage → 2 hits to kill (with no defense considered)
4. Check goblin's defense (2) → 13 damage per hit → still 2 hits
5. Confirm: Implementation matches intent, issue is elsewhere

Without `intent`, AI must guess what "too hard" means.

### ECS Runtime API

```python
from ai_engine import World

# Create world and spawn entities
world = World()

# Spawn from template
goblin_id = world.spawn("Goblin", position={"x": 5, "y": 3})
player_id = world.spawn("Player", position={"x": 0, "y": 0})

# Query components
goblin_health = world.get(goblin_id, "Health")
print(goblin_health)  # {"current": 20, "max": 20}

# Modify components
world.set(goblin_id, "Health", {"current": 15, "max": 20})

# Query by components
enemies = world.query(has=["AI", "Combat"], where={"AI.behavior": "aggressive"})
print(enemies)  # [goblin_id]

# Query by tags
early_enemies = world.query(tags=["enemy", "early_game"])
print(early_enemies)  # [goblin_id]

# Check if entity exists
exists = world.exists(goblin_id)  # True

# Remove entity
world.destroy(goblin_id)
```

### Advanced Queries

```python
# Find all damaged entities
damaged = world.query(
    has=["Health"],
    where=lambda e: e["Health"]["current"] < e["Health"]["max"]
)

# Find all entities within range of a position
nearby = world.query(
    has=["Position"],
    where=lambda e: distance(e["Position"], {"x": 5, "y": 5}) <= 3
)

# Find entities by multiple criteria
targets = world.query(
    has=["Health", "Position"],
    tags=["enemy"],
    where={
        "Health.current": {"$gt": 0},  # alive
        "Position.x": {"$lte": 10}     # in western half
    }
)
```

### Static Type Hints (Critical for AI)

All components and APIs must have comprehensive type hints. This provides crucial context for AI agents:

```python
from dataclasses import dataclass
from typing import Optional, List, TypeVar, Type

@dataclass
class Position:
    x: int
    y: int

@dataclass
class Health:
    current: int
    max: int

    def __post_init__(self):
        if self.current > self.max:
            raise ValueError(f"current ({self.current}) cannot exceed max ({self.max})")

@dataclass
class Combat:
    attack: int = 1
    defense: int = 0
    attack_range: int = 1

T = TypeVar('T')

class World:
    def spawn(self, template: str, **overrides) -> EntityId:
        """Spawn an entity from a template."""
        ...

    def get(self, entity: EntityId, component_type: Type[T]) -> T:
        """Get a component from an entity. Returns typed component."""
        ...

    def set(self, entity: EntityId, component: T) -> None:
        """Set a component on an entity."""
        ...

    def query(
        self,
        has: Optional[List[Type]] = None,
        tags: Optional[List[str]] = None,
        where: Optional[Callable[[Entity], bool]] = None
    ) -> List[Entity]:
        """Query entities by components, tags, or predicate."""
        ...
```

**Why this matters for AI**:
- AI sees method signatures and understands expected types
- IDE-style autocomplete context is available
- Runtime type checking catches errors early
- Generic types (like `get(...) -> T`) provide inference

### Snapshot/Rollback (First-Class Feature)

AI agents experiment by trying, evaluating, and undoing. Snapshot/rollback must be a core feature, not an afterthought.

```python
from ai_engine import Game

game = Game("game.yaml")

# Take a snapshot before experimenting
snapshot = game.snapshot()

# Try something
game.do_action("attack", source="player", target="goblin")
result = game.evaluate()  # Check outcome

if result.player_health < 20:
    # Bad outcome - rollback
    game.restore(snapshot)
    # Try something else
    game.do_action("use_item", item="health_potion")
else:
    # Good outcome - keep it
    pass

# Snapshots are cheap and composable
snapshots = []
for target in enemies:
    snap = game.snapshot()
    game.do_action("attack", target=target)
    result = game.evaluate()
    snapshots.append((target, result, snap))

# Find best option
best = max(snapshots, key=lambda x: x[1].score)
game.restore(best[2])
game.do_action("attack", target=best[0])
```

### REPL Snapshot Commands

```bash
$ ai_engine repl scenes/level_1.yaml

> snapshot save before_fight
Saved snapshot: before_fight

> do attack target=goblin_1
Attack dealt 10 damage.

> do attack target=goblin_1
Goblin died.

> snapshot save after_fight
Saved snapshot: after_fight

> snapshot restore before_fight
Restored to: before_fight

> snapshot list
  before_fight (turn 1, 5 entities)
  after_fight (turn 1, 4 entities)

> snapshot diff before_fight after_fight
Entity 2 (Goblin):
  - Health.current: 20 → destroyed
Events between snapshots:
  - damage_dealt: 10 to entity 2
  - damage_dealt: 10 to entity 2
  - entity_died: entity 2
```

### API Design Principles

```python
# Snapshots are immutable
snapshot = game.snapshot()
game.do_action(...)  # Modifies game, not snapshot

# Snapshots are serializable
snapshot.save("debug_state.json")
loaded = Snapshot.load("debug_state.json")
game.restore(loaded)

# Snapshots include full state
snapshot.entities      # All entity data
snapshot.events        # Event history
snapshot.state         # Global/scene state
snapshot.turn          # Turn number
snapshot.rng_state     # Random seed state for determinism
```

---

## 3.3 Turn Manager

Handles turn order, phases, and player/AI alternation.

### Turn Structure Definition

```yaml
# game.yaml (excerpt)

turn_structure:
  type: round_robin  # Options: round_robin, initiative, real_time_with_pause

  phases:
    - name: start_of_turn
      auto: true  # Runs automatically
      triggers:
        - emit: {event: "turn_started"}
        - run_system: "regeneration"
        - run_system: "status_effects_tick"

    - name: action
      auto: false  # Waits for player/AI input
      allowed_actions: [move, attack, use_item, skip]
      action_points: 2

    - name: end_of_turn
      auto: true
      triggers:
        - run_system: "check_win_conditions"
        - emit: {event: "turn_ended"}

  player_order:
    method: fixed  # Options: fixed, roll_initiative, speed_stat
    # For 'fixed': order determined by spawn order
    # For 'roll_initiative': roll at start of each round
    # For 'speed_stat': sort by entity.Combat.speed each round
```

### Turn Manager API

```python
from ai_engine import TurnManager

turns = TurnManager(world, config)

# Get current turn state
state = turns.get_state()
print(state)
# {
#   "round": 1,
#   "current_player": player_id,
#   "phase": "action",
#   "action_points_remaining": 2,
#   "valid_actions": ["move", "attack", "use_item", "skip"]
# }

# Check if action is valid
can_move = turns.can_do("move", {"to": {"x": 1, "y": 0}})
print(can_move)  # {"valid": True} or {"valid": False, "reason": "Tile occupied"}

# Perform action
result = turns.do_action("move", {"to": {"x": 1, "y": 0}})
print(result)
# {
#   "success": True,
#   "action_points_used": 1,
#   "events": [
#     {"type": "entity_moved", "entity": player_id, "from": [0,0], "to": [1,0]},
#     {"type": "tile_entered", "entity": player_id, "tile_type": "normal"}
#   ]
# }

# End turn manually
turns.end_turn()

# Advance to next player (usually automatic)
turns.next_player()
```

---

## 3.4 Event Bus

Decoupled communication between systems.

### Event Definition

```yaml
# schemas/events.yaml

entity_moved:
  description: "An entity changed position"
  fields:
    entity: {type: entity_id, required: true}
    from: {type: position, required: true}
    to: {type: position, required: true}
    cause: {type: string, default: "movement"}  # movement, knockback, teleport

damage_dealt:
  description: "An entity took damage"
  fields:
    target: {type: entity_id, required: true}
    amount: {type: integer, required: true}
    source: {type: entity_id}  # optional - could be trap, not entity
    damage_type: {type: string, default: "physical"}

entity_died:
  description: "An entity's health reached zero"
  fields:
    entity: {type: entity_id, required: true}
    killer: {type: entity_id}  # optional
    position: {type: position, required: true}

item_collected:
  description: "An entity picked up an item"
  fields:
    entity: {type: entity_id, required: true}
    item: {type: string, required: true}
    position: {type: position, required: true}
```

### Event Bus API

```python
from ai_engine import events

# Subscribe to events
@events.on("damage_dealt")
def log_damage(event):
    print(f"Entity {event.target} took {event.amount} damage")

@events.on("entity_died")
def handle_death(event):
    world.destroy(event.entity)
    if event.killer:
        grant_experience(event.killer, 10)

# Subscribe to multiple events
@events.on(["damage_dealt", "healing_received"])
def update_health_bar(event):
    render_health_bar(event.target)

# Emit events
events.emit("damage_dealt", {
    "target": goblin_id,
    "amount": 15,
    "source": player_id,
    "damage_type": "physical"
})

# Query event history
recent_damage = events.history(
    type="damage_dealt",
    last=10  # last 10 events of this type
)

last_turn_events = events.history(
    turn=3  # all events from turn 3
)

# Structured output (for AI)
print(events.history(last=5, format="json"))
```

---

## 3.5 Rule Engine

Declarative game logic that lives in data files, not scattered across code.

### Rule Definition Format

```yaml
# rules/combat_modifiers.yaml

rules:
  - id: backstab
    description: "Bonus damage when attacking from behind"
    priority: 10  # Higher priority rules apply first
    when:
      - "action.type == 'melee_attack'"
      - "is_behind(action.source, action.target)"
    then:
      - modify: "action.damage"
        multiply: 1.5
      - emit:
          event: "backstab_triggered"
          data: {attacker: "action.source", target: "action.target"}

  - id: wounded_penalty
    description: "Reduced attack when below 25% health"
    when:
      - "action.type in ['melee_attack', 'ranged_attack']"
      - "entity_health_percent(action.source) < 0.25"
    then:
      - modify: "action.damage"
        multiply: 0.75
      - log: "Wounded penalty applied to {action.source}"

  - id: resistance_physical
    description: "Physical resistance reduces physical damage"
    when:
      - "action.type == 'damage'"
      - "action.damage_type == 'physical'"
      - "has_component(action.target, 'Resistances')"
    then:
      - modify: "action.amount"
        subtract: "get_component(action.target, 'Resistances').physical"
        min: 1  # Always deal at least 1 damage
```

### Rule Engine API

```python
from ai_engine import rules

# Load rules
rules.load("rules/combat_modifiers.yaml")

# Apply rules to an action
action = {
    "type": "melee_attack",
    "source": player_id,
    "target": goblin_id,
    "damage": 15
}

modified_action = rules.apply(action, context={"world": world})
print(modified_action)
# {"type": "melee_attack", "source": 1, "target": 2, "damage": 22}  # backstab applied

# Query which rules would apply
matching = rules.match(action)
print(matching)
# [{"id": "backstab", "description": "Bonus damage when attacking from behind"}]

# List all rules affecting a mechanic
combat_rules = rules.list(affecting="damage")
print(combat_rules)
# ["backstab", "wounded_penalty", "resistance_physical", ...]

# Validate rules file
errors = rules.validate("rules/custom.yaml")
if errors:
    print(errors)
    # ["Rule 'my_rule': Unknown function 'nonexistent_func'"]
```

### Scene-Local Rules

Rules can also be defined within scenes for level-specific logic:

```yaml
# scenes/level_1.yaml

name: "Dungeon Entrance"

# ... entities, tilemap, etc ...

rules:
  - id: tutorial_invulnerability
    description: "Player can't die in tutorial area"
    when:
      - "action.type == 'damage'"
      - "action.target == player"
      - "scene.area == 'tutorial'"
    then:
      - modify: "action.amount"
        set: 0
      - emit: {event: "tutorial_hint", data: {message: "You would have taken damage!"}}

  - id: boss_door_locked
    description: "Boss door requires key"
    when:
      - "action.type == 'interact'"
      - "action.target == 'boss_door'"
      - "not has_item(action.source, 'boss_key')"
    then:
      - cancel_action: true
      - emit: {event: "message", data: {text: "The door is locked. Find the key."}}
```

---

## 3.6 State Manager

Centralized state with explicit schema, persistence, and queries.

### State Schema Definition

```yaml
# state/schema.yaml

global:
  # Persists across scenes and game sessions
  player_stats:
    type: object
    persist: true
    properties:
      total_kills: {type: integer, default: 0}
      total_deaths: {type: integer, default: 0}
      gold_collected: {type: integer, default: 0}
      achievements: {type: array, items: string, default: []}

  settings:
    type: object
    persist: true
    properties:
      difficulty: {type: string, enum: [easy, normal, hard], default: normal}
      music_volume: {type: float, min: 0, max: 1, default: 0.8}
      sfx_volume: {type: float, min: 0, max: 1, default: 1.0}

scene:
  # Resets when scene changes
  enemies_defeated: {type: integer, default: 0}
  secrets_found: {type: integer, default: 0}
  time_elapsed: {type: float, default: 0}
  triggered_events: {type: array, items: string, default: []}

entity:
  # Per-entity state (beyond components)
  status_effects:
    type: array
    items:
      type: object
      properties:
        effect: {type: string}
        duration: {type: integer}
        source: {type: entity_id}
```

### State Manager API

```python
from ai_engine import state

# Read state
kills = state.get("global.player_stats.total_kills")
difficulty = state.get("global.settings.difficulty")
enemies = state.get("scene.enemies_defeated")

# Write state
state.set("scene.enemies_defeated", enemies + 1)
state.set("global.player_stats.total_kills", kills + 1)

# Batch updates (atomic)
state.update({
    "scene.enemies_defeated": enemies + 1,
    "global.player_stats.total_kills": kills + 1,
    "global.player_stats.gold_collected": lambda x: x + 10  # increment
})

# Query state changes
changes = state.changes_since(turn=5)
print(changes)
# [
#   {"path": "scene.enemies_defeated", "old": 2, "new": 3, "turn": 6},
#   {"path": "global.player_stats.gold_collected", "old": 50, "new": 60, "turn": 6}
# ]

# Snapshot and restore
snapshot = state.snapshot()
# ... game progresses ...
state.restore(snapshot)  # Undo to snapshot

# Save/load persistent state
state.save("savegame_1.json")
state.load("savegame_1.json")
```

---

## 3.7 Query Engine

SQL-like queries on game state for complex lookups.

```python
from ai_engine import query

# Simple queries
enemies = query("entities WHERE has(AI) AND has(Combat)")
low_health = query("entities WHERE Health.current < 10")
in_range = query("entities WHERE distance(Position, {x:5, y:5}) <= 3")

# Complex queries
dangerous = query("""
    entities
    WHERE has(Combat)
    AND Combat.attack > 10
    AND distance(Position, player.Position) <= 5
    ORDER BY Combat.attack DESC
    LIMIT 3
""")

# Query with joins
combat_log = query("""
    events
    WHERE type = 'damage_dealt'
    AND turn >= 5
    JOIN entities AS target ON events.target = target.id
    SELECT events.amount, target.name, events.source
""")

# Aggregate queries
stats = query("""
    SELECT
        count(*) as total_enemies,
        avg(Health.current) as avg_health,
        sum(Combat.attack) as total_attack_power
    FROM entities
    WHERE tags CONTAINS 'enemy'
""")
```

### CLI Access

```bash
$ ai_engine query "entities WHERE tags CONTAINS 'enemy'"
[
  {"id": 2, "name": "Goblin", "position": {"x": 5, "y": 3}},
  {"id": 3, "name": "Goblin", "position": {"x": 6, "y": 3}},
  {"id": 4, "name": "Skeleton", "position": {"x": 10, "y": 7}}
]

$ ai_engine query "events WHERE type = 'damage_dealt' LIMIT 5"
[
  {"turn": 3, "type": "damage_dealt", "target": 2, "amount": 15, "source": 1},
  {"turn": 3, "type": "damage_dealt", "target": 1, "amount": 8, "source": 2},
  ...
]
```

---

## 3.8 Replay System

Deterministic replay with seeded randomness.

### Recording and Playback

```python
from ai_engine import replay

# Start recording
replay.start_recording()

# ... play the game ...

# Stop and save
replay.stop_recording()
replay.save("playthrough_1.replay")

# Load and replay
replay.load("playthrough_1.replay")
replay.play()  # Replays entire game

# Step through replay
replay.load("playthrough_1.replay")
while not replay.finished:
    replay.step()  # Advance one action
    print(world.get_state())

# Jump to specific point
replay.seek(turn=10, action=3)  # Turn 10, action 3

# Get replay info
info = replay.info("playthrough_1.replay")
print(info)
# {
#   "seed": 12345,
#   "turns": 42,
#   "total_actions": 156,
#   "players": ["Player 1", "Player 2"],
#   "winner": "Player 1",
#   "duration_seconds": 847
# }
```

### Seeded Randomness

All randomness MUST go through the framework's RNG:

```python
from ai_engine import rng

# Seeded at game start
rng.seed(12345)  # Or use random seed and save it

# All random operations use this
damage = rng.randint(5, 10)  # NOT random.randint()
crit = rng.random() < 0.15   # NOT random.random()
choice = rng.choice(items)   # NOT random.choice()

# Replay will produce identical results if same seed
```

### Time Simulation

```python
# Advance simulation time
from ai_engine import simulation

# Simulate 5 seconds of game time
simulation.advance(seconds=5.0)

# Simulate until condition
simulation.advance_until(
    condition=lambda: state.get("scene.enemies_defeated") >= 3,
    max_seconds=60.0
)

# Simulate N turns
simulation.advance_turns(5)
```

---

# Part 4: AI-Native Features

This is the core differentiator. These features exist specifically to make AI agents effective.

## 4.1 Natural Language Intent Fields

Every entity, system, and rule can have an `intent` field:

```yaml
# entities/boss_dragon.yaml

name: Dragon
intent: |
  The final boss of the dungeon. A challenging fight that:
  - Requires 4-5 turns to defeat with good play
  - Has a "rage" phase below 30% health with increased damage
  - Telegraphs big attacks one turn in advance
  - Can be cheesed with fire resistance potions (intended)
  - Should feel epic but fair, not RNG-dependent

description: "A massive fire-breathing dragon guarding the treasure hoard"

# ... components ...
```

```yaml
# rules/dragon_rage.yaml

rules:
  - id: dragon_rage_mode
    intent: |
      When dragon is wounded, it becomes more dangerous but also
      more vulnerable. This creates a risk/reward dynamic where
      players must decide whether to play safe or go all-in.

    description: "Dragon enters rage below 30% health"
    when:
      - "entity.name == 'Dragon'"
      - "entity_health_percent(entity) < 0.30"
      - "not has_status(entity, 'enraged')"
    then:
      - add_status: {entity: "entity", status: "enraged", duration: -1}
      - modify: "entity.Combat.attack"
        multiply: 1.5
      - modify: "entity.Combat.defense"
        multiply: 0.5
      - emit: {event: "boss_phase_change", data: {phase: "rage"}}
```

**How AI uses this:**

When asked "the dragon feels too easy", AI can:
1. Read intent: "4-5 turns to defeat with good play"
2. Simulate combat with player stats
3. Check if actual turns match intent
4. Identify discrepancy and adjust stats

When asked "add a second phase to the dragon fight", AI can:
1. Read intent: already has rage phase
2. Ask: "The dragon already has a rage phase below 30% health. Do you want a third phase, or to modify the existing rage phase?"

## 4.2 Template Directory Pattern

```
entities/
├── _templates/
│   ├── basic_enemy.yaml      # Copy this for simple enemies
│   ├── ranged_enemy.yaml     # Copy this for archers, mages
│   ├── boss.yaml             # Copy this for boss fights
│   ├── collectible.yaml      # Copy this for items
│   ├── interactable.yaml     # Copy this for doors, chests
│   └── npc.yaml              # Copy this for friendly NPCs
```

```yaml
# entities/_templates/basic_enemy.yaml

# TEMPLATE: Basic Melee Enemy
# Copy this file and modify for new enemy types.
# Required changes marked with TODO.

name: TODO_ENEMY_NAME  # TODO: Change this
description: "TODO: Describe this enemy"
intent: |
  TODO: Describe what this enemy should do and feel like.
  - How hard should it be?
  - What's its role (swarm, tank, glass cannon)?
  - Any special behaviors?

tags: [enemy, creature, TODO_ADD_TAGS]

components:
  Position:
    # Set when spawned

  Health:
    current: 20      # TODO: Adjust for difficulty
    max: 20

  Combat:
    attack: 8        # TODO: Adjust for difficulty
    defense: 2       # TODO: Adjust for difficulty
    attack_range: 1  # Melee = 1, Ranged = higher

  AI:
    behavior: aggressive  # Options: aggressive, defensive, passive, patrol
    detection_range: 5    # Tiles

  Sprite:
    idle: TODO_SPRITE_IDLE
    attack: TODO_SPRITE_ATTACK
    hurt: TODO_SPRITE_HURT
    death: TODO_SPRITE_DEATH

on_death:
  - emit: {event: "enemy_killed", data: {type: "TODO_ENEMY_TYPE"}}
  # TODO: Add loot drops if needed
```

**How AI uses this:**

When asked "create a skeleton archer enemy", AI:
1. Copies `_templates/ranged_enemy.yaml`
2. Fills in TODOs
3. Adjusts values based on intent
4. Validates against schema

## 4.3 REPL Interface

Interactive exploration and manipulation.

```bash
$ ai_engine repl scenes/level_1.yaml

AI_ENGINE_NAME REPL v0.1.0
Scene: level_1.yaml loaded
Type 'help' for commands, 'quit' to exit.

> status
Turn: 1
Current Player: player (id: 1)
Phase: action
Action Points: 2/2
Entities: 5 (1 player, 3 enemies, 1 chest)

> inspect player
{
  "id": 1,
  "name": "Player",
  "components": {
    "Position": {"x": 2, "y": 3},
    "Health": {"current": 100, "max": 100},
    "Combat": {"attack": 15, "defense": 5},
    "Inventory": {"items": ["sword"], "capacity": 10}
  },
  "tags": ["player", "hero"]
}

> query entities where tags contains "enemy"
[
  {"id": 2, "name": "Goblin", "Position": {"x": 5, "y": 3}},
  {"id": 3, "name": "Goblin", "Position": {"x": 6, "y": 4}},
  {"id": 4, "name": "Skeleton", "Position": {"x": 10, "y": 7}}
]

> set entity 2 Health.current 5
OK: Entity 2 Health.current = 5

> spawn Goblin at 8,8
Created entity 5 (Goblin) at (8, 8)

> do move to 3,3
Action 'move' executed.
Events:
  - entity_moved: player from (2,3) to (3,3)
  - tile_entered: normal tile
Action points: 1/2

> advance 2.0
Advanced 2.0 seconds (120 frames)
Events during advance:
  - ai_action: entity 2 moved from (5,3) to (4,3)
  - ai_action: entity 3 moved from (6,4) to (5,4)

> history 5
[Turn 1]
  1. entity_moved: player (2,3) → (3,3)
  2. ai_action: goblin_2 (5,3) → (4,3)
  3. ai_action: goblin_3 (6,4) → (5,4)
  4. turn_ended: player
  5. turn_started: goblin_2

> rules match action.type="melee_attack"
Matching rules:
  - backstab: "Bonus damage when attacking from behind"
  - flanking_bonus: "Bonus when ally adjacent to target"
  - wounded_penalty: "Reduced attack when below 25% health"

> emit damage_dealt target=2 amount=10 source=1
Event emitted: damage_dealt
Side effects:
  - Entity 2 Health: 5 → -5
  - Entity 2 destroyed (health <= 0)
  - Event emitted: entity_died

> undo
Undone last action. State restored to before 'emit'.

> save snapshot_debug_1
Saved snapshot: snapshot_debug_1.json

> quit
```

### JSON Mode for AI Agents

```bash
$ ai_engine repl --format json scenes/level_1.yaml

{"ready": true, "scene": "level_1.yaml", "entities": 5}

> {"command": "query", "query": "entities where Health.current < Health.max"}
{"result": [{"id": 2, "name": "Goblin", "Health": {"current": 15, "max": 20}}]}

> {"command": "do", "action": "attack", "target": 2}
{"success": true, "events": [{"type": "damage_dealt", "target": 2, "amount": 13}]}
```

## 4.4 Test DSL

Declarative test scenarios that AI can read and write.

```yaml
# tests/combat.test.yaml

name: "Combat System Tests"

tests:
  - name: "Basic melee attack deals correct damage"
    setup:
      load_scene: test_arena
      spawn:
        - type: Player
          id: player
          position: {x: 0, y: 0}
          components:
            Combat: {attack: 10, defense: 0}
        - type: Goblin
          id: target
          position: {x: 1, y: 0}
          components:
            Health: {current: 20, max: 20}
            Combat: {defense: 2}
    steps:
      - do: {action: attack, target: target}
      - assert: target.Health.current == 12  # 20 - (10 - 2) = 12

  - name: "Cannot attack out of range"
    setup:
      load_scene: test_arena
      spawn:
        - {type: Player, id: player, position: {x: 0, y: 0}}
        - {type: Goblin, id: target, position: {x: 5, y: 0}}  # 5 tiles away
    steps:
      - do: {action: attack, target: target}
      - assert: action_failed
      - assert: action_failure_reason == "Target out of range"
      - assert: target.Health.current == target.Health.max  # No damage

  - name: "Backstab rule applies from behind"
    setup:
      load_scene: test_arena
      spawn:
        - type: Player
          id: player
          position: {x: 5, y: 5}
          components:
            Combat: {attack: 10}
        - type: Goblin
          id: target
          position: {x: 5, y: 4}  # Facing "down" (positive y)
          components:
            AI: {facing: "down"}
            Health: {current: 30, max: 30}
            Combat: {defense: 0}
    steps:
      # Player is "behind" goblin (goblin faces down, player is above)
      - do: {action: attack, target: target}
      - assert: last_event.type == "backstab_triggered"
      - assert: target.Health.current == 15  # 30 - (10 * 1.5) = 15

  - name: "Player death triggers game over"
    setup:
      load_scene: test_arena
      spawn:
        - type: Player
          id: player
          position: {x: 0, y: 0}
          components:
            Health: {current: 5, max: 100}
        - type: Goblin
          id: enemy
          position: {x: 1, y: 0}
          components:
            Combat: {attack: 10}
    steps:
      - set: current_turn = "enemy"
      - do: {action: attack, source: enemy, target: player}
      - assert: player.Health.current <= 0
      - assert: event_emitted("game_over")
      - assert: state.game_result == "defeat"
```

### Running Tests

```bash
$ ai_engine test

Running tests...

tests/combat.test.yaml:
  ✓ Basic melee attack deals correct damage (0.02s)
  ✓ Cannot attack out of range (0.01s)
  ✓ Backstab rule applies from behind (0.03s)
  ✗ Player death triggers game over (0.02s)

    FAILED: assert: event_emitted("game_over")
    Expected: game_over event
    Actual: No such event

    Hint: Check rules/win_conditions.yaml for game_over trigger

tests/movement.test.yaml:
  ✓ Basic movement costs 1 action point
  ✓ Cannot move to occupied tile
  ✓ Cannot move through walls

5/6 tests passed (1 failed)
```

### Alternative: pytest Integration

For complex integration tests or when you need pytest's ecosystem:

```python
# tests/test_combat.py
import pytest
from ai_engine import World, load_scene

@pytest.fixture
def arena():
    """Create a test arena with player and goblin."""
    world = World()
    world.spawn("Player", id="player", position={"x": 0, "y": 0})
    world.spawn("Goblin", id="goblin", position={"x": 1, "y": 0})
    return world

def test_basic_attack_damage(arena):
    """Verify melee attack deals expected damage."""
    player = arena.get_entity("player")
    goblin = arena.get_entity("goblin")

    initial_health = arena.get(goblin, "Health")["current"]
    arena.do_action("attack", source=player, target=goblin)
    final_health = arena.get(goblin, "Health")["current"]

    expected_damage = 12 - 2  # player attack - goblin defense
    assert initial_health - final_health == expected_damage

def test_cannot_attack_out_of_range(arena):
    """Verify attack fails when target is too far."""
    arena.set("goblin", "Position", {"x": 10, "y": 0})

    result = arena.do_action("attack", source="player", target="goblin")
    assert not result["success"]
    assert "out of range" in result["reason"].lower()

@pytest.mark.parametrize("goblin_health,expected_alive", [
    (20, True),
    (10, True),
    (1, False),  # One hit kills
])
def test_goblin_survival(arena, goblin_health, expected_alive):
    """Parametrized test for different health scenarios."""
    arena.set("goblin", "Health", {"current": goblin_health, "max": 20})
    arena.do_action("attack", source="player", target="goblin")

    assert arena.exists("goblin") == expected_alive
```

Run with: `pytest tests/ -v`

The declarative `.test.yaml` format is preferred for game scenarios, but pytest works well for:
- Complex setup/teardown logic
- Parametrized testing
- Integration with CI/CD pipelines
- Using pytest plugins (coverage, profiling, etc.)

## 4.5 Semantic Diff

```bash
$ ai_engine diff

Changes since last save:

┌─────────────────────────────────────────────────────────────────┐
│ entities/goblin.yaml                                            │
├─────────────────────────────────────────────────────────────────┤
│ Combat stats changed:                                           │
│   attack: 8 → 12 (+50%)                                         │
│   defense: 2 → 3 (+50%)                                         │
│                                                                 │
│ Summary: Goblin significantly buffed                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ scenes/level_1.yaml                                             │
├─────────────────────────────────────────────────────────────────┤
│ Entities added:                                                 │
│   + Treasure Chest at (8, 5)                                    │
│   + Goblin at (7, 5)                                            │
│                                                                 │
│ Rules added:                                                    │
│   + "chest_guard": Goblin attacks if player approaches chest    │
│                                                                 │
│ Summary: Added guarded treasure encounter                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ rules/combat_modifiers.yaml                                     │
├─────────────────────────────────────────────────────────────────┤
│ Rule modified: backstab                                         │
│   damage multiplier: 1.5 → 2.0 (+33%)                           │
│                                                                 │
│ Summary: Backstab damage increased                              │
└─────────────────────────────────────────────────────────────────┘

Overall: 2 entities added, 1 entity modified, 1 rule modified
```

## 4.6 AI-Assist Hooks

### Context Configuration

```yaml
# .ai/context.yaml

# Files always included in AI context
always_include:
  - docs/ARCHITECTURE.md
  - docs/PATTERNS.md
  - schemas/components.yaml
  - schemas/events.yaml

# Task-specific context
tasks:
  add_entity:
    description: "Create a new entity type"
    prompt_file: .ai/tasks/add_entity.md
    include:
      - entities/_templates/
      - schemas/components.yaml
    examples:
      - entities/goblin.yaml
      - entities/skeleton.yaml
    output_dir: entities/
    validation: ai_engine validate entities/

  add_rule:
    description: "Create a new game rule"
    prompt_file: .ai/tasks/add_rule.md
    include:
      - rules/
      - docs/RULE_ENGINE.md
    examples:
      - rules/combat_modifiers.yaml
    output_dir: rules/
    validation: ai_engine validate rules/

  balance_entity:
    description: "Adjust entity stats for balance"
    prompt_file: .ai/tasks/balance_entity.md
    include:
      - entities/
      - docs/BALANCE_GUIDELINES.md
    run_after:
      - ai_engine test tests/combat.test.yaml
```

### Task Prompts

```markdown
<!-- .ai/tasks/add_entity.md -->

# Task: Add New Entity

You are adding a new entity to an AI_ENGINE_NAME game.

## Instructions

1. Copy the appropriate template from `entities/_templates/`:
   - `basic_enemy.yaml` for melee enemies
   - `ranged_enemy.yaml` for ranged enemies
   - `boss.yaml` for boss encounters
   - `collectible.yaml` for items
   - `interactable.yaml` for objects (doors, chests)
   - `npc.yaml` for friendly characters

2. Fill in all TODO fields:
   - `name`: Unique identifier
   - `description`: Short flavor text
   - `intent`: Design goals (balance, role, feel)
   - `tags`: Categorization
   - `components`: Stats and data
   - `sprites`: Asset references

3. Validate the entity:
   ```bash
   ai_engine validate entities/YOUR_ENTITY.yaml
   ```

4. If the entity has combat, run combat tests:
   ```bash
   ai_engine test tests/combat.test.yaml
   ```

## Balance Guidelines

- Early game enemies: 15-25 HP, 5-10 attack, 0-3 defense
- Mid game enemies: 30-50 HP, 12-18 attack, 3-6 defense
- Late game enemies: 60-100 HP, 20-30 attack, 8-12 defense
- Bosses: 150-300 HP, varies by design

## Component Reference

See `schemas/components.yaml` for all available components and their fields.
```

### CLI Context Generation

```bash
# Get context for a specific task
$ ai_engine ai-context add_entity "Fire Elemental"

=== Context for: Add Entity "Fire Elemental" ===

## Relevant Documentation
[Contents of docs/PATTERNS.md]

## Schema Reference
[Contents of schemas/components.yaml]

## Templates Available
- entities/_templates/basic_enemy.yaml
- entities/_templates/ranged_enemy.yaml
- entities/_templates/boss.yaml

## Examples
[Contents of entities/goblin.yaml]
[Contents of entities/skeleton.yaml]

## Task Instructions
[Contents of .ai/tasks/add_entity.md]

## Suggested Approach
Based on "Fire Elemental", recommend using:
- Template: basic_enemy.yaml or ranged_enemy.yaml (fire breath = ranged?)
- Tags: enemy, elemental, fire, magical
- Consider: Fire resistance, fire-based attacks, vulnerability to water

=====================================

# After implementation, run:
ai_engine validate entities/fire_elemental.yaml
ai_engine test tests/combat.test.yaml
```

## 4.7 Claude Code Integration

### Slash Commands

```markdown
<!-- .claude/commands/add-monster.md -->

Create a new monster entity for the game.

## Arguments
- $MONSTER_NAME (required): Name of the monster
- $DIFFICULTY (optional): easy/medium/hard (default: medium)

## Instructions

1. Read the task context:
   ```bash
   ai_engine ai-context add_entity "$MONSTER_NAME"
   ```

2. Choose template based on monster concept:
   - Melee attacker → basic_enemy.yaml
   - Ranged attacker → ranged_enemy.yaml
   - Major threat → boss.yaml

3. Create entity file at `entities/$MONSTER_NAME_lowercase.yaml`

4. Set stats based on difficulty:
   - easy: HP 15-25, ATK 5-10, DEF 0-3
   - medium: HP 30-50, ATK 12-18, DEF 3-6
   - hard: HP 60-100, ATK 20-30, DEF 8-12

5. Write a clear `intent` field explaining design goals

6. Validate:
   ```bash
   ai_engine validate entities/
   ai_engine test tests/combat.test.yaml
   ```

7. Report what was created and any test results
```

```markdown
<!-- .claude/commands/balance-check.md -->

Analyze game balance and suggest adjustments.

## Instructions

1. Run the balance analyzer:
   ```bash
   ai_engine analyze balance
   ```

2. Check combat simulations:
   ```bash
   ai_engine simulate combat --iterations 100
   ```

3. Compare against design intents:
   - Read `intent` fields in entities/
   - Check if actual stats match stated goals

4. Report findings:
   - Entities that don't match their intent
   - Outliers in damage/health ratios
   - Rules that never trigger
   - Rules that always trigger

5. Suggest specific stat changes with reasoning
```

```markdown
<!-- .claude/commands/playtest.md -->

Run an automated playtest session.

## Arguments
- $SCENE (optional): Scene to test (default: scenes/level_1.yaml)
- $STRATEGY (optional): random/aggressive/defensive (default: random)

## Instructions

1. Start REPL in simulation mode:
   ```bash
   ai_engine repl --simulate --strategy $STRATEGY $SCENE
   ```

2. Run simulation for 20 turns or until game end

3. Collect metrics:
   - Turns to complete
   - Player health remaining
   - Enemies killed
   - Items collected
   - Deaths/retries

4. Compare to design goals in scene's `intent` field

5. Report findings and suggest adjustments
```

### Usage

```bash
# In Claude Code
> /add-monster "Ice Wraith" hard
> /balance-check
> /playtest scenes/level_2.yaml aggressive
```

## 4.8 Structured AI Feedback Format

When AI agents make changes, they need machine-parseable feedback, not human-readable prose. Every operation that validates, tests, or analyzes should return structured JSON.

### Validation Response Format

```json
{
  "operation": "validate",
  "target": "entities/goblin.yaml",
  "passed": false,
  "errors": [
    {
      "file": "entities/goblin.yaml",
      "line": 15,
      "field": "Combat.attack",
      "error": "Value 150 exceeds schema maximum of 100",
      "suggestion": "Set Combat.attack to a value between 0 and 100"
    }
  ],
  "warnings": [
    {
      "file": "entities/goblin.yaml",
      "field": "intent",
      "warning": "Intent mentions 'low damage' but attack value 150 is above median"
    }
  ]
}
```

### Test Results Format

```json
{
  "operation": "test",
  "passed": 5,
  "failed": 1,
  "skipped": 0,
  "duration_ms": 342,
  "failures": [
    {
      "test": "goblin_dies_in_2_hits",
      "file": "tests/combat.test.yaml",
      "step": 3,
      "assertion": "target.Health.current == 0",
      "expected": 0,
      "actual": 30,
      "context": {
        "player_attack": 12,
        "goblin_defense": 2,
        "goblin_starting_health": 50,
        "hits_delivered": 2
      }
    }
  ],
  "intent_violations": [
    {
      "entity": "Goblin",
      "intent": "defeatable in 2-3 hits by starting player",
      "actual": "requires 5 hits with current stats",
      "suggestion": "Reduce Health.max from 50 to 25"
    }
  ]
}
```

### CLI Integration

All CLI commands support `--json` flag for machine-parseable output:

```bash
$ ai_engine validate entities/ --json
$ ai_engine test --json
$ ai_engine diff --json
$ ai_engine analyze balance --json
```

**This is non-negotiable for AI-native design.** Human-readable output is secondary to structured output.

---

## 4.9 Change Impact Analysis

Before AI makes a change, it should know what that change affects. The `impact` command provides this.

### Usage

```bash
$ ai_engine impact "entities/goblin.yaml:Combat.attack = 20"

Impact Analysis: Changing Goblin.Combat.attack from 8 to 20
═══════════════════════════════════════════════════════════

Rules Affected (3):
  • backstab (rules/combat_modifiers.yaml:12)
    - Uses source.Combat.attack in damage calculation
  • wounded_penalty (rules/combat_modifiers.yaml:25)
    - Modifies attack damage when wounded
  • flanking_bonus (rules/combat_modifiers.yaml:5)
    - Adds flat bonus to attack damage

Scenes Using This Entity (2):
  • scenes/level_1.yaml - 1 Goblin instance
  • scenes/level_2.yaml - 3 Goblin instances

Tests That May Fail (5):
  • tests/combat.test.yaml::goblin_dies_in_2_hits
  • tests/combat.test.yaml::basic_melee_attack_deals_correct_damage
  • tests/level_1.test.yaml::player_can_complete_level
  • tests/balance.test.yaml::early_enemies_damage_range
  • tests/balance.test.yaml::player_survives_3_hits

Intent Violations:
  ⚠ Goblin intent states: "Deals low but consistent damage"
    - Current attack (8) = low damage ✓
    - Proposed attack (20) = high damage ✗
    - Suggestion: Keep attack ≤ 12 to match "low damage" intent

Balance Impact (simulated 100 iterations):
  • Player vs Goblin win rate: 95% → 62% (-33%)
  • Average player health remaining: 35 → 12 (-66%)
  • Average turns to defeat Goblin: 2.3 → 2.3 (unchanged)

Would you like to proceed? Run: ai_engine apply "entities/goblin.yaml:Combat.attack = 20"
```

### JSON Output

```bash
$ ai_engine impact "entities/goblin.yaml:Combat.attack = 20" --json
```

```json
{
  "change": {
    "file": "entities/goblin.yaml",
    "field": "Combat.attack",
    "old_value": 8,
    "new_value": 20
  },
  "rules_affected": [
    {"id": "backstab", "file": "rules/combat_modifiers.yaml", "line": 12},
    {"id": "wounded_penalty", "file": "rules/combat_modifiers.yaml", "line": 25}
  ],
  "scenes_affected": [
    {"file": "scenes/level_1.yaml", "instances": 1},
    {"file": "scenes/level_2.yaml", "instances": 3}
  ],
  "tests_at_risk": [
    "tests/combat.test.yaml::goblin_dies_in_2_hits",
    "tests/combat.test.yaml::basic_melee_attack_deals_correct_damage"
  ],
  "intent_violations": [
    {
      "entity": "Goblin",
      "field": "Combat.attack",
      "intent_text": "Deals low but consistent damage",
      "violation": "Value 20 does not match 'low damage'",
      "suggested_max": 12
    }
  ],
  "balance_simulation": {
    "iterations": 100,
    "player_win_rate": {"before": 0.95, "after": 0.62, "delta": -0.33},
    "avg_player_health_remaining": {"before": 35, "after": 12, "delta": -23}
  }
}
```

### API Access

```python
from ai_engine import impact

result = impact.analyze(
    file="entities/goblin.yaml",
    field="Combat.attack",
    new_value=20
)

print(result.intent_violations)  # List of intent mismatches
print(result.tests_at_risk)      # Tests likely to fail
print(result.balance_simulation) # Win rate changes
```

---

## 4.10 "What If" Simulation

AI agents need to experiment without committing. The simulation system allows hypothetical changes to be tested.

### CLI Usage

```bash
# Simulate a single change
$ ai_engine simulate what-if \
    --change "goblin.Combat.attack=15" \
    --matchup "Player vs Goblin" \
    --iterations 1000

What-If Simulation Results
══════════════════════════

Change: Goblin.Combat.attack = 15 (currently 8)

Player vs Goblin (1000 iterations):
                    Current    After Change    Delta
  Player wins:      95.2%      78.4%           -16.8%
  Goblin wins:      4.8%       21.6%           +16.8%
  Avg turns:        2.3        2.8             +0.5
  Avg player HP:    35.2       22.1            -13.1

Intent Check:
  ✓ "Defeatable in 2-3 hits" - Still valid (2.8 avg turns)
  ⚠ "Player survives 3-4 hits" - Marginal (now 2.5 hits avg)
```

### Batch Simulation

```bash
# Test multiple configurations
$ ai_engine simulate sweep \
    --entity Goblin \
    --field Combat.attack \
    --range 5,10,15,20,25 \
    --matchup "Player vs Goblin" \
    --iterations 500

Sweep Results: Goblin.Combat.attack
═══════════════════════════════════

Attack | Player Wins | Avg Turns | Intent Match
-------|-------------|-----------|-------------
  5    |    98.2%    |    2.1    |     ✓
  8    |    95.2%    |    2.3    |     ✓  ← current
 10    |    89.4%    |    2.5    |     ✓
 15    |    78.4%    |    2.8    |     ⚠
 20    |    62.1%    |    3.2    |     ✗
 25    |    45.3%    |    3.8    |     ✗

Recommendation: Keep attack ≤ 12 to match intent "low damage"
```

### API Access

```python
from ai_engine import simulate

# Single what-if
result = simulate.what_if(
    changes={"entities/goblin.yaml": {"Combat.attack": 15}},
    matchup=("Player", "Goblin"),
    iterations=1000
)

print(result.player_win_rate)  # 0.784
print(result.intent_match)      # True/False
print(result.recommendation)    # "Keep attack ≤ 12..."

# Parameter sweep
sweep = simulate.sweep(
    entity="Goblin",
    field="Combat.attack",
    values=[5, 10, 15, 20, 25],
    iterations=500
)

for config in sweep.results:
    print(f"Attack {config.value}: {config.player_win_rate:.1%}")
```

### Deterministic Seeding

All simulations are deterministically seeded for reproducibility:

```bash
$ ai_engine simulate what-if --seed 12345 ...

# Same seed = same results, every time
```

---

## 4.11 Context Window Management

AI agents have limited context windows. The framework should help manage this by providing exactly the right context for each task.

### The `context` Command

```bash
$ ai_engine context --task "add enemy" --max-tokens 4000

=== CONTEXT FOR TASK: Add Enemy ===
=== Estimated tokens: ~3,847 ===

─── SCHEMA (relevant fields only) ───
# From schemas/components.yaml

Position:
  fields:
    x: {type: integer}
    y: {type: integer}

Health:
  fields:
    current: {type: integer, min: 0}
    max: {type: integer, min: 1}
  invariants: ["current <= max"]

Combat:
  fields:
    attack: {type: integer, min: 0, default: 1}
    defense: {type: integer, min: 0, default: 0}
    attack_range: {type: integer, min: 1, default: 1}

─── TEMPLATE (copy this) ───
# From entities/_templates/basic_enemy.yaml

name: TODO_ENEMY_NAME
description: "TODO: Describe this enemy"
intent: |
  TODO: Describe design goals
  - How hard should it be?
  - What's its role?

tags: [enemy, creature, TODO_ADD_TAGS]

components:
  Position: {}
  Health:
    current: 20
    max: 20
  Combat:
    attack: 8
    defense: 2
  AI:
    behavior: aggressive
  Sprite:
    idle: TODO_SPRITE

─── EXAMPLE (reference) ───
# From entities/goblin.yaml

name: Goblin
description: "A weak but numerous enemy"
intent: |
  Basic early-game enemy.
  - Defeatable in 2-3 hits
  - Deals low but consistent damage
...

─── VALIDATION COMMAND ───
ai_engine validate entities/YOUR_ENTITY.yaml

─── BALANCE GUIDELINES ───
Early game enemies: HP 15-25, ATK 5-10, DEF 0-3
Mid game enemies: HP 30-50, ATK 12-18, DEF 3-6
Late game enemies: HP 60-100, ATK 20-30, DEF 8-12

=== END CONTEXT ===
```

### Task-Specific Context

```bash
# Different tasks get different context
$ ai_engine context --task "add rule" --max-tokens 3000
$ ai_engine context --task "balance entity" --entity Goblin
$ ai_engine context --task "debug combat" --scene level_1
$ ai_engine context --task "add scene" --max-tokens 5000
```

### JSON Output for Programmatic Use

```bash
$ ai_engine context --task "add enemy" --json
```

```json
{
  "task": "add enemy",
  "estimated_tokens": 3847,
  "sections": [
    {
      "name": "schema",
      "file": "schemas/components.yaml",
      "content": "...",
      "tokens": 450
    },
    {
      "name": "template",
      "file": "entities/_templates/basic_enemy.yaml",
      "content": "...",
      "tokens": 320
    },
    {
      "name": "example",
      "file": "entities/goblin.yaml",
      "content": "...",
      "tokens": 580
    }
  ],
  "commands": {
    "validate": "ai_engine validate entities/YOUR_ENTITY.yaml",
    "test": "ai_engine test tests/combat.test.yaml"
  }
}
```

### Configuration

```yaml
# .ai/context.yaml

tasks:
  add_enemy:
    max_tokens: 4000
    include:
      - schemas/components.yaml: [Position, Health, Combat, AI, Sprite]
      - entities/_templates/basic_enemy.yaml: full
      - entities/goblin.yaml: full
      - docs/BALANCE_GUIDELINES.md: section:enemy_stats
    exclude:
      - "*.test.yaml"
    commands:
      validate: "ai_engine validate entities/{filename}"
      test: "ai_engine test tests/combat.test.yaml"

  add_rule:
    max_tokens: 3000
    include:
      - schemas/events.yaml: full
      - rules/_templates/: full
      - rules/combat_modifiers.yaml: first:2  # First 2 rules as examples
    commands:
      validate: "ai_engine validate rules/"

  balance_entity:
    max_tokens: 5000
    include:
      - entities/{entity}.yaml: full
      - entities/_templates/: full
      - docs/BALANCE_GUIDELINES.md: full
    dynamic:
      - "ai_engine simulate combat --entity {entity} --summary"
```

---

## 4.12 Inverted Documentation Priority

Traditional documentation explains concepts, then shows code. **AI-native documentation inverts this**: show the pattern first, explain second.

### Documentation Format for AI

```markdown
# PATTERN: Adding a New Enemy

## 1. Copy This Template

\`\`\`yaml
# entities/YOUR_ENEMY.yaml

name: YOUR_ENEMY_NAME
description: "One-line description"
intent: |
  Design goals:
  - Difficulty level (early/mid/late game)
  - Role (swarm, tank, glass cannon, etc.)
  - Special behaviors

tags: [enemy, creature, YOUR_TAGS]

components:
  Position: {}
  Health:
    current: 20  # Adjust for difficulty
    max: 20
  Combat:
    attack: 8    # Adjust for difficulty
    defense: 2   # Adjust for difficulty
  AI:
    behavior: aggressive
  Sprite:
    idle: your_sprite_idle
\`\`\`

## 2. Required Changes (in order)

| Line | Field | What to Change |
|------|-------|----------------|
| 3 | `name` | Unique entity name |
| 4 | `description` | Flavor text |
| 5-9 | `intent` | Design goals for AI to check against |
| 11 | `tags` | Add relevant tags |
| 16-17 | `Health` | Set HP based on difficulty tier |
| 19-21 | `Combat` | Set attack/defense based on role |
| 23 | `AI.behavior` | Choose: aggressive, defensive, patrol |
| 25 | `Sprite.idle` | Reference to sprite asset |

## 3. Validate

\`\`\`bash
ai_engine validate entities/your_enemy.yaml
\`\`\`

## 4. Test Combat Balance

\`\`\`bash
ai_engine simulate combat --entity YourEnemy --vs Player --iterations 100
\`\`\`

Expected results for early game enemy:
- Player win rate: > 90%
- Average turns to defeat: 2-3
- Player health remaining: > 50%

## 5. Reference Values

| Tier | HP | Attack | Defense | Player Wins |
|------|----|--------|---------|-------------|
| Early | 15-25 | 5-10 | 0-3 | >90% |
| Mid | 30-50 | 12-18 | 3-6 | 70-85% |
| Late | 60-100 | 20-30 | 8-12 | 50-70% |
| Boss | 150+ | varies | varies | 40-60% |
```

### Why This Order Matters

1. **Template first** — AI can immediately copy and modify
2. **Required changes as checklist** — AI knows exactly what to edit
3. **Validation command** — AI can verify its work
4. **Expected results** — AI can check if output matches intent
5. **Reference values** — AI has concrete numbers, not vague descriptions

### Anti-Pattern: Human-Style Documentation

```markdown
# ❌ DON'T: Concept-first documentation

## Understanding the Entity System

The Entity-Component-System (ECS) architecture separates data from behavior.
Entities are unique identifiers, components are pure data, and systems
contain logic. This approach offers several benefits...

[500 words of explanation]

## Creating Entities

To create an entity, you'll need to understand the component schemas first.
Let's explore each component type...

[300 more words before showing any code]
```

This wastes AI context on concepts it likely already knows. **Show the pattern. Let AI ask if it needs explanation.**

---

## 4.13 Literate Error Messages

Every error explains what, why, and how to fix:

```
Error: Action 'attack' failed

  What happened:
    Player (id: 1) attempted to attack Goblin (id: 3)

  Why it failed:
    Target out of range
    - Player position: (2, 3)
    - Target position: (7, 3)
    - Distance: 5 tiles
    - Player attack range: 1 tile

  How to fix:
    Option 1: Move closer to target
      Valid attack positions: (6,3), (7,2), (7,4), (8,3)

    Option 2: Use ranged attack (if available)
      Player has no ranged attack equipped

    Option 3: Check different target
      Entities in range: [Goblin (id: 2) at (3,3)]

  Relevant API:
    - world.query(has=["Combat"], where=lambda e: distance(e, player) <= range)
    - turns.can_do("attack", {"target": id}) → checks validity before attempting
```

```
Error: Schema validation failed for entities/broken.yaml

  What happened:
    Component 'Health' has invalid data

  Why it failed:
    Invariant violated: current <= max
    - current: 150
    - max: 100

  How to fix:
    Either:
    1. Reduce 'current' to <= 100
    2. Increase 'max' to >= 150

  Schema reference:
    Health:
      current: integer (required) - must be <= max
      max: integer (required) - must be >= 1

  Valid example:
    Health:
      current: 100
      max: 100
```

---

# Part 5: CLI Reference

## Command Overview

```bash
ai_engine <command> [options]

Core Commands:
  new <name>          Create new project
  run [scene]         Run game (optional: specific scene)
  repl [scene]        Start interactive REPL
  test [pattern]      Run tests (optional: filter by pattern)
  validate [path]     Validate files against schemas

Introspection Commands:
  schema <subcommand> Schema operations (list, show, validate)
  query <query>       Run query against game state
  info <name>         Get details about entity/rule/component

AI-Native Commands:
  impact <change>     Analyze impact of a proposed change
  simulate <type>     Run simulations (combat, what-if, sweep)
  context <task>      Generate AI-optimized context for a task
  diff                Show semantic diff of changes
  analyze <type>      Analyze game (balance, coverage, etc.)

Utility Commands:
  replay <file>       Replay a recorded game
  export <format>     Export game data (json, csv)

Global Flags:
  --json              Output in machine-parseable JSON (REQUIRED for AI agents)
  --quiet             Suppress non-essential output
  --verbose           Show detailed output
```

## The `--json` Flag

**Every command supports `--json` for machine-parseable output.** This is non-negotiable for AI-native design.

```bash
# Human-readable (default)
$ ai_engine validate entities/
Validating entities/...
  ✓ goblin.yaml
  ✗ broken.yaml: Health.current exceeds Health.max
1 error found.

# Machine-parseable (for AI agents)
$ ai_engine validate entities/ --json
{
  "command": "validate",
  "target": "entities/",
  "passed": false,
  "files_checked": 2,
  "errors": [
    {
      "file": "entities/broken.yaml",
      "line": 12,
      "field": "Health.current",
      "error": "Value 150 exceeds Health.max (100)",
      "suggestion": "Set Health.current to a value <= 100"
    }
  ]
}
```

## New AI-Native Commands

### `ai_engine impact`

Analyze the impact of a proposed change before making it.

```bash
$ ai_engine impact "entities/goblin.yaml:Combat.attack=20"
$ ai_engine impact "entities/goblin.yaml:Combat.attack=20" --json
```

See Section 4.9 for detailed output format.

### `ai_engine simulate`

Run deterministic simulations for balance testing.

```bash
# Single what-if simulation
$ ai_engine simulate what-if \
    --change "goblin.Combat.attack=15" \
    --matchup "Player vs Goblin" \
    --iterations 1000

# Parameter sweep
$ ai_engine simulate sweep \
    --entity Goblin \
    --field Combat.attack \
    --range 5,10,15,20,25 \
    --iterations 500

# Combat simulation
$ ai_engine simulate combat \
    --entity Goblin \
    --vs Player \
    --iterations 100 \
    --json
```

See Section 4.10 for detailed output format.

### `ai_engine context`

Generate AI-optimized context for a specific task.

```bash
$ ai_engine context --task "add enemy" --max-tokens 4000
$ ai_engine context --task "balance entity" --entity Goblin --json
$ ai_engine context --task "debug combat" --scene level_1
```

See Section 4.11 for detailed output format.

### `ai_engine info`

Get detailed information about any game element.

```bash
$ ai_engine info Health              # Component schema
$ ai_engine info Goblin              # Entity definition
$ ai_engine info backstab            # Rule definition
$ ai_engine info level_1             # Scene contents
$ ai_engine info damage_dealt        # Event schema
```

## Common Workflows

### Starting a New Project

```bash
$ ai_engine new my_game
Created project: my_game/
  - game.yaml (project manifest)
  - schemas/ (type definitions)
  - entities/ (entity templates)
  - systems/ (game logic)
  - scenes/ (levels)
  - rules/ (game rules)
  - tests/ (test scenarios)
  - .ai/ (AI assist config)
  - .claude/commands/ (Claude Code commands)

$ cd my_game
$ ai_engine validate
All files valid.

$ ai_engine run
Starting game...
```

### Development Cycle

```bash
# 1. Make changes to entities/goblin.yaml

# 2. Validate changes
$ ai_engine validate entities/goblin.yaml

# 3. See what changed
$ ai_engine diff

# 4. Run relevant tests
$ ai_engine test tests/combat.test.yaml

# 5. Interactive testing
$ ai_engine repl scenes/level_1.yaml
> spawn Goblin at 3,3
> do attack target=2
> inspect entity 2
```

### AI-Assisted Development

```bash
# Get context before asking AI to make changes
$ ai_engine ai-context add_entity "Necromancer"

# After AI creates file
$ ai_engine validate entities/necromancer.yaml
$ ai_engine test

# Check balance
$ ai_engine analyze balance
$ ai_engine simulate combat --entity necromancer --iterations 50
```

---

# Part 6: Rendering Interface

## Render Command Format

The framework outputs render commands as a list of operations:

```python
render_commands = [
    # Clear screen
    {"type": "clear", "color": "#1a1a2e"},

    # Draw background layers (parallax)
    {"type": "draw_image", "image": "background_1", "x": 0, "y": 0, "parallax": 0.5},

    # Draw tilemap
    {"type": "draw_tilemap", "tilemap": "level_1", "offset_x": 0, "offset_y": 0},

    # Draw entities (sorted by y for depth)
    {"type": "draw_sprite", "id": "goblin_1", "sprite": "goblin_idle_2", "x": 160, "y": 192, "flip_x": false},
    {"type": "draw_sprite", "id": "player", "sprite": "knight_walk_3", "x": 96, "y": 224, "flip_x": false},

    # Draw UI elements
    {"type": "draw_rect", "x": 10, "y": 10, "w": 100, "h": 12, "color": "#333333"},  # Health bar bg
    {"type": "draw_rect", "x": 10, "y": 10, "w": 75, "h": 12, "color": "#ff4444"},   # Health bar fill
    {"type": "draw_text", "text": "HP: 75/100", "x": 12, "y": 11, "size": 10, "color": "#ffffff"},

    {"type": "draw_text", "text": "Turn 3 - Player's Turn", "x": 10, "y": 580, "size": 14, "color": "#ffffff"},

    # Draw effects
    {"type": "draw_particles", "system": "damage_numbers", "particles": [
        {"text": "-15", "x": 165, "y": 180, "color": "#ff0000", "age": 0.3}
    ]},
]
```

## Renderer Implementation Interface

```python
# renderers/base.py

from abc import ABC, abstractmethod

class BaseRenderer(ABC):
    """Base class for AI_ENGINE_NAME renderers."""

    @abstractmethod
    def initialize(self, config: dict) -> None:
        """Set up the renderer (create window, load assets, etc.)"""
        pass

    @abstractmethod
    def render(self, commands: list) -> None:
        """Process render commands and display frame."""
        pass

    @abstractmethod
    def get_input(self) -> dict:
        """Get player input for this frame."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Clean up renderer resources."""
        pass


# renderers/pygame_renderer.py

import pygame
from .base import BaseRenderer

class PygameRenderer(BaseRenderer):
    def initialize(self, config):
        pygame.init()
        self.screen = pygame.display.set_mode((config["width"], config["height"]))
        self.sprites = {}  # Loaded sprite cache

    def render(self, commands):
        for cmd in commands:
            if cmd["type"] == "clear":
                self.screen.fill(self._parse_color(cmd["color"]))
            elif cmd["type"] == "draw_sprite":
                sprite = self._get_sprite(cmd["sprite"])
                self.screen.blit(sprite, (cmd["x"], cmd["y"]))
            elif cmd["type"] == "draw_rect":
                pygame.draw.rect(self.screen,
                    self._parse_color(cmd["color"]),
                    (cmd["x"], cmd["y"], cmd["w"], cmd["h"]))
            elif cmd["type"] == "draw_text":
                # ... text rendering
                pass
        pygame.display.flip()

    def get_input(self):
        events = pygame.event.get()
        return {
            "quit": any(e.type == pygame.QUIT for e in events),
            "keys": pygame.key.get_pressed(),
            "mouse": pygame.mouse.get_pos(),
            "clicks": [e for e in events if e.type == pygame.MOUSEBUTTONDOWN]
        }

    def shutdown(self):
        pygame.quit()


# renderers/terminal_renderer.py (ASCII art!)

class TerminalRenderer(BaseRenderer):
    def render(self, commands):
        # Convert to ASCII grid
        grid = [[' ' for _ in range(80)] for _ in range(24)]

        for cmd in commands:
            if cmd["type"] == "draw_sprite":
                char = self._sprite_to_char(cmd["sprite"])
                x, y = cmd["x"] // 10, cmd["y"] // 20  # Scale down
                if 0 <= x < 80 and 0 <= y < 24:
                    grid[y][x] = char

        # Print grid
        print("\033[2J\033[H")  # Clear terminal
        for row in grid:
            print(''.join(row))

    def _sprite_to_char(self, sprite_name):
        mapping = {
            "player": "@",
            "goblin": "g",
            "skeleton": "s",
            "wall": "#",
            "floor": ".",
            "chest": "$",
        }
        for key, char in mapping.items():
            if key in sprite_name.lower():
                return char
        return "?"


# renderers/headless.py (for testing)

class HeadlessRenderer(BaseRenderer):
    """Renderer that does nothing - for testing and AI simulation."""

    def __init__(self):
        self.last_commands = []
        self.input_queue = []

    def render(self, commands):
        self.last_commands = commands  # Store for inspection

    def get_input(self):
        if self.input_queue:
            return self.input_queue.pop(0)
        return {"quit": False, "keys": {}, "mouse": (0, 0), "clicks": []}

    def queue_input(self, input_data):
        """For testing: queue input to be returned by get_input()"""
        self.input_queue.append(input_data)

    def get_last_render(self):
        """For testing: inspect what was rendered"""
        return self.last_commands
```

## Using Renderers

```python
# main.py

from ai_engine import Game
from ai_engine.renderers import PygameRenderer, TerminalRenderer, HeadlessRenderer

# Choose renderer based on environment
import os
if os.environ.get("HEADLESS"):
    renderer = HeadlessRenderer()
elif os.environ.get("TERMINAL"):
    renderer = TerminalRenderer()
else:
    renderer = PygameRenderer()

# Create and run game
game = Game("game.yaml", renderer=renderer)
game.run()
```

```bash
# Run with different renderers
$ ai_engine run                    # Default: Pygame
$ TERMINAL=1 ai_engine run         # ASCII art in terminal
$ HEADLESS=1 ai_engine run         # No display (for testing)
```

---

# Part 7: Example - Building a Game

Let's walk through building "Dungeon Crawl" - a simple turn-based dungeon crawler.

## Step 1: Project Setup

```bash
$ ai_engine new dungeon_crawl
$ cd dungeon_crawl
```

## Step 2: Define Core Entities

```yaml
# entities/player.yaml

name: Player
description: "The hero exploring the dungeon"
intent: |
  The player-controlled character. Should feel powerful but vulnerable.
  - Can take 3-4 hits from basic enemies before dying
  - Defeats basic enemies in 2-3 hits
  - Has limited inventory for strategic decisions
  - Starts weak but can find equipment to improve

tags: [player, hero, controllable]

components:
  Position: {}

  Health:
    current: 50
    max: 50

  Combat:
    attack: 12
    defense: 3
    attack_range: 1

  Inventory:
    items: []
    capacity: 5

  Sprite:
    idle: hero_idle
    walk: hero_walk
    attack: hero_attack
    hurt: hero_hurt
    death: hero_death

on_spawn:
  - emit: {event: "player_spawned"}

on_death:
  - emit: {event: "player_died"}
  - emit: {event: "game_over", data: {result: "defeat"}}
```

```yaml
# entities/goblin.yaml

name: Goblin
description: "A small, green-skinned creature with a rusty dagger"
intent: |
  Basic early-game enemy. Teaches combat without being threatening.
  - Player should defeat in 2 hits
  - Deals ~10 damage per hit (5 hits to kill player)
  - No special abilities
  - Drops gold occasionally

tags: [enemy, creature, melee, early_game]

components:
  Position: {}

  Health:
    current: 20
    max: 20

  Combat:
    attack: 10
    defense: 2
    attack_range: 1

  AI:
    behavior: aggressive
    detection_range: 5

  Sprite:
    idle: goblin_idle
    walk: goblin_walk
    attack: goblin_attack
    hurt: goblin_hurt
    death: goblin_death

on_death:
  - emit: {event: "enemy_killed", data: {type: "goblin", xp: 10}}
  - chance: 0.5
    spawn: {type: "GoldCoin", at: "self.position"}
```

```yaml
# entities/gold_coin.yaml

name: GoldCoin
description: "A shiny gold coin"
intent: |
  Basic collectible. Rewards exploration and combat.
  - Automatically collected on contact
  - Worth 10 gold
  - Satisfying pickup (sound + particles)

tags: [collectible, treasure, auto_pickup]

components:
  Position: {}

  Collectible:
    type: gold
    value: 10
    auto_pickup: true

  Sprite:
    idle: coin_spin

on_collect:
  - modify_state: {path: "global.gold", add: 10}
  - emit: {event: "gold_collected", data: {amount: 10}}
  - emit: {event: "play_sound", data: {sound: "coin_pickup"}}
  - destroy: self
```

## Step 3: Define Rules

```yaml
# rules/combat.yaml

rules:
  - id: basic_melee_attack
    description: "Standard melee attack resolution"
    when:
      - "action.type == 'melee_attack'"
      - "distance(source.Position, target.Position) <= source.Combat.attack_range"
    then:
      - calculate:
          name: damage
          formula: "max(1, source.Combat.attack - target.Combat.defense)"
      - modify: "target.Health.current"
        subtract: "damage"
      - emit:
          event: "damage_dealt"
          data: {source: "source.id", target: "target.id", amount: "damage"}

  - id: death_check
    description: "Destroy entities at 0 or less health"
    when:
      - "entity.Health.current <= 0"
    then:
      - emit: {event: "entity_died", data: {entity: "entity.id"}}
      - trigger: "entity.on_death"
      - destroy: "entity"
```

```yaml
# rules/win_conditions.yaml

rules:
  - id: reach_exit
    description: "Win by reaching the dungeon exit"
    when:
      - "event.type == 'tile_entered'"
      - "event.entity == player"
      - "event.tile_type == 'exit'"
    then:
      - emit: {event: "level_complete"}
      - modify_state: {path: "scene.completed", set: true}

  - id: player_death
    description: "Lose when player dies"
    when:
      - "event.type == 'entity_died'"
      - "event.entity == player"
    then:
      - emit: {event: "game_over", data: {result: "defeat"}}
```

## Step 4: Create a Scene

```yaml
# scenes/level_1.yaml

name: "Dungeon Entrance"
description: "The first level - learn the basics"
intent: |
  Tutorial level that teaches:
  - Movement
  - Combat (1 goblin)
  - Collecting items (health potion)
  - Reaching the exit
  Should be completable in 1-2 minutes.

tilemap:
  width: 10
  height: 8
  tiles: |
    ##########
    #........#
    #..G.....#
    #........#
    #....H...#
    #........#
    #@......E#
    ##########
  legend:
    "#": wall
    ".": floor
    "@": player_spawn
    "G": goblin_spawn
    "H": health_potion_spawn
    "E": exit

entities:
  - type: Player
    id: player
    spawn_at: player_spawn

  - type: Goblin
    id: goblin_1
    spawn_at: goblin_spawn

  - type: HealthPotion
    id: potion_1
    spawn_at: health_potion_spawn

initial_state:
  enemies_defeated: 0
  items_collected: 0

rules:
  - id: tutorial_hint_combat
    description: "Show combat hint when near goblin"
    when:
      - "distance(player.Position, goblin_1.Position) <= 3"
      - "not 'combat_hint' in state.hints_shown"
    then:
      - emit: {event: "show_hint", data: {text: "Press SPACE to attack!"}}
      - modify_state: {path: "scene.hints_shown", append: "combat_hint"}
```

## Step 5: Write Tests

```yaml
# tests/level_1.test.yaml

name: "Level 1 Tests"

tests:
  - name: "Player can complete level"
    setup:
      load_scene: level_1
    steps:
      # Move toward goblin
      - do: {action: move, direction: up}
      - do: {action: move, direction: up}
      - do: {action: move, direction: up}
      - do: {action: move, direction: up}
      # Fight goblin
      - do: {action: move, direction: right}
      - do: {action: move, direction: right}
      - do: {action: attack, target: goblin_1}
      - do: {action: attack, target: goblin_1}
      - assert: goblin_1 not in entities
      # Get potion and exit
      - do: {action: move, direction: right}
      - do: {action: move, direction: right}
      - do: {action: move, direction: down}
      - do: {action: move, direction: down}
      - repeat: 5
        do: {action: move, direction: right}
      - assert: event_emitted("level_complete")

  - name: "Goblin dies in 2 hits"
    intent: "Verify goblin matches design intent"
    setup:
      load_scene: test_arena
      spawn:
        - {type: Player, id: player, position: {x: 0, y: 0}}
        - {type: Goblin, id: goblin, position: {x: 1, y: 0}}
    steps:
      - do: {action: attack, target: goblin}
      - assert: goblin.Health.current == 10  # 20 - (12 - 2)
      - do: {action: attack, target: goblin}
      - assert: goblin not in entities
```

## Step 6: Run and Test

```bash
$ ai_engine validate
All files valid.

$ ai_engine test
Running tests...
  ✓ Player can complete level (0.5s)
  ✓ Goblin dies in 2 hits (0.1s)
2/2 tests passed

$ ai_engine run scenes/level_1.yaml
Starting game...
```

---

# Part 8: Implementation Roadmap

This document describes the design. Building everything at once is a recipe for failure. Here's a **prioritized, phased approach** that delivers a working framework quickly while deferring complexity.

## Critical Principle: Working > Complete

A working game with 4 core systems beats a half-implemented framework with 12 systems. **Ship something playable, then expand.**

---

## Phase 1: Minimum Viable Framework (Weeks 1-4)

**Goal**: A playable turn-based game that AI agents can read and modify.

### 1.1 Schema Registry (Priority: CRITICAL)
- YAML schema definitions with validation
- Runtime introspection API (`schema.get()`, `schema.list()`, `schema.validate()`)
- `--json` output from day 1
- **Skip for now**: Complex invariant expressions (use Python validators)

### 1.2 ECS World (Priority: CRITICAL)
- Entity spawning from YAML templates
- Component attachment and querying
- Simple query methods: `world.query(has=["Health", "Combat"])`
- **Skip for now**: SQL-like query DSL (use Python lambdas/methods instead)

### 1.3 Event Bus (Priority: CRITICAL)
- Emit/subscribe pattern
- Event history storage
- Query history by turn/type
- **Skip for now**: Complex event filtering DSL

### 1.4 YAML Loaders (Priority: CRITICAL)
- Load entities from `entities/*.yaml`
- Load scenes from `scenes/*.yaml`
- Excellent YAML error messages with line numbers

### 1.5 Pygame Renderer (Priority: HIGH)
- Single renderer (not three)
- Render command consumption
- Basic input handling
- **Skip for now**: Terminal renderer, web renderer (add later)

### Deliverable: A playable prototype
```bash
ai_engine new my_game
ai_engine run
# Player can move around, attack enemies, collect items
```

---

## Phase 2: Make It Testable (Weeks 5-8)

**Goal**: AI agents can verify their changes work correctly.

### 2.1 Turn Manager (Priority: HIGH)
- Phase-based turn structure
- Action validation
- Player order management

### 2.2 Simple Rule Engine (Priority: HIGH)
- Rules as Python functions with decorators (not YAML DSL)
- Rule registration and execution
- **Skip for now**: Declarative YAML rule expressions

```python
# Start simple - Python predicates
@rule(when=lambda ctx: ctx.action.type == "melee_attack")
def apply_backstab(ctx):
    if is_behind(ctx.source, ctx.target):
        ctx.action.damage *= 1.5
```

### 2.3 CLI Validation (Priority: HIGH)
- `ai_engine validate` with `--json` output
- Schema validation for all files
- Cross-reference checking (entity refs exist, etc.)

### 2.4 pytest Integration (Priority: HIGH)
- Python test fixtures for game state
- Assertion helpers
- **Skip for now**: Custom `.test.yaml` DSL (pytest works fine)

```python
# Use pytest directly - AI knows pytest
def test_goblin_dies_in_2_hits(arena):
    arena.do_action("attack", target="goblin")
    arena.do_action("attack", target="goblin")
    assert not arena.exists("goblin")
```

### Deliverable: Testable game
```bash
ai_engine validate entities/
pytest tests/ -v
# AI can verify changes don't break things
```

---

## Phase 3: AI-Native Tooling (Weeks 9-12)

**Goal**: AI agents can understand impact of changes and experiment safely.

### 3.1 Structured JSON Output (Priority: CRITICAL)
- `--json` flag on EVERY command
- Consistent response schemas
- Machine-parseable error messages

### 3.2 Impact Analysis (Priority: HIGH)
- `ai_engine impact "entity.field=value"`
- Shows affected rules, scenes, tests
- Intent violation detection

### 3.3 Snapshot/Rollback (Priority: HIGH)
- `game.snapshot()` and `game.restore()`
- First-class API for AI experimentation
- REPL integration

### 3.4 Intent Checking (Priority: HIGH)
- Parse `intent` fields from entities/rules
- Compare stats against stated goals
- Warn on violations

### 3.5 Basic Simulation (Priority: MEDIUM)
- `ai_engine simulate combat --entity Goblin --iterations 100`
- Win rate, average turns, health remaining
- Deterministic seeding

### Deliverable: AI-assistable game
```bash
ai_engine impact "goblin.Combat.attack=15" --json
# AI sees: "5 tests at risk, intent violation detected"
```

---

## Phase 4: Developer Experience (Weeks 13-16)

**Goal**: Smooth development workflow for both humans and AI.

### 4.1 REPL Interface (Priority: MEDIUM)
- Interactive game manipulation
- JSON mode for AI agents
- Command history

### 4.2 Context Generation (Priority: MEDIUM)
- `ai_engine context --task "add enemy"`
- Token-aware truncation
- Task-specific file selection

### 4.3 Headless Renderer (Priority: MEDIUM)
- For automated testing
- Render command inspection

### 4.4 State Manager (Priority: MEDIUM)
- Global/scene/entity state separation
- Persistence to JSON
- State change tracking

### Deliverable: Full dev workflow
```bash
ai_engine repl scenes/level_1.yaml --json
ai_engine context --task "add boss" --max-tokens 4000
```

---

## Phase 5: Advanced Features (Weeks 17+)

**Goal**: Polish and power features. Only build what's actually needed.

### 5.1 Declarative Rule DSL (Priority: LOW)
- YAML-based rule expressions
- Only if Python predicates prove insufficient
- Custom expression parser

### 5.2 Query DSL (Priority: LOW)
- SQL-like entity queries
- Only if method-based queries prove insufficient

### 5.3 Test DSL (Priority: LOW)
- `.test.yaml` declarative tests
- Only if pytest proves awkward for game scenarios

### 5.4 Semantic Diff (Priority: LOW)
- Game-aware change detection
- Nice-to-have, not essential

### 5.5 Replay System (Priority: LOW)
- Recording and playback
- Useful for debugging, not core

### 5.6 Additional Renderers (Priority: LOW)
- Terminal ASCII renderer
- Web renderer
- Build on demand

### 5.7 Claude Code Integration (Priority: MEDIUM)
- `.claude/commands/` slash commands
- Only after core framework is stable

---

## What NOT to Build (Defer Indefinitely)

These add complexity without proportional value for AI agents:

| Feature | Why Defer |
|---------|-----------|
| Custom expression language for rules | Python lambdas work fine |
| SQL-like query DSL | Method chaining is sufficient |
| Multiple renderer support | One renderer is enough to start |
| Hot-reload system | Manual restart is acceptable |
| Visual level editor | AI doesn't need GUI |
| Asset pipeline | Simple file references work |
| Networking/multiplayer | Massive scope increase |
| Mod support | Premature abstraction |

---

## Complexity Warnings

### The Rule Expression Language Trap

The design shows:
```yaml
when:
  - "count(allies_adjacent_to(action.target)) >= 1"
```

This requires building:
- Expression parser
- AST evaluator
- Function registry
- Error handling

**Alternative that works today**:
```python
@rule
def flanking_bonus(ctx):
    if ctx.action.type == "melee_attack":
        if count_allies_adjacent_to(ctx.action.target) >= 1:
            ctx.action.damage += 2
```

AI agents understand Python. They don't need a custom DSL.

### The Query Language Trap

The design shows:
```python
query("SELECT avg(Health.current) FROM entities WHERE tags CONTAINS 'enemy'")
```

This requires building:
- Query parser
- Query optimizer
- Join logic

**Alternative that works today**:
```python
enemies = world.query(tags=["enemy"])
avg_health = sum(e.Health.current for e in enemies) / len(enemies)
```

Build the DSL only if the simple approach proves genuinely insufficient.

---

## Success Metrics Per Phase

| Phase | Success Criteria |
|-------|------------------|
| 1 | Can play a simple turn-based game |
| 2 | Can run `pytest` and `validate` with `--json` |
| 3 | Can run `impact` and `simulate` commands |
| 4 | Can use REPL and context generation |
| 5 | Advanced features only as needed |

---

## Recommended First Week

Day 1-2:
- Project structure scaffold
- Schema Registry with YAML loading
- `ai_engine schema list/show` commands

Day 3-4:
- ECS World basics
- Entity spawning from YAML
- Component queries

Day 5-7:
- Event Bus
- Scene loading
- Basic Pygame renderer

End of Week 1: Something renders on screen.

---

# Part 9: Distribution & Packaging

How to package and distribute games built with AI_ENGINE_NAME.

## Development Setup

```bash
# Create project with virtual environment
mkdir my_game && cd my_game
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install ai_engine pygame pyyaml

# Or with requirements.txt
pip install -r requirements.txt
```

## requirements.txt

```
# Core framework
pydantic>=2.0
pyyaml>=6.0
typer>=0.9
rich>=13.0

# Rendering
pygame>=2.5

# Development
pytest>=7.0
watchdog>=3.0  # For hot-reload
```

## pyproject.toml

```toml
[project]
name = "my-game"
version = "0.1.0"
description = "A turn-based game built with AI_ENGINE_NAME"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.0",
    "pyyaml>=6.0",
    "typer>=0.9",
    "rich>=13.0",
    "pygame>=2.5",
]

[project.scripts]
my-game = "my_game.main:main"

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "watchdog>=3.0",
    "pyinstaller>=6.0",
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
```

## Creating Executables

### PyInstaller (Recommended)

```bash
# Install
pip install pyinstaller

# Basic executable
pyinstaller --onefile main.py

# With game assets and data
pyinstaller --onefile --windowed \
    --add-data "entities:entities" \
    --add-data "scenes:scenes" \
    --add-data "rules:rules" \
    --add-data "assets:assets" \
    --name "MyGame" \
    main.py

# Result: dist/MyGame.exe (or MyGame on Mac/Linux)
```

### Nuitka (Faster, Smaller)

```bash
# Install
pip install nuitka

# Compile to standalone executable
nuitka --standalone --onefile \
    --include-data-dir=entities=entities \
    --include-data-dir=scenes=scenes \
    --include-data-dir=assets=assets \
    --output-filename=MyGame \
    main.py
```

### Comparison

| Tool | Output Size | Startup Time | Compile Time |
|------|-------------|--------------|--------------|
| PyInstaller | ~40-60MB | Slower | Fast |
| Nuitka | ~25-40MB | Faster | Slower |

## Distribution Checklist

```
my_game_release/
├── MyGame.exe           # Standalone executable
├── README.txt           # How to play
├── LICENSE.txt          # Your license
└── saves/               # Empty saves directory
```

Users double-click the executable — no Python installation required.

## Platform-Specific Notes

### Windows
- Use `--windowed` flag to hide console
- Sign executable for Windows SmartScreen

### macOS
- Creates `.app` bundle with PyInstaller
- May need to codesign for Gatekeeper

### Linux
- AppImage format recommended for distribution
- Use `--strip` flag for smaller binary

---

# Appendix A: Design Principles

## Core Principles

1. **Text over binary** — If it can be text, it must be text.

2. **Explicit over implicit** — State your intentions. Document your assumptions.

3. **Data over code** — Express logic as data where possible. Code is for computation.

4. **Flat over nested** — Avoid deep hierarchies. Prefer composition.

5. **Query over traverse** — Don't walk object graphs. Query for what you need.

6. **Convention over configuration** — Rigid conventions reduce decisions.

7. **Validate early** — Catch errors at load time, not runtime.

8. **Fail loudly** — Errors should explain themselves.

9. **Design for inspection** — Every system should be queryable.

10. **Assume your partner is an AI** — Write for reading, not just writing.

## AI-Native Principles

11. **JSON output first, human output second** — Every command must support `--json`. AI agents cannot reliably parse human-formatted output.

12. **Show patterns, not concepts** — Documentation should show copyable examples first, explanations second. AI agents pattern-match; they don't need conceptual preambles.

13. **Make impact visible** — Before any change, AI should be able to ask "what will this affect?" Impact analysis is a first-class feature.

14. **Enable experimentation** — Snapshot/rollback must be cheap and easy. AI agents learn by trying, evaluating, and undoing.

15. **Type everything** — Static type hints provide crucial context. AI agents use signatures to understand APIs.

16. **Intent fields are contracts** — The `intent` field isn't documentation; it's a testable specification. Implementation should be validated against intent.

17. **Structured errors with fixes** — Errors must include: what happened, why, and how to fix. AI agents cannot "poke around" like humans.

18. **Deterministic by default** — All randomness must be seeded. Simulations must be reproducible. AI agents need predictable environments.

19. **Context-window aware** — The framework should help AI agents manage limited context. Provide exactly the files needed, truncated intelligently.

20. **Prefer Python over DSLs** — AI agents already understand Python. Custom DSLs add learning burden without proportional benefit. Use Python first; add DSLs only when proven necessary.

## Anti-Patterns to Avoid

| Anti-Pattern | Why It Hurts AI | Better Approach |
|--------------|-----------------|-----------------|
| Binary formats | AI cannot read | Text formats (YAML, JSON) |
| GUI configuration | Not in code | Config files with schemas |
| Implicit state | Cannot query | Explicit state with introspection |
| Scattered logic | Hard to trace | Centralized systems |
| Human-only docs | Wastes context | Pattern-first documentation |
| Unstructured output | Cannot parse | JSON with consistent schemas |
| Deep inheritance | Hard to understand | Flat composition (ECS) |
| Hidden dependencies | Surprising failures | Explicit imports and refs |
| Magic strings | No validation | Typed enums and schemas |
| Undocumented conventions | Must guess | Explicit, enforced conventions |

---

# Appendix B: Glossary

## Core Concepts

| Term | Definition |
|------|------------|
| **Entity** | A unique ID representing a game object |
| **Component** | Data attached to an entity (Position, Health, etc.) |
| **System** | Logic that processes entities with specific components |
| **Event** | A record of something that happened |
| **Rule** | Logic that modifies actions or triggers effects (Python decorators) |
| **Scene** | A level or map definition |
| **Render Command** | Abstract instruction for displaying something |
| **Schema** | Type definition that can be validated and queried |
| **REPL** | Read-Eval-Print Loop for interactive exploration |

## AI-Native Concepts

| Term | Definition |
|------|------------|
| **Intent** | Natural language description of design goals; a testable contract |
| **Impact Analysis** | Analyzing what a proposed change will affect before making it |
| **What-If Simulation** | Testing hypothetical changes without committing them |
| **Snapshot** | A complete, serializable copy of game state for rollback |
| **Context Window** | The limited amount of text an AI agent can process at once |
| **Structured Output** | JSON-formatted responses that AI can reliably parse |
| **Intent Violation** | When implementation doesn't match stated design goals |
| **Pattern-First Docs** | Documentation that shows copyable examples before explanations |

## Implementation Terms

| Term | Definition |
|------|------------|
| **ECS** | Entity-Component-System architecture |
| **Event Sourcing** | Storing complete history of events, not just current state |
| **Deterministic Seed** | Fixed random seed for reproducible simulations |
| **Headless Mode** | Running without graphics for testing |
| **Type Hints** | Python annotations that describe expected types |

---

# Appendix C: Quick Reference

## Most-Used Commands

```bash
# Validate all files
ai_engine validate --json

# Check impact of a change
ai_engine impact "entity.field=value" --json

# Run combat simulation
ai_engine simulate combat --entity Goblin --vs Player --json

# Get context for a task
ai_engine context --task "add enemy" --max-tokens 4000

# Run tests
pytest tests/ -v

# Start REPL
ai_engine repl scenes/level_1.yaml --json
```

## File Locations

| What | Where |
|------|-------|
| Entity definitions | `entities/*.yaml` |
| Entity templates | `entities/_templates/*.yaml` |
| Component schemas | `schemas/components.yaml` |
| Event schemas | `schemas/events.yaml` |
| Game rules | `rules/*.yaml` (or `systems/*.py` for Python rules) |
| Scenes/levels | `scenes/*.yaml` |
| Tests | `tests/*.py` (pytest) |
| AI task prompts | `.ai/tasks/*.md` |
| Claude Code commands | `.claude/commands/*.md` |

## Priority Order for Implementation

1. Schema Registry + `--json` output
2. ECS World with typed components
3. Event Bus with history
4. Pygame renderer
5. Turn Manager
6. Python rule decorators
7. CLI validation
8. pytest integration
9. Impact analysis
10. Simulation commands
11. REPL + context generation
12. (Everything else as needed)

---

*This document is the source of truth for AI_ENGINE_NAME. When in doubt, refer here.*

---

## ---------- PENDING REFACTOR ----------

### Summary of Critique Discussion

Based on architectural review and discussion with AI coding agents (Claude Code + Indy), the following changes are recommended for the framework design.

### Action Items by Category

| Concern | Verdict | Action |
|---------|---------|--------|
| Intent field | Keep | This is genuinely innovative |
| Performance | Monitor | Use Pydantic at boundaries, dataclasses at runtime |
| YAML rules | Kill | Python decorators only, no custom DSL |
| Context command | Simplify | Keyword-based "starter kit" command, not semantic analysis |
| Impact analysis | Keep | Phase 3 as originally planned - important to retain |
| Spatial helpers | Add | Include in Phase A or B |
| Asset management | Add | Include in Phase B |
| Phase 1 scope | Keep | Reviewer misread - it's learning, not framework building |

### Key Changes Required

#### 1. MUST KILL: YAML Rule System
**Current Problem:** The document contradicts itself - Section 3.5 proposes YAML-based rules, Section 8 admits this is a trap, Appendix A warns against DSLs.

**Action Required:**
- Remove all references to YAML-based rule syntax (`when: "action.type == ..."`)
- Keep only Python decorator approach (`@rule`)
- **Rationale:** LLMs are trained on billions of lines of Python, almost zero lines of custom YAML DSLs. Python provides IDE support, debugging, type checking for free.

#### 2. MUST ADD: Spatial Reasoning Helpers
**Current Gap:** AI is bad at 2D grids, pathfinding, line-of-sight calculations.

**Action Required:**
- Add utility library for spatial operations:
  - `grid.get_tiles_in_range(entity, distance=3)`
  - `grid.get_path(from_pos, to_pos)`
  - `grid.has_line_of_sight(a, b)`
  - `grid.get_entities_in_cone(origin, direction, angle)`
- Include in Phase A or B

#### 3. MUST ADD: Asset Management System
**Current Gap:** Document hand-waves asset references ("Simple file references work").

**Action Required:**
- Generate asset manifest/registry
- Prefer constants over magic strings: `Assets.Sprites.GOBLIN_IDLE` vs `"goblin_idle"`
- Validate asset references at load time
- Include in Phase B

#### 4. MUST REFACTOR: Performance Architecture
**Current Risk:** Python + Pydantic + Event Sourcing + ECS can be slow for simulations.

**Action Required:**
- Use Pydantic only at boundaries (loading/saving)
- Convert to plain dataclasses for runtime
- Factory pattern: `schema_object.to_runtime()`
- **Rationale:** Validate once when loading, use fast Python objects at runtime

#### 5. MUST SIMPLIFY: Context Command
**Current Design:** Complex algorithmic relevance detection.

**New Approach:** Simple "starter kit" commands that concatenate relevant files.

**Action Required:**
```bash
# Instead of complex context prediction:
renee context add-enemy
# Just concatenates: template + schema + one example + validation command
# ~20 lines of code, not a complex subsystem
```

**Examples:**
- `renee context add-enemy` → returns enemy template + Combat schema + example enemy + validation command
- `renee context add-system` → returns system template + event schemas + example system
- `renee context modify-balance` → returns all entity stats + simulation command

**Rationale:** Keyword-based, predictable, simple. No AI-powered relevance detection needed.

#### 6. KEEP: Impact Analysis (Phase 3)
**Decision:** Retain impact analysis as originally planned in Phase 3.

**Rationale:** While AI agents can grep and navigate, structured impact analysis provides value by:
- Understanding semantic relationships (not just string matching)
- Tracking rule registry dependencies
- Validating intent preservation across changes
- Providing structured JSON output for agent consumption

**Keep as designed in original document.**

#### 7. MUST PRIORITIZE: Unique Value Features

**High Priority (Phase A/B):**
1. ✅ Schema registry + introspection (`renee schema show Combat --json`)
2. ✅ Simulation commands with JSON output (`renee simulate combat --iterations 100 --json`)
3. ✅ Intent validation system (check if implementation matches design goals)
4. ✅ Test runner integration with structured output
5. ✅ Spatial reasoning helpers (pathfinding, LOS, range queries)
6. ✅ Asset manifest system
7. ✅ Simple context "starter kit" commands

**Phase 3 (Keep as planned):**
1. ✅ Impact analysis with dependency tracking
2. ✅ Advanced validation

**Defer/Kill:**
1. 🔪 YAML rule DSL (use Python only)

### Design Principle Clarification

> **AI-Native doesn't mean "AI can use it"**
>
> **AI-Native means "AI can derive insights it couldn't get elsewhere"**

- **Bad:** Complex AI-powered context prediction (over-engineered)
- **Good:** Simple keyword-based context commands (`renee context add-enemy`)
- **Good:** Building `renee simulate` to run 1000 combat iterations with statistics
- **Good:** Intent validation that checks if code matches design goals

### Updated Priority Order for Implementation

1. Schema Registry + `--json` output *(keep)*
2. ECS World with typed components *(keep)*
3. Event Bus with history *(keep)*
4. Spatial reasoning utilities *(add)*
5. Asset manifest system *(add)*
6. Python rule decorators *(keep, remove YAML alternative)*
7. Simple context "starter kit" commands *(add, simplified approach)*
8. Pygame renderer *(keep)*
9. Turn Manager *(keep)*
10. Simulation commands with statistics *(keep, elevate priority)*
11. Intent validation system *(keep, elevate priority)*
12. CLI validation *(keep)*
13. pytest integration with JSON output *(keep)*
14. Impact analysis *(keep as Phase 3)*
15. REPL *(keep)*

### Next Steps

1. Create refined design document (renee-engine.md) incorporating these changes
2. Remove all YAML rule syntax examples
3. Add spatial reasoning helper specifications
4. Add asset management system design
5. Add simple context "starter kit" command examples
6. Update sysprmopt.md if needed based on renee-engine.md changes
