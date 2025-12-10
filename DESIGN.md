# Renee: An AI-Native Game Framework

## Design Document v2.0

---

# Executive Summary

**Renee** is a turn-based game framework designed from the ground up for AI-assisted development. Unlike traditional game engines that assume human developers reading documentation and clicking through GUIs, Renee assumes your co-developer is an AI coding agent like Claude Code or Cursor.

### What "AI-Native" Means

**AI-Native doesn't mean "AI can use it"**

**AI-Native means "AI can derive insights it couldn't get elsewhere"**

Traditional engines are hostile to AI agents:
- Binary formats AI can't read
- GUI-configured values not in code
- Implicit state scattered across files
- Documentation written for humans who can "explore"

Renee inverts this:
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
| **Testing** | pytest | Familiar to AI agents, no custom DSL needed |
| **Rendering** | pygame (primary) | Simple, well-documented, battle-tested |
| **Distribution** | pyinstaller, nuitka | Single executable output for easy sharing |

### Flagship Features

| Feature | What It Does | Why AI Loves It |
|---------|--------------|-----------------|
| **Schema Registry** | Runtime-queryable type definitions | AI asks "what fields does a Monster have?" and gets an answer |
| **Intent Fields** | Natural language descriptions on entities | AI compares implementation against stated goals |
| **`--json` on Everything** | Machine-parseable output from all commands | AI reliably parses structured responses |
| **Spatial Reasoning Helpers** | Grid utilities, pathfinding, LOS APIs | AI doesn't need to implement A* from scratch |
| **Asset Management** | Validated asset manifest with constants | `Assets.Sprites.GOBLIN` vs `"goblin"` magic strings |
| **Impact Analysis** | Shows change effects with intent validation | AI knows what breaks before making changes |
| **Simulation** | Test hypothetical changes with statistics | AI experiments with balance safely |
| **Snapshot/Rollback** | First-class state snapshots | AI tries, evaluates, undoes freely |
| **Context Commands** | Simple "starter kit" commands | AI gets templates + examples + validation commands |
| **REPL with JSON Mode** | Interactive game manipulation | AI experiments, observes, iterates |
| **Event Sourcing** | Complete history of everything that happened | AI debugs by reading the past |
| **Python Rule System** | Game logic as Python decorators, NOT DSL | AI writes rules in familiar Python |
| **Render Commands** | Abstract output, pluggable renderers | AI tests games without graphics |

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

## Document Map

This document (DESIGN.md) covers strategic architecture, design principles, and core systems. For implementation details, see:

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **[DESIGN.md](DESIGN.md)** | Strategic design & architecture | Understanding Renee's philosophy and core systems |
| **[CLI.md](CLI.md)** | Complete command reference | Looking up command syntax and options |
| **[RENDERING.md](RENDERING.md)** | Render command specification | Building custom renderers |
| **[TUTORIAL.md](TUTORIAL.md)** | Step-by-step game building guide | First time building a Renee game |
| **[PATTERNS.md](PATTERNS.md)** | Copyable patterns for AI agents | Adding entities, systems, rules, scenes |
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | Packaging & distribution guide | Shipping your game to players |

**Quick Start Path:**
1. Read DESIGN.md (this document) for architecture
2. Follow TUTORIAL.md to build your first game
3. Reference PATTERNS.md when adding new content
4. Use CLI.md as command reference
5. Consult DEPLOYMENT.md when ready to ship

---

# Part 1: Architecture Overview

## High-Level Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                     Game Definition (Text Files)                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Entities │ │ Systems  │ │  Scenes  │ │  Rules   │           │
│  │  (YAML)  │ │ (Python) │ │  (YAML)  │ │ (Python) │           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
└───────┼────────────┼────────────┼────────────┼─────────────────┘
        │            │            │            │
        ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Renee Runtime                            │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Schema    │  │    ECS      │  │    Event    │             │
│  │  Registry   │  │   World     │  │    Bus      │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │    Rule     │  │    Turn     │  │   Spatial   │             │
│  │   Engine    │  │   Manager   │  │   Helpers   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Asset     │  │   Replay    │  │    REPL     │             │
│  │  Registry   │  │   System    │  │  Interface  │             │
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

### 2. Entity Component System (ECS)

**Core Structure:**
- Entities are IDs (just numbers)
- Components are pure data attached to entities
- Systems are isolated logic that processes entities

**Entity Definition Format (YAML):**
```yaml
name: Goblin
description: "A weak but numerous enemy"
intent: |
  A basic melee enemy for early game encounters.
  - Should be defeatable by a starting player in 2-3 hits
  - Deals low but consistent damage
  - No special abilities, just basic attack
tags: [enemy, creature, melee, early_game]

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
    aggro_range: 5
```

**Why ECS Matters for AI:**
- Flat structure (no deep inheritance to trace)
- Components are readable data (not hidden in object state)
- Systems are isolated (modify one without understanding others)
- Easy to query: "give me all entities with Health and Combat"

