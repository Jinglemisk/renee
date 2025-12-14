# Renee Game Framework - Launch Guide

Step-by-step instructions to verify the engine is in a working state.

---

## 1. Create Virtual Environment

```bash
cd /Users/jinglemisk/Desktop/CENGIZ\ AI/REPOS/workspace/renee-claude
python3 -m venv .venv
source .venv/bin/activate
```

---

## 2. Install Dependencies

```bash
pip install -e ".[dev]"
```

For pygame support (optional):
```bash
pip install -e ".[dev,graphics]"
```

---

## 3. Run All Tests

```bash
pytest tests/ -v
```

Expected output: `195 passed`

---

## 4. Verify Core Imports

```bash
python3 -c "
from renee.ecs.world import World
from renee.events.bus import EventBus
from renee.rules.engine import RuleEngine
from renee.actions.pipeline import ActionPipeline
from renee.schema.registry import SchemaRegistry
from renee.spatial import Grid, find_path
from renee.turns.manager import TurnManager
from renee.render import HeadlessRenderer, TerminalRenderer
from renee.game import Game, GameConfig, GameState, GameMode
print('All core imports successful')
"
```

---

## 5. Run the CLI

```bash
renee --help
```

Expected output: CLI help with available commands.

---

## 6. Run the REPL

```bash
python3 -c "
from renee.ecs.world import World
from renee.cli.repl import GameREPL

world = World()
repl = GameREPL(world, json_mode=False)

# Test commands
print(repl.execute('help'))
print(repl.execute('state'))
print(repl.execute('entities'))
"
```

---

## 7. Verify ECS System

```bash
python3 -c "
from dataclasses import dataclass
from renee.ecs.world import World
from renee.types import EntityId, Position

@dataclass
class Health:
    current: int
    maximum: int

world = World()

# Create entity with components
entity = world.create_entity()
world.add_component(entity, Position(5, 10))
world.add_component(entity, Health(100, 100))
world.add_tag(entity, 'player')

# Query
pos = world.get_component(entity, Position)
print(f'Entity {entity} at position ({pos.x}, {pos.y})')

# Query by component
for e in world.query(Position, Health):
    print(f'Found entity with Position and Health: {e}')

print('ECS system working')
"
```

---

## 8. Verify Event System

```bash
python3 -c "
from dataclasses import dataclass
from renee.events.bus import EventBus
from renee.types import EntityId

@dataclass(frozen=True)
class DamageEvent:
    target: EntityId
    amount: int

bus = EventBus()
received = []

def on_damage(event):
    received.append(event)
    print(f'Received damage event: {event.amount} damage to entity {event.target}')

bus.subscribe(DamageEvent, on_damage)
bus.emit(DamageEvent(target=EntityId(1), amount=25))

assert len(received) == 1
print('Event system working')
"
```

---

## 9. Verify Rule Engine

```bash
python3 -c "
from renee.rules.engine import RuleEngine
from renee.rules.decorators import pre_rule, post_rule
from renee.actions.action import Action

engine = RuleEngine()

@pre_rule('attack', engine=engine)
def check_range(ctx):
    if ctx.params.get('distance', 0) > 5:
        ctx.cancel('Target out of range')

@post_rule('attack', engine=engine)
def log_attack(ctx):
    print(f'Attack executed on {ctx.params.get(\"target\")}')

# Test the rules
from renee.rules.context import ActionContext
ctx = ActionContext(action_type='attack', params={'target': 'enemy', 'distance': 3})
engine.apply_rules('attack', 'pre', ctx)
print(f'Action cancelled: {ctx.cancelled}')

ctx2 = ActionContext(action_type='attack', params={'target': 'enemy', 'distance': 10})
engine.apply_rules('attack', 'pre', ctx2)
print(f'Out of range cancelled: {ctx2.cancelled}')

print('Rule engine working')
"
```

---

## 10. Verify Spatial System

```bash
python3 -c "
from renee.spatial import Grid, find_path
from renee.types import Position

grid = Grid(10, 10)

# Add obstacles
grid.set_blocked(Position(3, 3), True)
grid.set_blocked(Position(3, 4), True)
grid.set_blocked(Position(3, 5), True)

# Find path around obstacles
start = Position(1, 4)
goal = Position(5, 4)
path = find_path(grid, start, goal)

print(f'Path from {start} to {goal}:')
for pos in path:
    print(f'  -> ({pos.x}, {pos.y})')

print('Spatial system working')
"
```

---

## 11. Verify Headless Renderer

```bash
python3 -c "
from renee.render import HeadlessRenderer, ClearCommand, DrawRectCommand

renderer = HeadlessRenderer()
renderer.initialize({'width': 800, 'height': 600})

commands = [
    ClearCommand(color=(0, 0, 0)),
    DrawRectCommand(x=100, y=100, width=50, height=50, color=(255, 0, 0)),
]

renderer.render(commands)
print(f'Rendered {len(renderer.last_commands)} commands')
print(f'Renderer running: {renderer.is_running()}')

renderer.shutdown()
print('Headless renderer working')
"
```

