# Renee-Merged Status

This is the unified implementation of the Renee AI-native turn-based game framework, merging the best features from both renee-codex and renee-claude worktrees.

## Merge Summary

**Base**: renee-codex (better DESIGN.md compliance: event appliers, @rule decorator, intents)

**Added from renee-claude**:
- Game class orchestrator
- Entity templates and bulk operations
- Rule introspection (to_json, get_summary)
- typer + rich CLI
- Additional render commands (DrawLine, DrawCircle, DrawTilemap)

## Feature Completion

| Feature | Status | Source |
|---------|--------|--------|
| ECS World with intents | Done | codex |
| Entity templates | Done | claude |
| Bulk operations | Done | claude |
| WorldSnapshot rollback | Done | codex |
| Named snapshots | Done | merged |
| Action Pipeline | Done | codex |
| Event Appliers | Done | codex |
| @rule decorator | Done | codex |
| Rule introspection | Done | claude |
| EventBus with history | Done | codex |
| SchemaRegistry | Done | codex |
| TurnManager | Done | codex |
| Grid (spatial) | Done | codex |
| Multiplayer (NDJSON TCP) | Done | codex |
| Game orchestrator | Done | claude |
| typer CLI | Done | claude |
| Structured errors | Done | codex |
| Render commands | Done | merged |
| Renderers (pygame/terminal/headless) | Done | codex |

## Architecture

### Core Systems

1. **ECS World** (`ecs/world.py`)
   - Entity creation/destruction with lifecycle events
   - Component management with hooks
   - Tags and intents
   - Entity templates
   - Snapshots (both immediate and named)
   - Serialization (to_dict/from_dict)

2. **Action Pipeline** (`actions/pipeline.py`)
   - Event-sourced action processing
   - Pre/post rule execution
   - Schema validation
   - Turn validation
   - Event appliers for replay/sync

3. **Rule Engine** (`rules/engine.py`)
   - @rule decorator for Python-based rules
   - Priority ordering (higher = earlier)
   - Action type filtering
   - Intent documentation
   - Introspection (to_json, get_summary)

4. **Game Orchestrator** (`game.py`)
   - Central coordination
   - Lifecycle hooks (on_start, on_update, on_render, on_shutdown)
   - Real-time and turn-based modes
   - State management

5. **Event Bus** (`events/bus.py`)
   - Event emission with metadata
   - Subscription system
   - Event history

### CLI

Uses typer + rich for a type-safe CLI with beautiful output:

```bash
renee new my-game              # Create new project
renee schemas list --path x    # List schemas
renee demo local               # Run grid-walk demo
renee repl --demo              # Interactive REPL
```

All commands support `--json` for AI agent parsing.

## Tests

All 63 tests passing:
- test_actions.py - Action pipeline
- test_assets.py - Asset registry
- test_ecs.py - ECS world
- test_events.py - Event bus
- test_multiplayer.py - Multiplayer sync
- test_rendering.py - Render commands
- test_schema.py - Schema registry
- test_spatial.py - Grid and pathfinding
- test_turns.py - Turn manager
- test_types.py - Core types

## Usage

### Simple Mode (Game Orchestrator)

```python
from renee import Game, GameConfig

config = GameConfig(title="My Game", mode=GameMode.TURN_BASED)
game = Game(config)

@game.on_start
def setup():
    player = game.world.create_entity()
    game.world.add_component(player, Position(5, 5))

game.run()
```

### Advanced Mode (Primitives)

```python
from renee import World, ActionPipeline, EventBus, RuleEngine, rule

world = World()
bus = EventBus()
rules = RuleEngine()
pipeline = ActionPipeline(world=world, bus=bus, rules=rules)

@rule(phase="pre", priority=10, intent="Validate movement range")
def check_range(ctx):
    if distance > max_range:
        ctx.cancel("Target is out of range")

rules.register(check_range)
```

## Key Decisions

1. **Priority ordering**: Higher = earlier (more intuitive)
2. **CLI framework**: typer + rich (type-safe, beautiful output)
3. **Snapshot API**: Frozen dataclass + optional named storage
4. **Error handling**: Structured ReneeError with code/message/hint/context
5. **Rendering directory**: `render/` (shorter, consistent)
