# Renee CLI Quick Start

## Installation

```bash
pip install -e .
```

## Quick Commands

### Create a New Game

```bash
# Create a new project
renee new my-game

# With template
renee new my-game --template=tactics
```

### Interactive REPL

```bash
# Start REPL
renee repl

# Common REPL commands
renee> entities              # List all entities
renee> entity 0             # Show entity details
renee> state                # Show world state
renee> snapshot             # Create state snapshot
renee> help                 # Show help
renee> exit                 # Exit REPL
```

### Schema Introspection

```bash
# List all schemas
renee schema --list

# Show specific schema
renee schema Health

# JSON output for AI
renee schema --list --json
```

### AI-Friendly JSON Mode

All commands support `--json` for machine-parseable output:

```bash
renee schema --list --json
renee repl --json-mode
renee new my-game --json
```

## REPL Quick Reference

| Command | Description | Example |
|---------|-------------|---------|
| `entity <id>` | Show entity details | `entity 0` |
| `entities [tag]` | List entities | `entities player` |
| `spawn <template>` | Create from template | `spawn enemy` |
| `destroy <id>` | Remove entity | `destroy 3` |
| `component <entity> <type>` | Get component | `component 0 Position` |
| `set <entity> <comp> <json>` | Set component | `set 0 Position {"x": 5}` |
| `state` | Show world summary | `state` |
| `snapshot` | Save state | `snapshot` |
| `restore <id>` | Restore state | `restore abc-123...` |
| `history` | Show commands | `history` |
| `help` | Show help | `help` |
| `exit` | Exit REPL | `exit` |

## Example Session

```bash
# Create a new game
$ renee new tactics-game
Success: Created new project: tactics-game

# Start REPL
$ cd tactics-game
$ renee repl

renee> entities
Count: 0
Entities: []

renee> state
Entities:
  Count: 0
  IDs: []
Snapshots:
  Count: 0
  IDs: []

renee> snapshot
Snapshot ID: abc-123-def-456

renee> exit
Success: Goodbye!
```

## JSON Mode Example

```bash
$ renee repl --json-mode
{"count": 0, "entities": []}
{"entities": {"count": 0, "ids": []}, "snapshots": {"count": 0, "ids": []}}
{"snapshot_id": "abc-123-def-456"}
{"success": "Goodbye!"}
```

## Project Structure

After running `renee new my-game`:

```
my-game/
├── game.yaml              # Project config
├── schemas/               # Type definitions
│   ├── components.yaml
│   ├── events.yaml
│   └── actions.yaml
├── entities/              # Entity templates
├── systems/               # Game logic
├── rules/                 # Game rules
├── scenes/                # Levels
├── assets/                # Game assets
└── tests/                 # Tests
```

## Next Steps

1. Define components in `schemas/components.yaml`
2. Create entity templates in `entities/`
3. Implement game systems in `systems/`
4. Add rules in `rules/`
5. Use REPL to test and experiment

## Documentation

- Full CLI docs: `src/renee/cli/README.md`
- Framework design: `DESIGN.md`
- Examples: `examples/cli_demo.py`

## Running Examples

```bash
# CLI demonstration
python examples/cli_demo.py

# Run tests
pytest tests/test_cli.py -v
```