---

## 12. Verify Game Class

```bash
python3 -c "
from renee.game import Game, GameConfig, GameMode
from renee.render import HeadlessRenderer

config = GameConfig(
    title='Test Game',
    mode=GameMode.TURN_BASED,
    target_fps=60
)

game = Game(config)

# Test lifecycle hooks
started = False
updated = False

@game.on_start
def setup():
    global started
    started = True
    entity = game.world.create_entity()
    print(f'Created entity {entity}')

@game.on_update
def update(dt):
    global updated
    updated = True

# Initialize renderer
renderer = HeadlessRenderer()
game.init_renderer(renderer, {'width': 800, 'height': 600})

# Start game (don't run loop)
game._start()
game._update(0.016)

print(f'Game state: {game.state}')
print(f'Started hook called: {started}')
print(f'Updated hook called: {updated}')
print(f'Entity count: {game.world.entity_count()}')

game.stop()
print('Game class working')
"
```

---

## 13. Verify Schema Registry

```bash
python3 -c "
from renee.schema.registry import SchemaRegistry
from renee.schema.schema import Schema, FieldDefinition

registry = SchemaRegistry()

# Register a component schema
registry.register_component(
    'Health',
    Schema(
        name='Health',
        schema_type='component',
        fields={
            'current': FieldDefinition(name='current', field_type='int', required=True),
            'maximum': FieldDefinition(name='maximum', field_type='int', required=True),
        },
        intent='Tracks entity health points'
    )
)

# Query the registry
print(f'Registered schemas: {registry.list_schemas()}')
print(f'Has Health: {registry.has_schema(\"Health\")}')

# Validate data
errors = registry.validate('Health', {'current': 100, 'maximum': 100})
print(f'Validation errors: {errors}')

print('Schema registry working')
"
```

---

## 14. Full Integration Test

```bash
python3 -c "
from dataclasses import dataclass
from renee.ecs.world import World
from renee.events.bus import EventBus
from renee.rules.engine import RuleEngine
from renee.rules.decorators import pre_rule
from renee.actions.pipeline import ActionPipeline
from renee.types import EntityId, Position

# Components
@dataclass
class Health:
    current: int
    maximum: int

@dataclass(frozen=True)
class DamageEvent:
    target: EntityId
    amount: int
    source: EntityId

# Setup systems
world = World()
bus = EventBus()
rules = RuleEngine()
pipeline = ActionPipeline()

# Create entities
player = world.create_entity()
world.add_component(player, Position(0, 0))
world.add_component(player, Health(100, 100))
world.add_tag(player, 'player')

enemy = world.create_entity()
world.add_component(enemy, Position(1, 0))
world.add_component(enemy, Health(50, 50))
world.add_tag(enemy, 'enemy')

# Register rule
@pre_rule('attack', engine=rules)
def validate_attack(ctx):
    target = ctx.params.get('target')
    if not world.entity_exists(target):
        ctx.cancel('Target does not exist')

# Register action handler
def handle_attack(ctx):
    target = ctx.params['target']
    damage = ctx.params['damage']

    health = world.get_component(target, Health)
    new_health = Health(max(0, health.current - damage), health.maximum)
    world.add_component(target, new_health)

    bus.emit(DamageEvent(target=target, amount=damage, source=ctx.params['source']))
    return {'damage_dealt': damage, 'remaining_hp': new_health.current}

pipeline.register_handler('attack', handle_attack)

# Execute attack
from renee.actions.action import Action
attack = Action('attack', {'target': enemy, 'damage': 20, 'source': player})

# Apply pre-rules
from renee.rules.context import ActionContext
ctx = ActionContext(action_type='attack', params=attack.params)
rules.apply_rules('attack', 'pre', ctx)

if not ctx.cancelled:
    result = pipeline.execute(attack, world, bus, rules)
    print(f'Attack result: {result.data}')

    enemy_health = world.get_component(enemy, Health)
    print(f'Enemy health: {enemy_health.current}/{enemy_health.maximum}')

    events = bus.get_history()
    print(f'Events emitted: {len(events)}')

print('Full integration test passed')
"
```

---

## Quick Verification Command

Run this single command to verify everything:

```bash
cd /Users/jinglemisk/Desktop/CENGIZ\ AI/REPOS/workspace/renee-claude && \
source .venv/bin/activate && \
pytest tests/ -q && \
python3 -c "from renee.game import Game; print('Framework ready')"
```

Expected output:
```
195 passed in X.XXs
Framework ready
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'renee'` | Run `pip install -e .` |
| `No module named 'pytest'` | Run `pip install pytest` |
| Tests fail with dataclass errors | Ensure Python 3.11+ |
| Import errors in render module | Check `render/__init__.py` exists |
