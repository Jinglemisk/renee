# Renee CLI Reference

> See [DESIGN.md](DESIGN.md) for strategic architecture

## Command Overview

```bash
renee <command> [options]

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
$ renee validate entities/
Validating entities/...
  ✓ goblin.yaml
  ✗ broken.yaml: Health.current exceeds Health.max
1 error found.

# Machine-parseable (for AI agents)
$ renee validate entities/ --json
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

### `renee impact`

Analyze the impact of a proposed change before making it.

```bash
$ renee impact "entities/goblin.yaml:Combat.attack=20"
$ renee impact "entities/goblin.yaml:Combat.attack=20" --json
```

See DESIGN.md Section 4.9 for detailed output format.

### `renee simulate`

Run deterministic simulations for balance testing.

```bash
# Single what-if simulation
$ renee simulate what-if \
    --change "goblin.Combat.attack=15" \
    --matchup "Player vs Goblin" \
    --iterations 1000

# Parameter sweep
$ renee simulate sweep \
    --entity Goblin \
    --field Combat.attack \
    --range 5,10,15,20,25 \
    --iterations 500

# Combat simulation
$ renee simulate combat \
    --entity Goblin \
    --vs Player \
    --iterations 100 \
    --json
```

See DESIGN.md Section 4.10 for detailed output format.

### `renee context`

Generate AI-optimized context for a specific task.

```bash
$ renee context --task "add enemy" --max-tokens 4000
$ renee context --task "balance entity" --entity Goblin --json
$ renee context --task "debug combat" --scene level_1
```

See DESIGN.md Section 4.11 for detailed output format.

### `renee info`

Get detailed information about any game element.

```bash
$ renee info Health              # Component schema
$ renee info Goblin              # Entity definition
$ renee info backstab            # Rule definition
$ renee info level_1             # Scene contents
$ renee info damage_dealt        # Event schema
```

## Common Workflows

### Starting a New Project

```bash
$ renee new my_game
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
$ renee validate
All files valid.

$ renee run
Starting game...
```

### Development Cycle

```bash
# 1. Make changes to entities/goblin.yaml

# 2. Validate changes
$ renee validate entities/goblin.yaml

# 3. See what changed
$ renee diff

# 4. Run relevant tests
$ renee test tests/combat.test.yaml

# 5. Interactive testing
$ renee repl scenes/level_1.yaml
> spawn Goblin at 3,3
> do attack target=2
> inspect entity 2
```

### AI-Assisted Development

```bash
# Get context before asking AI to make changes
$ renee context --task "add entity" --entity "Necromancer"

# After AI creates file
$ renee validate entities/necromancer.yaml
$ renee test

# Check balance
$ renee analyze balance
$ renee simulate combat --entity necromancer --iterations 50
```