### 3. Event Sourcing for Complete History

The game is a sequence of events, not mutable state.

```python
event_log = [
    {"turn": 1, "type": "game_started", "players": [1, 2]},
    {"turn": 1, "type": "action_move", "entity": 1, "from": [0,0], "to": [1,0]},
    {"turn": 1, "type": "damage_dealt", "target": 1, "amount": 5, "source": "trap"},
    {"turn": 1, "type": "turn_ended", "player": 1},
]
```

**Why This Matters for AI:**
- Complete history is always available
- Debugging = "find the event that caused bad state"
- Replay by re-processing events
- AI can ask "what happened on turn 5?"

### 4. Performance Architecture: Pydantic at Boundaries

**The Problem:** Pydantic validation on every entity operation is slow.

**The Solution:** Use Pydantic only at boundaries (loading/saving), convert to plain dataclasses for runtime.

```python
# Pydantic schema for validation (loading)
class HealthSchema(BaseModel):
    current: int
    max: int

    @field_validator('current')
    @classmethod
    def current_not_exceed_max(cls, v, info):
        if v > info.data.get('max', 0):
            raise ValueError('current cannot exceed max')

# Plain dataclass for runtime (fast)
@dataclass
class Health:
    current: int
    max: int

# Factory pattern: validate once, use fast object
def load_entity(yaml_path: str) -> Entity:
    data = yaml.load(yaml_path)
    schema = EntitySchema(**data)  # Validate with Pydantic
    return schema.to_runtime()      # Convert to fast dataclass
```

---

# Part 2: The Intent System (Key Innovation)

## Why Intent Fields Matter

LLMs struggle with "grounding" — connecting high-level concepts ("make it hard") to low-level integers (`hp: 500`).

The `intent` field treats design goals as testable contracts.

## Entity Intent Example

```yaml
name: Dragon
description: "Final boss of Act 1"
intent: |
  Epic boss fight that tests everything the player has learned.

  Phase 1 (100%-60% HP):
  - Moderate damage, predictable attacks
  - Teaches players the basic pattern

  Phase 2 (60%-30% HP):
  - Enters "rage mode" - higher damage, lower defense
  - Introduces area-of-effect attacks
  - Creates risk/reward: burst damage vs. survival

  Phase 3 (30%-0% HP):
  - Desperate attacks, very high damage
  - Summons minions as distractions
  - Players must decide: kill minions or focus boss?

  Win rate target: 60-70% for prepared players
  Average time to kill: 8-12 turns

components:
  Health:
    current: 300
    max: 300
  Combat:
    attack: 25
    defense: 10
```

## How AI Uses Intent

When asked "the dragon feels too easy", AI can:
1. Read the intent: "Win rate target: 60-70%"
2. Run simulation: `renee simulate combat --attacker Player --defender Dragon --iterations 1000`
3. Get actual win rate: 85%
4. Identify mismatch and suggest adjustments

**Without intent:** AI must guess what "too easy" means.
**With intent:** AI has explicit design goals to validate against.

## Intent Validation in Impact Analysis

```bash
$ renee impact "dragon.Combat.attack=35" --json
```

```json
{
  "change": "dragon.Combat.attack=35",
  "intent_violations": [
    {
      "entity": "Dragon",
      "intent": "Win rate target: 60-70% for prepared players",
      "simulation_result": "Win rate drops to 42% with attack=35",
      "suggestion": "This makes the boss too hard. Consider attack=28-30 instead."
    }
  ],
  "affected_tests": ["tests/test_dragon_fight.py"],
  "affected_systems": ["systems/combat.py"]
}
```

---

# Part 3: Core Systems

## Schema Registry

Runtime-queryable type definitions that allow the framework to describe itself.

### Schema Definition Format

```yaml
# schemas/components.yaml
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
  description: "Offensive and defensive stats"
  fields:
    attack:
      type: integer
      min: 0
      description: "Base damage per attack"
    defense:
      type: integer
      min: 0
      description: "Damage reduction"
    crit_chance:
      type: float
      min: 0.0
      max: 1.0
      default: 0.0
      description: "Probability of critical hit"
```

### Runtime Introspection API

```python
from renee import schema

# Get schema for a component type
health_schema = schema.get("Health")

# List all registered schemas
all_components = schema.list(type="component")

# Validate data against schema
is_valid, errors = schema.validate("Health", {"current": 50, "max": 100})

# Get default values
defaults = schema.defaults("Combat")
```

### CLI Access

```bash
$ renee schema list
$ renee schema show Health --json
$ renee schema validate entities/goblin.yaml --json
```

**Why This Matters:**
AI asks "what fields does a Monster have?" and gets an answer. No guessing, no documentation searching.

---

## ECS World

### ECS Runtime API

