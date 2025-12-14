# Renee CLI and REPL

The Renee CLI provides command-line tools for managing game projects, running games, and interactive development.

## Features

- **AI-Native Design**: All commands support `--json` flag for machine-parseable output
- **Interactive REPL**: Experiment with game state in real-time
- **Project Scaffolding**: Quick project creation with standard structure
- **Schema Introspection**: Query type definitions at runtime
- **Validation**: Check game files against schemas

## Installation

```bash
pip install renee
```

## Commands

### Project Management

#### `renee new`

Create a new game project with standard directory structure.

```bash
# Create a new project
renee new my-game

# Create with template
renee new my-game --template=tactics

# Specify custom path
renee new my-game --path=/path/to/project

# JSON output
renee new my-game --json
```

**Output Directory Structure:**
```
my-game/
├── game.yaml           # Project manifest
├── schemas/            # Type definitions
│   ├── components.yaml
│   ├── events.yaml
│   └── actions.yaml
├── entities/           # Entity templates
│   └── _templates/
├── systems/            # Game logic
├── rules/              # Game rules
├── scenes/             # Levels/maps
├── assets/             # Game assets
│   ├── sprites/
│   ├── sounds/
│   └── fonts/
└── tests/              # pytest tests
```

#### `renee validate`

Validate game files against schemas.

```bash
# Validate current project
renee validate

# Validate specific project
renee validate --project=/path/to/game

# JSON output
renee validate --json
```

### Game Execution

#### `renee run`

Run a game.

```bash
# Run current project
renee run

# Run specific project
renee run --project=/path/to/game

# Run headless (no graphics)
renee run --headless
```

### Introspection

#### `renee schema`

Show or list schemas.

```bash
# List all schemas
renee schema --list

# List component schemas only
renee schema --list --type=component

# Show specific schema
renee schema Health

# JSON output
renee schema --list --json
```

#### `renee query`

Query game state.

```bash
# Query specific entity
renee query --entity=42

# Query by tag
renee query --tag=player

# Query by component
renee query --component=Health

# JSON output
renee query --tag=player --json
```

### AI-Native Tools

#### `renee simulate`

Run simulations for balance testing.

```bash
# Run scenario 100 times
renee simulate scenarios/combat.yaml --runs=100

# Use specific seed for reproducibility
renee simulate scenarios/combat.yaml --runs=1000 --seed=42

# JSON output with statistics
renee simulate scenarios/combat.yaml --runs=100 --json
```

#### `renee impact`

Analyze impact of proposed changes.

```bash
# Analyze a change
renee impact "increase sword damage from 10 to 15"

# JSON output
renee impact "add cooldown to fireball spell" --json
```

**Output includes:**
- Affected files
- Affected rules
- Intent violations
- Simulation results (before/after)

### Interactive REPL

#### `renee repl`

Start interactive REPL for game manipulation.

```bash
# Start REPL for current project
renee repl

# Start REPL for specific project
renee repl --project=/path/to/game

# JSON mode (for AI agents)
renee repl --json-mode
```

## REPL Commands

The REPL provides an interactive environment for game experimentation.

### Entity Management

```bash
# Show entity details
renee> entity 0
Entity: 0
Components:
  Position: {"x": 0, "y": 0}
Tags: ["player"]

# List all entities
renee> entities
Count: 3
Entities: [0, 1, 2]

# List entities with tag
renee> entities player
Tag: player
Count: 1
Entities: [0]

# Create entity from template
renee> spawn player_template
Entity: 3
Template: player_template

# Destroy entity
renee> destroy 3
Success: Destroyed entity 3
```

### Component Operations

```bash
# Get component from entity
renee> component 0 Position
x: 0
y: 0

# Set component on entity
renee> set 0 Position {"x": 5, "y": 10}
Success: Set component 'Position' on entity 0

# Query entities with components
renee> query Position Health
# (Returns entities with both components)
```

### World State

```bash
# Show world state summary
renee> state
Entities:
  Count: 3
  IDs: [0, 1, 2]
Snapshots:
  Count: 1
  IDs: ["abc-123..."]

# Create snapshot
renee> snapshot
Snapshot ID: abc-123-def-456

# Restore to snapshot
renee> restore abc-123-def-456
Success: Restored to snapshot abc-123-def-456
```

### Other Commands

```bash
# Show command history
renee> history
Count: 5
Commands:
  [0]: entities
  [1]: entity 0
  [2]: snapshot
  [3]: destroy 1
  [4]: history

# Show help
renee> help

# Exit REPL
renee> exit
```

## JSON Mode

All commands support `--json` flag for machine-parseable output.

### Example: List schemas

```bash
$ renee schema --list --json
{
  "schemas": [
    "Health",
    "Position",
    "Sprite"
  ]
}
```

### Example: REPL JSON mode

```bash
$ renee repl --json-mode
{"entities": [0, 1, 2]}  # entities command
{"id": 0, "components": {...}, "tags": ["player"]}  # entity 0 command
{"success": "Destroyed entity 1"}  # destroy 1 command
```

## Output Formatting

The CLI provides two output modes:

### Human-Readable Mode (Default)

Pretty-printed output for developers:
- Tables for lists
- Indented JSON for complex data
- Status messages with context

### JSON Mode (`--json`)

Structured output for AI agents:
- Always valid JSON
- Consistent schema
- Machine-parseable

## Python API

You can also use the CLI components programmatically:

```python
from renee.cli.output import OutputFormatter
from renee.cli.repl import GameREPL
from renee.ecs.world import World

# Output formatting
formatter = OutputFormatter(json_mode=True)
formatter.success("Entity created", {"id": 42})

# REPL
world = World()
repl = GameREPL(world, json_mode=False)
result = repl.execute("entities")
print(result)
```

## Examples

See `examples/cli_demo.py` for a complete demonstration of CLI and REPL functionality.

```bash
python examples/cli_demo.py
```

## Testing

Run CLI tests:

```bash
pytest tests/test_cli.py
```

## Architecture

The CLI is built with:

- **typer**: Modern CLI framework with type hints
- **rich**: Beautiful terminal output (optional enhancement)
- **pydantic**: Data validation
- **World**: ECS core for state management

### Module Structure

```
renee/cli/
├── __init__.py       # Package exports
├── main.py           # Main CLI entry point (typer app)
├── output.py         # Output formatting (JSON & human)
├── repl.py           # REPL implementation
├── commands/         # Command modules (future organization)
│   └── __init__.py
└── README.md         # This file
```

## Design Principles

### 1. AI-First Design

Every command outputs JSON with `--json`:
```bash
renee schema Health --json
```

### 2. Consistent Output Schema

All JSON responses follow a consistent structure:
```json
{
  "status": "success|error|info",
  "message": "Human-readable message",
  "data": { ... }
}
```

### 3. Introspection

The framework can describe itself:
```bash
renee schema --list
renee query --help
```

### 4. Interactive Experimentation

The REPL enables rapid iteration:
- Create entities
- Modify state
- Create snapshots
- Roll back changes
- Query results

## Future Enhancements

Planned features:
- [ ] `renee run` - Game execution
- [ ] `renee validate` - Schema validation
- [ ] `renee simulate` - Balance testing
- [ ] `renee impact` - Change analysis
- [ ] Enhanced REPL commands (action execution, event history)
- [ ] Project templates (tactics, card game, roguelike)
- [ ] Asset manifest generation
