# Renee Framework Development Roadmap

> **Audience**: Engine developers building the Renee framework itself.
>
> **Philosophy**: Working > Complete. A minimal engine that runs one game beats a half-implemented engine that runs nothing.

---

## What We're Building

Renee is a **framework/engine** for turn-based games. This roadmap covers building the engine itself, not games made with it.

```
┌─────────────────────────────────────────────────────────────────┐
│                    WHAT WE'RE BUILDING                          │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                   Renee Framework                          │ │
│  │                                                           │ │
│  │  • Schema system (define component types)                 │ │
│  │  • ECS runtime (entities, components, queries)            │ │
│  │  • Event bus (emit, subscribe, history)                   │ │
│  │  • Action pipeline (request → rules → execute → events)   │ │
│  │  • Turn manager (flexible time structure)                 │ │
│  │  • Spatial utilities (grid, pathfinding, LOS)             │ │
│  │  • YAML loaders (parse game content)                      │ │
│  │  • Render command output (abstract, renderer-agnostic)    │ │
│  │  • CLI tools (validate, simulate, repl, run)              │ │
│  │                                                           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Games Built WITH Renee                        │ │
│  │                                                           │ │
│  │  • Strategy game (territory control)                      │ │
│  │  • Card game (deck builder)                               │ │
│  │  • Tactics RPG                                            │ │
│  │  • Board game (Catan-style)                               │ │
│  │  • etc.                                                   │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase Overview

| Phase | Focus | Deliverable |
|-------|-------|-------------|
| **Phase 0** | Project Setup | Repo structure, dev environment, CI |
| **Phase 1** | Data Layer | Schema system, ECS, Event bus |
| **Phase 2** | Logic Layer | Actions, Rules, Turn management |
| **Phase 3** | I/O Layer | YAML loading, Rendering, Input |
| **Phase 4** | CLI & Tooling | Commands, REPL, Validation |
| **Phase 5** | AI-Native Features | Impact analysis, Simulation, Context |
| **Phase 6** | Integration & Testing | Example game, Documentation, Polish |

---

## Phase 0: Project Setup

**Goal**: Development environment ready for engine work.

### 0.1 Repository Structure

```
renee/
├── src/
│   └── renee/
│       ├── __init__.py
│       ├── schema/          # Schema registry
│       ├── ecs/             # Entity-Component-System
│       ├── events/          # Event bus
│       ├── actions/         # Action pipeline
│       ├── rules/           # Rule engine
│       ├── turns/           # Turn management
│       ├── spatial/         # Grid, pathfinding, LOS
│       ├── loaders/         # YAML parsing
│       ├── rendering/       # Render commands, base renderer
│       ├── cli/             # CLI commands
│       ├── repl/            # Interactive REPL
│       └── types/           # Semantic types (EntityId, etc.)
├── tests/
│   └── ...                  # Mirror of src/ structure
├── examples/
│   └── example_game/        # Example game for testing
├── docs/
│   └── ...                  # Generated API docs
├── pyproject.toml
├── README.md
├── DESIGN.md
├── ROADMAP.md
└── ...
```

### 0.2 Development Environment

- [ ] `pyproject.toml` with dependencies (pydantic, pyyaml, typer, rich, pygame)
- [ ] Dev dependencies (pytest, mypy, ruff, black)
- [ ] Pre-commit hooks (formatting, linting)
- [ ] CI pipeline (tests on push)

### 0.3 Initial Package Structure

- [ ] Create empty modules for each subsystem
- [ ] Set up `__init__.py` exports
- [ ] Basic `renee --version` command works

### Phase 0 Deliverable

```bash
$ pip install -e ".[dev]"
$ renee --version
renee 0.1.0
$ pytest
# 0 tests (but infrastructure works)
```

---

## Phase 1: Data Layer

**Goal**: The core data structures that everything else builds on.

### 1.1 Semantic Types Module

Framework-provided types beyond Python primitives.

**Implementation:**
```python
# src/renee/types/core.py