```python
from renee import World

# Create world
world = World()

# Spawn entities from templates
goblin_id = world.spawn("Goblin", position={"x": 5, "y": 3})

# Get component data
health = world.get(goblin_id, "Health")
print(health.current)  # 20

# Modify components
world.set(goblin_id, "Health", Health(current=15, max=20))

# Query by components/tags
enemies = world.query(has=["AI", "Combat"], tags=["enemy"])

# Iterate over query results
for entity_id in enemies:
    combat = world.get(entity_id, "Combat")
    print(f"Enemy {entity_id} has {combat.attack} attack")
```

### Snapshot/Rollback (First-Class Feature)

```python
# Save current state
snapshot = world.snapshot()

# Try something risky
world.do_action("attack", source=player_id, target=boss_id)

# Check result
player_health = world.get(player_id, "Health").current

# Undo if it went badly
if player_health < 20:
    world.restore(snapshot)
```

**Why This Matters:**
AI can experiment freely. Try an approach, see if it works, roll back if not.

### Static Type Hints (Critical for AI)

```python
from dataclasses import dataclass
from typing import Type, TypeVar

T = TypeVar('T')

@dataclass
class Health:
    current: int
    max: int

class World:
    def get(self, entity: EntityId, component_type: Type[T]) -> T:
        """Get a component from an entity."""
        ...

    def query(self, has: list[str], tags: list[str] = None) -> list[EntityId]:
        """Query entities by components and tags."""
        ...
```

AI agents can read type signatures and understand what functions expect.

---

## Event Bus

### Event Definition Schema

```yaml
# schemas/events.yaml
damage_dealt:
  description: "An entity took damage"
  fields:
    target: {type: entity_id, required: true}
    amount: {type: integer, required: true}
    source: {type: entity_id}
    damage_type: {type: string, default: "physical"}

entity_died:
  description: "An entity's health reached 0"
  fields:
    entity: {type: entity_id, required: true}
    killer: {type: entity_id}
```

### Event Bus API

```python
from renee import events

# Subscribe to events
@events.on("damage_dealt")
def log_damage(event):
    print(f"Entity {event.target} took {event.amount} damage")

# Emit events
events.emit("damage_dealt", {
    "target": goblin_id,
    "amount": 15,
    "source": player_id,
    "damage_type": "fire"
})

# Query event history
recent_damage = events.history(type="damage_dealt", last=10)
turn_5_events = events.history(turn=5)
```

---

## Spatial Reasoning Helpers

AI is bad at 2D grids, pathfinding, and spatial calculations. Provide utilities.

### Grid API

```python
from renee.spatial import Grid

# Create grid
grid = Grid(width=20, height=15)

# Mark obstacles
grid.set_blocked(x=5, y=3)

# Pathfinding
path = grid.get_path(from_pos=(0, 0), to_pos=(10, 10))
# Returns: [(0,0), (1,0), (2,1), (3,2), ...]

# Line of sight
has_los = grid.has_line_of_sight(from_pos=(0, 0), to_pos=(10, 10))

# Range queries
tiles_in_range = grid.get_tiles_in_range(center=(5, 5), distance=3)

# Cone/area queries
tiles_in_cone = grid.get_tiles_in_cone(
    origin=(5, 5),
    direction="north",
    angle=45,
    distance=5
)

# Get entities at position
entities = grid.get_entities_at(x=5, y=3)
```

**Why This Matters:**
Don't make AI implement A* from scratch. It will get it wrong. Provide battle-tested utilities.

---

## Asset Management System

### The Problem: Magic Strings

```python
# BAD: AI has to guess valid asset names
sprite = "goblin_idle"  # Typo: should be "goblin_idle_1"?
sound = "hit_sound"     # Does this file exist?
```

### The Solution: Asset Manifest

```python
# assets/manifest.yaml (auto-generated)
sprites:
  - goblin_idle
  - goblin_walk_1
  - goblin_walk_2
  - knight_idle

sounds:
  - sword_hit
  - fireball_cast
  - enemy_death
```

```python
# Generated: renee/assets.py
class Sprites:
    GOBLIN_IDLE = "goblin_idle"
    GOBLIN_WALK_1 = "goblin_walk_1"
    GOBLIN_WALK_2 = "goblin_walk_2"
    KNIGHT_IDLE = "knight_idle"

class Sounds:
    SWORD_HIT = "sword_hit"
    FIREBALL_CAST = "fireball_cast"
    ENEMY_DEATH = "enemy_death"

class Assets:
    Sprites = Sprites
    Sounds = Sounds
```

### Usage

```python
from renee.assets import Assets

# GOOD: Type-safe, validated, autocomplete-friendly
sprite = Assets.Sprites.GOBLIN_IDLE
sound = Assets.Sounds.SWORD_HIT
```

### CLI Commands

```bash
# Regenerate asset manifest
$ renee assets scan

# Validate asset references in entities
$ renee assets validate --json
```

**Why This Matters:**
AI doesn't have to guess. Constants are validated. IDEs provide autocomplete.

---

## Python Rule System (No YAML DSL)

### Core Design Decision

Rules are Python functions with decorators, **NOT custom YAML DSL**.

### Python Decorator Approach

```python
from renee.rules import rule

@rule
def flanking_bonus(ctx):
    """Apply +2 damage when attacking with allies nearby."""
    if ctx.action.type == "melee_attack":
        allies_near_target = ctx.world.query(
            has=["Position"],
            tags=["ally"]
        )
        adjacent = [
            e for e in allies_near_target
            if ctx.grid.distance(e, ctx.action.target) == 1
        ]

        if len(adjacent) >= 1:
            ctx.action.damage += 2

@rule(when=lambda ctx: ctx.action.type == "melee_attack")
def apply_backstab(ctx):
    """Apply 1.5x damage when attacking from behind."""
    if ctx.grid.is_behind(ctx.action.source, ctx.action.target):
        ctx.action.damage *= 1.5
```

### Rationale

- AI agents are trained on billions of lines of Python
- Almost zero training on custom YAML DSLs
- Python provides IDE support, debugging, type checking for free
- No need to build expression parser, AST evaluator, function registry

### What NOT to Do

```yaml
# DON'T DO THIS - requires custom DSL parser
rules:
  flanking_bonus:
    when: "action.type == 'melee_attack'"
    condition: "count(allies_adjacent_to(action.target)) >= 1"
    effect:
      - modify: "action.damage"
        add: 2
```

This is harder for AI, harder to debug, and requires building a custom parser.

---

# Part 4: AI-Native Tooling

## CLI Design Principles

1. **Every command has `--json` flag**
2. **Structured output, not prose**
3. **Exit codes: 0 = success, 1 = error**
4. **Predictable output format**

### Example: Schema Introspection

```bash
$ renee schema show Health --json
```

```json
{
  "name": "Health",
  "description": "Entity's health pool",
  "fields": {
    "current": {
      "type": "integer",
      "min": 0,
      "description": "Current health points"
    },
    "max": {
      "type": "integer",
      "min": 1,
      "description": "Maximum health points"
    }
  },
  "required": ["current", "max"],
  "invariants": ["current <= max"]
}
```

---

## Context Commands (Simplified)

Instead of complex AI-powered context prediction, provide simple "starter kit" commands.

### Design

```bash
# Get template + schema + example + validation command
$ renee context add-enemy
```

**Output:**
```
# Enemy Template
# Copy entities/_templates/basic_enemy.yaml and modify

# Relevant Schema
# schemas/components.yaml (Combat, Health, AI sections)

# Example Enemy
# entities/goblin.yaml

# Validation Command
renee validate entities/your_enemy.yaml --json
```

### Available Commands

```bash
renee context add-enemy      # Enemy template + Combat/AI schemas + example
renee context add-system     # System template + event schemas + example
renee context modify-balance # All entity stats + simulation command
renee context add-ability    # Ability template + rule examples
```

**Rationale:**
Keyword-based, predictable, simple. ~20 lines of code per command, not a complex subsystem.

---

## Impact Analysis (Phase 3)

Shows what breaks when you make a change, with intent validation.

### Usage

```bash
$ renee impact "goblin.Combat.attack=15" --json
```

### Output

```json
{
  "change": "goblin.Combat.attack=15",
  "affected_files": [
    "tests/test_goblin_combat.py",
    "scenes/level_1.yaml",
    "scenes/level_2.yaml"
  ],
  "affected_rules": [
    "systems/combat.py:flanking_bonus"
  ],
  "intent_violations": [
    {
      "entity": "Goblin",
      "intent": "defeatable in 2-3 hits by starting player",
      "actual": "now requires 4 hits (player attack=12, goblin health=20, new defense with attack=15)",
      "suggestion": "Reduce Health.max from 20 to 18 to maintain 2-3 hit intent"
    }
  ],
  "simulation_result": {
    "player_vs_goblin_win_rate": "95% -> 78%",
    "avg_turns_to_kill": "2.1 -> 3.4"
  }
}
```

**Why This Matters:**
AI knows what breaks *before* making changes. Intent validation ensures changes align with design goals.

---

## Simulation Commands

Test hypothetical changes with statistical analysis.

### Single Matchup Simulation

```bash
$ renee simulate combat \
    --attacker Player \
    --defender Goblin \
    --iterations 1000 \
    --json
```

```json
{
  "matchup": "Player vs Goblin",
  "iterations": 1000,
  "results": {
    "player_wins": 876,
    "goblin_wins": 124,
    "win_rate": 0.876,
    "avg_turns": 2.3,
    "avg_player_health_remaining": 68.5
  }
}
```

### What-If Analysis

```bash
$ renee simulate what-if \
    --change "goblin.Combat.attack=15" \
    --matchup "Player vs Goblin" \
    --iterations 1000 \
    --json
```

```json
{
  "change": "goblin.Combat.attack=15",
  "baseline": {
    "win_rate": 0.876,
    "avg_turns": 2.3
  },
  "modified": {
    "win_rate": 0.742,
    "avg_turns": 3.1
  },
  "delta": {
    "win_rate": -0.134,
    "avg_turns": +0.8
  }
}
```