from typing import NewType, Annotated
from dataclasses import dataclass

# Entity reference (int at runtime, but semantically meaningful)
EntityId = NewType('EntityId', int)

# Asset reference (validated against manifest)
AssetRef = NewType('AssetRef', str)

# Probability (0.0 to 1.0)
Probability = Annotated[float, "0.0 <= x <= 1.0"]

# Dice notation
@dataclass
class DiceRoll:
    count: int
    sides: int
    modifier: int = 0

    @classmethod
    def parse(cls, notation: str) -> "DiceRoll":
        """Parse '2d6+3' format"""
        ...

    def roll(self, rng) -> int:
        """Roll with given RNG"""
        ...

# Position on grid
@dataclass
class Position:
    x: int
    y: int
```

**Tasks:**
- [ ] Define `EntityId`, `AssetRef`, `Probability`, `Position`, `DiceRoll`, `Duration`
- [ ] Implement `DiceRoll.parse()` for notation like "2d6+3"
- [ ] Implement `Formula` type for runtime-evaluated expressions
- [ ] Write unit tests for each type
- [ ] **Document: Semantic Types Reference (NEW DOCUMENTATION)**

### 1.2 Schema Registry

Runtime-queryable type definitions.

**Implementation:**
```python
# src/renee/schema/registry.py

class SchemaRegistry:
    def register(self, name: str, schema: dict) -> None:
        """Register a component/event schema"""

    def get(self, name: str) -> Schema:
        """Get schema by name"""

    def list(self, type: str = None) -> list[str]:
        """List registered schemas, optionally filtered by type"""

    def validate(self, name: str, data: dict) -> ValidationResult:
        """Validate data against schema"""

    def load_from_yaml(self, path: Path) -> None:
        """Load schemas from YAML file"""
```

**Tasks:**
- [ ] Implement `SchemaRegistry` class
- [ ] Schema loading from YAML
- [ ] Validation with Pydantic (at boundaries)
- [ ] Introspection API (`get`, `list`, `fields`)
- [ ] Constraint validation (`min`, `max`, `enum`, `pattern`, etc.)
- [ ] Cross-field invariant validation
- [ ] JSON serialization of schemas
- [ ] **Document: Component Definition Specification (NEW DOCUMENTATION)**
  - Field types and constraints
  - How to define custom components
  - Schema YAML format

### 1.3 ECS Core

Entity-Component-System implementation.

**Implementation:**
```python
# src/renee/ecs/world.py

class World:
    def create_entity(self) -> EntityId:
        """Create empty entity, return ID"""

    def destroy_entity(self, entity: EntityId) -> None:
        """Remove entity and all its components"""

    def add_component(self, entity: EntityId, component: Any) -> None:
        """Attach component to entity"""

    def remove_component(self, entity: EntityId, component_type: type) -> None:
        """Remove component from entity"""

    def get_component(self, entity: EntityId, component_type: type[T]) -> T:
        """Get component from entity"""

    def has_component(self, entity: EntityId, component_type: type) -> bool:
        """Check if entity has component"""

    def query(self, *component_types: type) -> Iterator[EntityId]:
        """Get all entities with specified components"""

    def spawn(self, template: str, **overrides) -> EntityId:
        """Spawn entity from template with optional overrides"""
```

**Tasks:**
- [ ] Implement `World` class
- [ ] Entity creation/destruction
- [ ] Component add/remove/get/has
- [ ] Query by component types
- [ ] Query by tags
- [ ] Template-based spawning
- [ ] Entity lifecycle hooks (`on_spawn`, `on_destroy`)
- [ ] Snapshot/restore for rollback
- [ ] **Document: Entity-Component Relationship (NEW DOCUMENTATION)**
  - ECS mental model
  - Entities are IDs, not types
  - Templates are component bundles

### 1.4 Event Bus

Event emission, subscription, and history.

**Implementation:**
```python
# src/renee/events/bus.py