### Parameter Sweep

```bash
$ renee simulate sweep \
    --entity Goblin \
    --field Combat.attack \
    --range 5,10,15,20,25 \
    --iterations 500 \
    --json
```

**Why This Matters:**
AI can experiment with balance safely. "What if I increase attack by 5?" gets a numerical answer.

---

## REPL Interface

Interactive game manipulation for AI experimentation.

### Standard Mode

```bash
$ renee repl scenes/level_1.yaml

Renee REPL v1.0
Type 'help' for commands

> inspect player
Entity: player
Components:
  Health: {current: 100, max: 100}
  Combat: {attack: 12, defense: 5}
  Position: {x: 0, y: 0}

> query entities where tags contains "enemy"
Found 3 entities:
  - goblin_1 (tags: enemy, creature)
  - goblin_2 (tags: enemy, creature)
  - skeleton_1 (tags: enemy, undead)

> set goblin_1 Health.current 5
Updated goblin_1.Health.current = 5

> do attack player goblin_1
Action executed: attack
  - goblin_1 took 7 damage (12 attack - 5 defense)
  - goblin_1 died

> snapshot save before_fight
Snapshot saved: before_fight

> snapshot restore before_fight
Snapshot restored: before_fight
```

### JSON Mode (for AI)

```bash
$ renee repl --format json scenes/level_1.yaml

> {"command": "query", "query": "entities where Health.current < Health.max"}
{"result": [{"id": 2, "name": "Goblin", "Health": {"current": 15, "max": 20}}]}

> {"command": "inspect", "entity": 2}
{"result": {"entity": 2, "components": {"Health": {"current": 15, "max": 20}, "Combat": {"attack": 8}}}}
```

**Why This Matters:**
AI can experiment interactively, see results immediately, iterate quickly.

---

# Part 5: File Structure

## Directory Layout

```
my_game/
├── game.yaml                    # Project manifest
├── schemas/                     # Type definitions
│   ├── components.yaml
│   ├── events.yaml
│   └── actions.yaml
├── entities/                    # Entity templates
│   ├── _templates/              # Canonical examples for AI
│   │   ├── basic_enemy.yaml
│   │   ├── ranged_enemy.yaml
│   │   ├── boss.yaml
│   │   ├── collectible.yaml
│   │   └── npc.yaml
│   ├── player.yaml
│   ├── goblin.yaml
│   ├── skeleton.yaml
│   └── dragon.yaml
├── systems/                     # Game logic (Python)
│   ├── combat.py
│   ├── movement.py
│   └── inventory.py
├── rules/                       # Rules (Python decorators)
│   ├── combat_modifiers.py
│   └── tile_effects.py
├── scenes/                      # Level/map definitions
│   ├── level_1.yaml
│   ├── level_2.yaml
│   └── boss_arena.yaml
├── assets/                      # Game assets
│   ├── sprites/
│   ├── sounds/
│   ├── fonts/
│   └── manifest.yaml            # Auto-generated asset registry
├── tests/                       # pytest tests
│   ├── test_combat.py
│   ├── test_movement.py
│   └── test_balance.py
└── docs/                        # Documentation
    ├── ARCHITECTURE.md
    └── PATTERNS.md
```

## File Naming Conventions

- `*.yaml` - Data definition
- `*.py` - Logic/behavior
- `_templates/` - Canonical examples for AI to copy
- `_` prefix - Internal/private

**Why Rigid Conventions Matter:**
AI agents pattern-match. "To add a monster, create a file in `entities/`" works because the convention is absolute.

## Template Directory Pattern

```
entities/_templates/
├── basic_enemy.yaml      # Copy for simple enemies
├── ranged_enemy.yaml     # Copy for archers, mages
├── boss.yaml             # Copy for boss fights
├── collectible.yaml      # Copy for items
└── npc.yaml              # Copy for friendly NPCs
```

Each template has TODO markers for AI to fill in:

```yaml
name: TODO_ENEMY_NAME  # TODO: Change this
description: "TODO: Describe this enemy"
intent: |
  TODO: Describe what this enemy should do and feel like.
  - How hard should it be?
  - What's its role in the game?
  - What's the player experience?

tags: [enemy, TODO_ADD_TAGS]

components:
  Health:
    current: 20  # TODO: Adjust
    max: 20
  Combat:
    attack: 8    # TODO: Adjust
    defense: 2   # TODO: Adjust
```

---

# Part 6: Implementation Roadmap

## Critical Principle: Working > Complete

A working game with 4 core systems beats a half-implemented framework with 12 systems.

## Phase 1: Minimum Viable Framework (Weeks 1-4)

**Goal:** A playable turn-based game that AI agents can read and modify.

**Priority Systems:**

1. **Schema Registry** (CRITICAL)
   - YAML schema definitions with validation
   - Runtime introspection API
   - `--json` output from day 1

2. **ECS World** (CRITICAL)
   - Entity spawning from YAML templates
   - Component attachment and querying
   - Simple query methods

3. **Event Bus** (CRITICAL)
   - Emit/subscribe pattern
   - Event history storage
   - Query history by turn/type

4. **YAML Loaders** (CRITICAL)
   - Load entities from `entities/*.yaml`
   - Load scenes from `scenes/*.yaml`

5. **Spatial Reasoning Helpers** (HIGH)
   - Grid utilities
   - Pathfinding (A*)
   - Line of sight
   - Range/cone queries

6. **Asset Management** (HIGH)
   - Asset manifest generation
   - Constants for asset references
   - Validation

7. **Pygame Renderer** (HIGH)
   - Single renderer (not three)
   - Render command consumption
   - Basic input handling

**Deliverable:** `renee run` produces a playable prototype

---

## Phase 2: Make It Testable (Weeks 5-8)

**Goal:** AI agents can verify their changes work correctly.

**Priority Systems:**

1. **Turn Manager** (HIGH)
   - Phase-based turn structure
   - Action validation

2. **Python Rule Engine** (HIGH)
   - Rules as Python functions with decorators
   - Rule registration and execution
   - Context object for rule execution

3. **CLI Validation** (HIGH)
   - `renee validate` with `--json` output
   - Schema validation for all files

4. **pytest Integration** (HIGH)
   - Python test fixtures for game state
   - NOT custom `.test.yaml` DSL

5. **Simple Context Commands** (MEDIUM)
   - `renee context add-enemy`
   - `renee context add-system`
   - Template + schema + example bundling

**Deliverable:** `pytest tests/ -v` validates game logic

---

## Phase 3: AI-Native Tooling (Weeks 9-12)

**Goal:** AI agents can understand impact of changes and experiment safely.

**Priority Systems:**

1. **Structured JSON Output** (CRITICAL)
   - `--json` flag on EVERY command

2. **Impact Analysis** (HIGH)
   - Shows affected rules, scenes, tests
   - Intent violation detection
   - Semantic understanding of dependencies

3. **Snapshot/Rollback** (HIGH)
   - First-class API for AI experimentation
   - REPL integration

4. **Intent Validation** (HIGH)
   - Parse `intent` fields
   - Compare implementation against stated goals
   - Suggest corrections

5. **Simulation Commands** (HIGH)
   - Combat simulations
   - Win rate analysis
   - What-if scenarios
   - Parameter sweeps

**Deliverable:** `renee impact "goblin.Combat.attack=15" --json` shows comprehensive change analysis

---

## Phase 4: Developer Experience (Weeks 13-16)

**Goal:** Smooth development workflow.

**Priority Systems:**

1. **REPL Interface** (MEDIUM)
   - Interactive game manipulation
   - JSON mode for AI agents

2. **Headless Renderer** (MEDIUM)
   - For automated testing
   - No pygame dependency

3. **State Manager** (MEDIUM)
   - Global/scene/entity state separation
   - Persistence to JSON

4. **Replay System** (MEDIUM)
   - Record full game sessions
   - Deterministic replay
   - Debugging tool

**Deliverable:** Full development workflow from idea to tested feature

---

## Phase 5: Advanced Features (Weeks 17+)

**Goal:** Polish and power features. Only build what's actually needed.

**Low Priority (Build Only If Needed):**
- Additional renderers (terminal, web)
- Hot-reload system
- Visual level editor
- Networking/multiplayer (likely never)

**What NOT to Build (Deferred Indefinitely):**
- Custom YAML rule DSL (Python works fine)
- SQL-like query DSL (method chaining is sufficient)
- Custom test DSL (pytest works fine)

---

# Part 7: Key Innovations Summary

1. **Intent Fields** - Natural language design goals that AI can validate against
2. **Python Decorators for Rules** - No custom DSL, use Python directly
3. **Snapshot/Rollback as First-Class** - AI experimentation is core, not afterthought
4. **Schema Registry** - Framework describes itself to AI
5. **`--json` on Everything** - Structured output for AI parsing
6. **Spatial Reasoning Helpers** - Don't make AI implement A* from scratch
7. **Asset Management** - Constants over magic strings
8. **Impact Analysis with Intent** - Know what breaks AND why
9. **Simple Context Commands** - Starter kits, not AI-powered prediction
10. **Template Directory Pattern** - Canonical examples for AI to copy

---

# Part 8: Testing and Simulation

## pytest Integration (Not Custom DSL)

```python
import pytest
from renee import World

@pytest.fixture
def arena():
    world = World()
    world.spawn("Player", id="player", position={"x": 0, "y": 0})
    world.spawn("Goblin", id="goblin", position={"x": 1, "y": 0})
    return world

def test_basic_attack_damage(arena):
    player = arena.get_entity("player")
    goblin = arena.get_entity("goblin")

    initial_health = arena.get(goblin, "Health").current
    arena.do_action("attack", source=player, target=goblin)
    final_health = arena.get(goblin, "Health").current

    player_attack = arena.get(player, "Combat").attack
    goblin_defense = arena.get(goblin, "Combat").defense
    expected_damage = player_attack - goblin_defense

    assert initial_health - final_health == expected_damage
```