class EventBus:
    def emit(self, event_type: str, data: dict) -> None:
        """Emit event to all subscribers"""

    def on(self, event_type: str, handler: Callable) -> None:
        """Subscribe to event type"""

    def off(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from event type"""

    def history(self,
                event_type: str = None,
                turn: int = None,
                last: int = None) -> list[Event]:
        """Query event history"""

    def clear_history(self) -> None:
        """Clear event history"""
```

**Tasks:**
- [ ] Implement `EventBus` class
- [ ] Event emission with automatic metadata (turn, timestamp, id)
- [ ] Subscription with handlers
- [ ] Event history storage
- [ ] History querying (by type, turn, entity, custom filter)
- [ ] Framework events: define which events the engine always emits
- [ ] **Document: Event System Specification (NEW DOCUMENTATION)**
  - Events vs Actions distinction
  - Built-in framework events
  - Custom event definition
  - Subscription patterns

### 1.5 Spatial Reasoning Helpers

Grid utilities, pathfinding, and spatial queries that AI shouldn't implement from scratch.

**Implementation:**
```python
# src/renee/spatial/grid.py

class Grid:
    def __init__(self, width: int, height: int):
        """Create grid of given dimensions"""

    def set_blocked(self, x: int, y: int, blocked: bool = True) -> None:
        """Mark tile as blocked/unblocked"""

    def get_path(self, from_pos: tuple, to_pos: tuple) -> list[tuple]:
        """A* pathfinding between two positions"""

    def has_line_of_sight(self, from_pos: tuple, to_pos: tuple) -> bool:
        """Check if there's clear line of sight"""

    def get_tiles_in_range(self, center: tuple, distance: int) -> list[tuple]:
        """Get all tiles within Manhattan distance"""

    def get_tiles_in_cone(self, origin: tuple, direction: str, angle: int, distance: int) -> list[tuple]:
        """Get tiles in a cone shape"""

    def get_entities_at(self, x: int, y: int) -> list[EntityId]:
        """Get all entities at position"""
```

**Tasks:**
- [ ] Implement `Grid` class
- [ ] A* pathfinding algorithm
- [ ] Bresenham line-of-sight
- [ ] Range queries (circle, cone, rectangle)
- [ ] Entity position tracking
- [ ] Obstacle integration with ECS
- [ ] **Document: Spatial API Reference (NEW DOCUMENTATION)**

### 1.6 Asset Management

Validated asset references with generated constants - no magic strings.

**Implementation:**
```python
# src/renee/assets/registry.py

class AssetRegistry:
    def scan(self, assets_dir: Path) -> None:
        """Scan directory and build manifest"""

    def validate_reference(self, asset_type: str, name: str) -> bool:
        """Check if asset reference is valid"""

    def generate_constants(self, output_path: Path) -> None:
        """Generate Python constants file"""

    def get_path(self, asset_type: str, name: str) -> Path:
        """Get filesystem path for asset"""
```

**Generated Output:**
```python
# Generated: renee/assets.py
class Sprites:
    UNIT_INFANTRY = "unit_infantry"
    UNIT_CAVALRY = "unit_cavalry"
    CARD_CREATURE = "card_creature"

class Sounds:
    ACTION_CONFIRM = "action_confirm"
    TURN_START = "turn_start"

class Assets:
    Sprites = Sprites
    Sounds = Sounds
```

**Tasks:**
- [ ] Implement `AssetRegistry` class
- [ ] Directory scanning for sprites, sounds, fonts
- [ ] Manifest generation (`assets/manifest.yaml`)
- [ ] Python constants generation
- [ ] Validation of asset references in entities
- [ ] CLI command: `renee assets scan`
- [ ] CLI command: `renee assets validate`

### Phase 1 Deliverable

```python
# This code should work:
from renee import World, SchemaRegistry, EventBus
from renee.types import EntityId, Position
from renee.spatial import Grid
from renee.assets import Assets

# Schema registration
schema = SchemaRegistry()
schema.load_from_yaml("schemas/components.yaml")

# ECS operations
world = World()
entity = world.create_entity()
world.add_component(entity, Position(x=5, y=3))
world.add_component(entity, Health(current=100, max=100))

# Queries
for e in world.query(Position, Health):
    print(f"Entity {e} at {world.get_component(e, Position)}")

# Events
bus = EventBus()
bus.on("damage_dealt", lambda e: print(f"Damage: {e.amount}"))
bus.emit("damage_dealt", {"target": entity, "amount": 15})

# Spatial
grid = Grid(20, 15)
path = grid.get_path((0, 0), (10, 10))
in_range = grid.get_tiles_in_range((5, 5), distance=3)

# Assets (type-safe, no magic strings)
sprite = Assets.Sprites.UNIT_INFANTRY
```

---

## Phase 2: Logic Layer

**Goal**: The systems that process game logic.

### 2.1 Action Pipeline

Request → Validation → Rules → Execution → Events.

**Implementation:**
```python
# src/renee/actions/pipeline.py

class ActionPipeline:
    def register_action(self, name: str, handler: Callable, schema: dict) -> None:
        """Register an action type with its handler and validation schema"""

    def execute(self, action_name: str, **params) -> ActionResult:
        """Execute action through the pipeline"""
        # 1. Validate params against schema
        # 2. Run pre-rules (can modify/cancel)
        # 3. If not cancelled, run handler
        # 4. Run post-rules
        # 5. Emit completion event

class ActionContext:
    """Passed to rules, allows modification/cancellation"""
    action_name: str
    params: dict
    world: World
    cancelled: bool = False

    def cancel(self, reason: str) -> None:
        """Cancel this action"""

    def modify(self, **changes) -> None:
        """Modify action parameters"""
```

**Tasks:**
- [ ] Implement `ActionPipeline` class
- [ ] Action registration with schemas
- [ ] Parameter validation
- [ ] Pre-rule execution phase
- [ ] Action handler execution
- [ ] Post-rule execution phase
- [ ] Action cancellation
- [ ] Action modification by rules
- [ ] Action result/events
- [ ] **Document: Action Pipeline Specification (NEW DOCUMENTATION)**
  - Pipeline stages diagram
  - How rules intercept actions
  - Modification vs cancellation
  - Custom action definition

### 2.2 Rule Engine

Python decorators for game logic.

**Implementation:**
```python
# src/renee/rules/engine.py

class RuleEngine:
    def register(self, rule: Rule) -> None:
        """Register a rule"""

    def get_matching_rules(self, phase: str, action: str) -> list[Rule]:
        """Get rules that match current context"""

    def execute_rules(self, phase: str, ctx: ActionContext) -> None:
        """Execute all matching rules in order"""

# Decorator for defining rules
def rule(when: str = None, phase: str = "pre", priority: int = 0):
    """Decorator to register a function as a rule"""
    def decorator(fn):
        ...
    return decorator

# Usage:
@rule(phase="pre", priority=10)
def shield_blocks_damage(ctx: RuleContext):
    """Reduce damage if target has shield"""
    if ctx.action_name == "attack":
        target = ctx.params["target"]
        if ctx.world.has_component(target, Shield):
            shield = ctx.world.get_component(target, Shield)
            ctx.modify(damage=ctx.params["damage"] - shield.reduction)
```

**Tasks:**
- [ ] Implement `RuleEngine` class
- [ ] `@rule` decorator
- [ ] Rule registration and discovery
- [ ] Rule matching (by action type, conditions)
- [ ] Rule execution order (priority)
- [ ] Rule context object
- [ ] Pre/post phase distinction
- [ ] **Document: Rule Context API (NEW DOCUMENTATION)**
  - Full `ctx` object specification
  - How to modify actions
  - How to cancel actions
  - Priority and ordering

### 2.3 Turn Manager

Flexible, game-defined time structure.

**Implementation:**
```python
# src/renee/turns/manager.py

class TurnManager:
    def define_structure(self, structure: TimeStructure) -> None:
        """Set the turn structure for this game"""

    def current_unit(self, level: str) -> TimeUnit:
        """Get current time unit at given level (round, turn, phase)"""

    def current_actor(self) -> EntityId:
        """Who is currently acting"""

    def advance(self) -> None:
        """Advance to next unit (may cascade: phase→turn→round)"""

    def can_act(self, entity: EntityId, action: str) -> bool:
        """Check if entity can take this action in current phase"""

class TimeStructure:
    """Defines the hierarchy of time units"""

class TimeUnit:
    """A single level of time (round, turn, phase, etc.)"""

class Phase:
    """A phase within a turn, with traits"""

class Trait:
    """Composable behavior for phases (skippable, timed, etc.)"""
```

**Tasks:**
- [ ] Implement `TimeStructure`, `TimeUnit`, `Phase`, `Trait` classes
- [ ] Configurable hierarchy (game defines own levels)
- [ ] Turn order strategies (alternating, clockwise, initiative, simultaneous, custom)
- [ ] Phase traits (skippable, mandatory, timed, interruptible, etc.)
- [ ] Phase templates (ActionPhase, ResourcePhase, etc.)
- [ ] Transition rules (auto, manual, conditional)
- [ ] AI turn hooks
- [ ] YAML-based structure definition
- [ ] **Document: Turn Manager Specification (NEW DOCUMENTATION)**
  - TimeUnit abstraction
  - Trait system
  - Pre-built templates
  - Custom structure examples

### Phase 2 Deliverable

```python
# This code should work:
from renee import World, ActionPipeline, RuleEngine, TurnManager
from renee.rules import rule
from renee.turns import TimeStructure, Phase, Trait

# Define turn structure
turns = TurnManager()
turns.define_structure(TimeStructure([
    Phase("main", traits=[Trait.UNLIMITED_ACTIONS, Trait.MANUAL_ADVANCE]),
    Phase("end", traits=[Trait.AUTO_ADVANCE]),
]))

# Define rules
@rule(phase="pre")
def modifier_reduces_effect(ctx):
    if ctx.action_name == "engage":
        target = ctx.params["target"]
        if ctx.world.has_component(target, Protection):
            protection = ctx.world.get_component(target, Protection)
            ctx.modify(effect=max(0, ctx.params["effect"] - protection.value))

# Execute action (goes through pipeline + rules)
pipeline.execute("engage", source=unit_a, target=unit_b, effect=10)
```

---

## Phase 3: I/O Layer

**Goal**: Loading game content and outputting to renderers.

### 3.1 YAML Loaders

Parse game content from files.

**Implementation:**
```python
# src/renee/loaders/entity_loader.py

class EntityLoader:
    def load(self, path: Path) -> EntityTemplate:
        """Load entity template from YAML"""

    def load_directory(self, path: Path) -> dict[str, EntityTemplate]:
        """Load all templates from directory"""

# src/renee/loaders/scene_loader.py

class SceneLoader:
    def load(self, path: Path) -> Scene:
        """Load scene from YAML"""

# Similar: SchemaLoader, RuleLoader (discovers Python rules), TurnStructureLoader
```

**Tasks:**
- [ ] Entity template loader
- [ ] Scene loader (tilemap, entity spawns, scene rules)
- [ ] Schema loader
- [ ] Turn structure loader (YAML → TimeStructure)
- [ ] Validation during load (references exist, schemas valid)
- [ ] Helpful error messages with line numbers

### 3.2 Render Command System

Abstract output that renderers consume.

**Implementation:**
```python
# src/renee/rendering/commands.py

@dataclass
class RenderCommand:
    """Base for all render commands"""
    type: str

@dataclass
class ClearCommand(RenderCommand):
    type: str = "clear"
    color: str = "#000000"

@dataclass
class DrawSpriteCommand(RenderCommand):
    type: str = "draw_sprite"
    sprite: str
    x: int
    y: int
    flip_x: bool = False
    flip_y: bool = False

# ... other commands

class RenderCommandBuffer:
    def clear(self, color: str) -> None:
        """Add clear command"""

    def draw_sprite(self, sprite: str, x: int, y: int, **kwargs) -> None:
        """Add sprite draw command"""

    def get_commands(self) -> list[RenderCommand]:
        """Get all commands for this frame"""
```

**Tasks:**
- [ ] Define all render command types (clear, draw_sprite, draw_rect, draw_text, draw_tilemap, etc.)
- [ ] Render command buffer
- [ ] Command serialization to JSON/dict
- [ ] Y-sorting for depth
- [ ] Layer system

### 3.3 Base Renderer Interface

Abstract interface that concrete renderers implement.

**Implementation:**
```python
# src/renee/rendering/base.py

class BaseRenderer(ABC):
    @abstractmethod
    def initialize(self, config: dict) -> None:
        """Set up renderer (create window, load assets)"""

    @abstractmethod
    def render(self, commands: list[RenderCommand]) -> None:
        """Process render commands"""

    @abstractmethod
    def get_input(self) -> InputState:
        """Get current input state"""

    @abstractmethod
    def shutdown(self) -> None:
        """Clean up resources"""
```

**Tasks:**
- [ ] Define `BaseRenderer` ABC
- [ ] Define `InputState` structure
- [ ] Implement `PygameRenderer`
- [ ] Implement `HeadlessRenderer` (for testing)
- [ ] Asset loading interface

### 3.4 Input System

Map raw input to game actions.

**Implementation:**
```python
# src/renee/input/manager.py

class InputManager:
    def bind(self, input: str, action: str) -> None:
        """Bind input to action (e.g., 'space' → 'attack')"""

    def process(self, input_state: InputState) -> list[str]:
        """Convert raw input to action names"""

    def load_bindings(self, path: Path) -> None:
        """Load bindings from config file"""
```

**Tasks:**
- [ ] Input binding system
- [ ] Keyboard mapping
- [ ] Mouse mapping (click positions to grid/entities)
- [ ] Binding configuration (YAML)
- [ ] **Document: Input → Action Binding (NEW DOCUMENTATION)**

### Phase 3 Deliverable

```python
# This code should work:
from renee import World
from renee.loaders import EntityLoader, SceneLoader
from renee.rendering import PygameRenderer, RenderCommandBuffer

# Load content
entities = EntityLoader().load_directory("entities/")
scene = SceneLoader().load("scenes/level_1.yaml")

# Set up renderer
renderer = PygameRenderer()
renderer.initialize({"width": 800, "height": 600})

# Game loop
buffer = RenderCommandBuffer()
buffer.clear("#1a1a2e")
for entity in world.query(Position, Sprite):
    pos = world.get_component(entity, Position)
    sprite = world.get_component(entity, Sprite)
    buffer.draw_sprite(sprite.idle, pos.x * 32, pos.y * 32)

renderer.render(buffer.get_commands())
```

---

## Phase 4: CLI & Tooling

**Goal**: Command-line tools for game development.

### 4.1 CLI Framework

Base CLI with `--json` support everywhere.

**Implementation:**
```python
# src/renee/cli/main.py

import typer
from rich import print

app = typer.Typer()

@app.command()
def version(json: bool = False):
    """Show version"""
    if json:
        print({"version": "0.1.0"})
    else:
        print("renee 0.1.0")

# ... other commands
```

**Tasks:**
- [ ] Set up typer CLI
- [ ] Global `--json` flag
- [ ] Rich output for human mode
- [ ] Consistent exit codes (0 = success, 1 = error)
- [ ] Error output in JSON format

### 4.2 Core Commands

Essential commands for development.

**Commands:**
```bash
renee new <name>           # Create project scaffold
renee validate [path]      # Validate YAML files
renee run [scene]          # Run game
renee test [pattern]       # Run tests
```

**Tasks:**
- [ ] `renee new` - project scaffolding
- [ ] `renee validate` - schema validation
- [ ] `renee run` - game execution
- [ ] `renee test` - pytest wrapper

### 4.3 Introspection Commands

Query the framework about itself.

**Commands:**
```bash
renee schema list          # List all schemas
renee schema show <name>   # Show schema details
renee info <name>          # Info about entity/component/rule
```

**Tasks:**
- [ ] `renee schema list`
- [ ] `renee schema show`
- [ ] `renee info`

### 4.4 REPL

Interactive game manipulation.

**Implementation:**
```python
# src/renee/repl/repl.py

class Repl:
    def run(self, scene_path: str, json_mode: bool = False) -> None:
        """Start REPL session"""

    def execute(self, command: str) -> dict:
        """Execute REPL command, return result"""
```

**Commands:**
```
> inspect <entity>
> query <component> [<component>...]
> set <entity> <component>.<field> <value>
> do <action> [params...]
> spawn <template> [at x,y]
> destroy <entity>
> snapshot save <name>
> snapshot restore <name>
> history [last N]
```

**Tasks:**
- [ ] REPL command parser
- [ ] All REPL commands
- [ ] JSON mode output
- [ ] Tab completion
- [ ] Command history

### Phase 4 Deliverable

```bash
$ renee new my_game
Created project: my_game/

$ cd my_game && renee validate
All files valid.

$ renee schema show Health --json
{"name": "Health", "fields": {...}}

$ renee repl scenes/level_1.yaml
> inspect player
Entity: player (id=1)
  Position: {x: 0, y: 0}
  Health: {current: 100, max: 100}
> do attack target=2
Action executed: attack
```

---

## Phase 5: AI-Native Features

**Goal**: Tools that give AI agents insights they can't derive themselves.

### 5.1 Impact Analysis

Show what breaks before making changes.

**Implementation:**
```python
# src/renee/analysis/impact.py

class ImpactAnalyzer:
    def analyze(self, change: str) -> ImpactReport:
        """Analyze impact of a proposed change"""
        # Returns: affected files, affected rules, intent violations, simulation delta
```

**Tasks:**
- [ ] Parse change expressions ("entity.Component.field=value")
- [ ] Find affected files (grep + semantic)
- [ ] Find affected rules
- [ ] Intent field parsing and validation
- [ ] Integration with simulation
- [ ] `renee impact` command

### 5.2 Simulation Engine

Run hypothetical scenarios.

**Implementation:**
```python
# src/renee/simulation/engine.py

class SimulationEngine:
    def run_combat(self, attacker: str, defender: str, iterations: int) -> SimResult:
        """Simulate combat N times, return statistics"""

    def run_what_if(self, change: str, scenario: str, iterations: int) -> CompareResult:
        """Compare baseline vs modified"""

    def run_sweep(self, entity: str, field: str, values: list, iterations: int) -> SweepResult:
        """Test range of values"""
```

**Tasks:**
- [ ] Deterministic RNG with seeding
- [ ] Combat simulation
- [ ] What-if comparison
- [ ] Parameter sweep
- [ ] Statistical output
- [ ] `renee simulate` command

### 5.3 Context Commands

Starter kits for common tasks.

**Tasks:**
- [ ] `renee context add-entity`
- [ ] `renee context add-system`
- [ ] `renee context add-rule`
- [ ] `renee context add-scene`

### Phase 5 Deliverable

```bash
$ renee impact "infantry.UnitStats.strength=15" --json
{
  "change": "infantry.UnitStats.strength=15",
  "affected_files": ["entities/infantry.yaml", "tests/test_engagement.py"],
  "affected_rules": ["modifier_reduces_effect"],
  "intent_violations": [{
    "entity": "Infantry",
    "intent": "eliminated in 2-3 engagements",
    "violation": "now requires 4 engagements"
  }],
  "simulation_delta": {
    "attacker_win_rate": "92% → 78%"
  }
}

$ renee simulate scenario --entity-a Commander --entity-b Infantry --iterations 1000 --json
{
  "win_rate": 0.87,
  "avg_turns": 2.3,
  "avg_resource_remaining": 65
}
```

---

## Phase 6: Integration & Testing

**Goal**: Prove it works with a real game.

### 6.1 Example Game: Territory Control

Build the tutorial game using the framework. A strategy game demonstrating core systems.

**Tasks:**
- [ ] Define components (UnitStats, Position, Control, Resources)
- [ ] Define entities (Commander, Infantry, Territory, Outpost)
- [ ] Define rules (engagement, capture, resource production)
- [ ] Define scenes (tutorial map, skirmish arena)
- [ ] Define turn structure
- [ ] Write tests
- [ ] Make it playable

### 6.2 Documentation Completion

Fill all documentation gaps.

**Tasks:**
- [ ] **Component Definition Specification** - complete
- [ ] **Entity-Component Relationship** - complete
- [ ] **Event System Specification** - complete
- [ ] **Action Pipeline Specification** - complete
- [ ] **Rule Context API** - complete
- [ ] **Turn Manager Specification** - complete
- [ ] **Input → Action Binding** - complete
- [ ] **PATTERNS.md** - all patterns complete
- [ ] API reference (generated from docstrings)

### 6.3 Test Coverage

Comprehensive framework tests.

**Tasks:**
- [ ] Unit tests for every module
- [ ] Integration tests (full game flow)
- [ ] Property-based tests for core logic
- [ ] Performance benchmarks
- [ ] CI enforcement of coverage threshold

### Phase 6 Deliverable

```bash
$ cd examples/example_game
$ renee validate
All files valid.

$ pytest
42 passed in 1.2s

$ renee run
# Playable game launches
```

---

## What NOT to Build

Explicitly out of scope:

| Don't Build | Why |
|-------------|-----|
| Custom YAML rule DSL | Python works better, AI knows Python |
| Custom test DSL | pytest works better |
| Visual level editor | Text + AI is the paradigm |
| Networking/multiplayer | Different architecture entirely |
| 3D support | Turn-based 2D only |
| Physics engine | Not needed for turn-based |

---

## Documentation Gaps Summary

These must be written during their respective phases:

| Phase | Documentation Needed |
|-------|---------------------|
| 1 | Semantic Types Reference |
| 1 | Component Definition Specification |
| 1 | Entity-Component Relationship |
| 1 | Event System Specification |
| 1 | Spatial API Reference |
| 2 | Action Pipeline Specification |
| 2 | Rule Context API |
| 2 | Turn Manager Specification |
| 3 | Input → Action Binding |
| 6 | Complete PATTERNS.md |

---

## Success Criteria

### Framework is Complete When:

- [ ] Example game (territory control) is fully playable
- [ ] All documentation gaps are filled
- [ ] All CLI commands work with `--json`
- [ ] Test coverage > 80%
- [ ] A developer can build a different game type (card game, RPG) using only docs
- [ ] An AI agent can modify the example game, validate, simulate, and verify

---

## Appendix: Module Dependency Order

Build in this order to minimize blocked work:

```
Phase 1 (no dependencies):
  types → schema → ecs → events → spatial → assets

  Note: spatial depends on ecs (for entity positions)
        assets has no dependencies (standalone)

Phase 2 (depends on Phase 1):
  actions → rules → turns
  (all depend on: ecs, events)

Phase 3 (depends on Phase 1):
  loaders (depends on: schema, ecs, assets)
  rendering (no dependencies)
  input (depends on: actions)

Phase 4 (depends on Phase 1-3):
  cli (depends on: everything)
  repl (depends on: ecs, actions, loaders)

Phase 5 (depends on Phase 1-4):
  analysis (depends on: everything)
  simulation (depends on: ecs, actions, rules)
```

---

*This roadmap tracks building the Renee framework itself. For building games WITH Renee, see TUTORIAL.md.*