## Deterministic Seeding

All randomness goes through framework's RNG for reproducibility:

```python
from renee import rng

# Set seed for reproducible tests
rng.seed(12345)

# Use framework RNG (NOT random.randint())
damage = rng.randint(5, 10)
crit = rng.random() < 0.15
```

**Why This Matters:**
Tests are deterministic. AI can reproduce bugs reliably.

---

# Part 9: Design Principles

## 1. Everything is Text

- No binary formats
- YAML for data, Python for logic
- JSON for state export
- AI can read, modify, understand everything

## 2. Everything is Introspectable

```python
# Framework can describe itself
schema.list()
schema.get("Health")
world.query(has=["Combat"])
events.history(turn=5)
```

## 3. Everything is Declarative

```yaml
# Describe WHAT, not HOW
name: Goblin
components:
  Health: {current: 20, max: 20}
  Combat: {attack: 8}
```

## 4. Everything is Predictable

- Rigid file naming conventions
- Consistent directory structure
- Explicit patterns (templates with TODOs)
- No "magic" behavior

## 5. Provide Unique Insights

Build features that give AI insights it can't derive on its own:
- ✅ Simulation (run 1000 combats, get win rate)
- ✅ Intent validation (check implementation matches goals)
- ✅ Schema introspection (query component fields)
- ❌ Context prediction (AI can grep)
- ❌ Semantic code understanding (AI can read)

## 6. Literate Error Messages

Every error explains **what**, **why**, and **how to fix**:

```
Error: Action 'attack' failed

What happened:
  Player (id: 1) attempted to attack Goblin (id: 3)

Why it failed:
  Target out of range (distance: 5, max range: 1)

How to fix:
  Option 1: Move closer to target
    Valid positions: [(6,3), (7,2), (7,4)]

  Option 2: Attack a different target
    Entities in range: [Skeleton (id: 2) at (3,3)]
```

AI agents can parse structured errors and take corrective action without guessing.

---

# Appendix A: What NOT to Build

## Avoid These Traps

### 1. Custom YAML Rule DSL

**Don't:**
```yaml
rules:
  - when: "count(allies_near(target)) >= 1"
    then: "damage += 2"
```

**Do:**
```python
@rule
def flanking_bonus(ctx):
    if len(ctx.grid.get_allies_near(ctx.target)) >= 1:
        ctx.damage += 2
```

### 2. Custom Test DSL

**Don't:**
```yaml
tests:
  - name: "Goblin dies in 2-3 hits"
    given:
      - spawn Player
      - spawn Goblin
    when:
      - player attacks goblin
    then:
      - goblin.health < goblin.max_health
```

**Do:**
```python
def test_goblin_dies_in_2_3_hits(arena):
    # Use pytest, which AI already knows
    assert True
```

### 3. Complex AI-Powered Context Prediction

**Don't:** Build a system that tries to predict which files are relevant using embeddings/vector search.

**Do:** Simple keyword-based commands: `renee context add-enemy`

### 4. Over-Engineering Impact Analysis

**Don't:** Build full static analysis with AST parsing and type inference.

**Do:** Start with structured grep + schema awareness + simulation.

---

# Appendix B: Technology Choices Explained

## Why Python?

1. Largest training corpus for LLMs
2. AI agents are extremely fluent in Python
3. Rich ecosystem (pygame, pytest, pydantic)
4. Strong typing available (dataclasses, type hints)

## Why Pydantic?

1. Runtime schema validation
2. Automatic JSON serialization
3. Clear error messages
4. AI-friendly (widely used in training data)

**But:** Only use at boundaries. Convert to dataclasses for runtime performance.

## Why YAML for Data?

1. Human and AI readable
2. No executable code (safer than Python data files)
3. Clean syntax for nested data
4. Comments for documentation

## Why pytest?

1. AI agents already know it
2. No custom DSL to learn
3. Excellent tooling
4. JSON output support (`pytest --json-report`)

## Why Pygame?

1. Simple, well-documented
2. Pure Python (no compilation)
3. Battle-tested
4. AI training corpus includes many pygame examples

---

# Appendix C: CLI Command Reference

All commands support `--json` flag for structured output.

```bash
# Schema operations
renee schema list
renee schema show <component>
renee schema validate <file>

# Validation
renee validate <file>
renee validate --all

# Asset management
renee assets scan
renee assets validate

# Context helpers
renee context add-enemy
renee context add-system
renee context modify-balance
renee context add-ability

# Impact analysis
renee impact "<change>"

# Simulation
renee simulate combat --attacker <A> --defender <B> --iterations <N>
renee simulate what-if --change "<change>" --matchup "<matchup>" --iterations <N>
renee simulate sweep --entity <E> --field <F> --range <values> --iterations <N>

# Running the game
renee run <scene>
renee run <scene> --headless

# REPL
renee repl <scene>
renee repl <scene> --format json

# Testing
renee test
renee test --json
```

---

# Appendix D: Complete Example

Here's a complete example showing the full flow from entity definition to testing:

## 1. Define Entity

```yaml
# entities/skeleton.yaml
name: Skeleton
description: "An undead warrior risen from the grave"
intent: |
  Mid-tier enemy for dungeon areas.
  - Tougher than goblins (3-4 hits to defeat)
  - Deals moderate damage
  - Immune to poison
  - Drops bones (crafting material)

tags: [enemy, undead, melee, mid_game]

components:
  Position: {}

  Health:
    current: 35
    max: 35

  Combat:
    attack: 14
    defense: 4
    attack_range: 1

  Resistances:
    poison: 1.0  # Immune
    fire: 0.5    # Weak to fire

  AI:
    behavior: aggressive
    detection_range: 6

  Sprite:
    idle: skeleton_idle
    walk: skeleton_walk
    attack: skeleton_attack

on_death:
  - emit: {event: "enemy_killed", data: {type: "skeleton", xp: 25}}
  - chance: 0.7
    spawn: {type: "Bone", at: "self.position"}
```

## 2. Validate

```bash
$ renee validate entities/skeleton.yaml --json
{
  "passed": true,
  "file": "entities/skeleton.yaml",
  "errors": []
}
```

## 3. Check Balance

```bash
$ renee simulate combat --attacker Player --defender Skeleton --iterations 1000 --json
{
  "matchup": "Player vs Skeleton",
  "iterations": 1000,
  "results": {
    "player_wins": 782,
    "skeleton_wins": 218,
    "win_rate": 0.782,
    "avg_turns": 3.4,
    "avg_player_health_remaining": 42.3
  }
}
```

## 4. Verify Intent

```bash
$ renee impact "skeleton.Combat.attack=20" --json
{
  "change": "skeleton.Combat.attack=20",
  "intent_violations": [
    {
      "entity": "Skeleton",
      "intent": "Tougher than goblins (3-4 hits to defeat)",
      "current": "Player defeats skeleton in 3.4 hits",
      "with_change": "Player defeats skeleton in 3.4 hits",
      "status": "OK - still within intent range"
    }
  ],
  "simulation_result": {
    "player_vs_skeleton_win_rate": "78.2% -> 68.5%"
  }
}
```

## 5. Write Test

```python
# tests/test_skeleton.py
import pytest
from renee import World

@pytest.fixture
def combat_arena():
    world = World()
    world.spawn("Player", id="player", position={"x": 0, "y": 0})
    world.spawn("Skeleton", id="skeleton", position={"x": 1, "y": 0})
    return world

def test_skeleton_takes_3_to_4_hits(combat_arena):
    """Verify skeleton intent: 'Tougher than goblins (3-4 hits to defeat)'"""
    player = combat_arena.get_entity("player")
    skeleton = combat_arena.get_entity("skeleton")

    player_attack = combat_arena.get(player, "Combat").attack
    skeleton_health = combat_arena.get(skeleton, "Health").max
    skeleton_defense = combat_arena.get(skeleton, "Combat").defense

    damage_per_hit = player_attack - skeleton_defense  # 12 - 4 = 8
    hits_to_kill = skeleton_health / damage_per_hit     # 35 / 8 = 4.375

    # Should take 4-5 hits (rounds up from 4.375)
    assert 3 <= hits_to_kill <= 5, f"Expected 3-5 hits, got {hits_to_kill}"

def test_skeleton_fire_weakness(combat_arena):
    """Verify skeleton has 0.5 resistance to fire (takes 2x damage)"""
    skeleton = combat_arena.get_entity("skeleton")
    resistances = combat_arena.get(skeleton, "Resistances")

    assert resistances.fire == 0.5, "Skeleton should be weak to fire"

def test_skeleton_poison_immunity(combat_arena):
    """Verify skeleton is immune to poison"""
    skeleton = combat_arena.get_entity("skeleton")
    resistances = combat_arena.get(skeleton, "Resistances")

    assert resistances.poison == 1.0, "Skeleton should be immune to poison"
```

## 6. Run Tests

```bash
$ renee test tests/test_skeleton.py -v
tests/test_skeleton.py::test_skeleton_takes_3_to_4_hits PASSED
tests/test_skeleton.py::test_skeleton_fire_weakness PASSED
tests/test_skeleton.py::test_skeleton_poison_immunity PASSED

3 passed in 0.12s
```

## Complete Flow Summary

1. **Define** entity with intent field
2. **Validate** schema compliance
3. **Simulate** to verify balance
4. **Check impact** of changes against intent
5. **Write tests** that verify intent goals
6. **Run tests** to confirm implementation

This is the Renee development cycle: intent-driven, validated, testable.

---

*This document is the source of truth for Renee. When in doubt, refer here.*
