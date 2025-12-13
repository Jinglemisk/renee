# Renee: An AI-Native Game Framework

## Design Document v3.0

---

# Executive Summary

**Renee** is a turn-based game framework designed from the ground up for AI-assisted development. Unlike traditional game engines that assume human developers reading documentation and clicking through GUIs, Renee assumes your co-developer is an AI coding agent.

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

### Genre Agnosticism

Renee is a **framework**, not a game template. It provides primitives for turn-based games of any genre:

| Genre | Example Games | Renee Provides |
|-------|--------------|----------------|
| Tactics/Strategy | Chess, Fire Emblem, XCOM | Grid, pathfinding, turn order |
| Card Games | Poker, Hearthstone, Slay the Spire | Zones, state machines, hidden information |
| Board Games | Catan, Monopoly, Ticket to Ride | Resource tracking, player rotation |
| RPG/Dungeon | Darkest Dungeon, Into the Breach | Entity stats, event-driven combat |
| Puzzle | Baba Is You, Into the Breach | Rule composition, state validation |

The framework defines **no game-specific components**. Components like "Health", "Mana", "Cards", or "Resources" are defined by the game developer, not the framework.

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
| **Schema Registry** | Runtime-queryable type definitions | AI asks "what fields does this component have?" and gets an answer |
| **Intent Fields** | Natural language descriptions on entities | AI compares implementation against stated goals |
| **`--json` on Everything** | Machine-parseable output from all commands | AI reliably parses structured responses |
| **Spatial Reasoning Helpers** | Grid utilities, pathfinding, LOS APIs | AI doesn't need to implement A* from scratch |
| **Asset Management** | Validated asset manifest with constants | Type-safe asset references, no magic strings |
| **Impact Analysis** | Shows change effects with intent validation | AI knows what breaks before making changes |
| **Simulation** | Test hypothetical changes with statistics | AI experiments with balance safely |
| **Snapshot/Rollback** | First-class state snapshots | AI tries, evaluates, undoes freely |
| **REPL with JSON Mode** | Interactive game manipulation | AI experiments, observes, iterates |
| **Event Sourcing** | Complete history of everything that happened | AI debugs by reading the past |
| **Python Rule System** | Game logic as Python decorators, NOT DSL | AI writes rules in familiar Python |
| **Render Commands** | Abstract output, pluggable renderers | AI tests games without graphics |
| **Multiplayer Support** | Local, network, and async play | Turn-based games are inherently social |

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
│  │   Action    │  │    Turn     │  │   Spatial   │             │
│  │  Pipeline   │  │   Manager   │  │   Helpers   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Asset     │  │   Replay    │  │    REPL     │             │
│  │  Registry   │  │   System    │  │  Interface  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐                              │
│  │    Rule     │  │ Multiplayer │                              │
│  │   Engine    │  │   Layer     │                              │
│  └─────────────┘  └─────────────┘                              │
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
│    Pygame    │  │   Terminal   │  │   Headless   │
│   Renderer   │  │   Renderer   │  │   Renderer   │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Key Architectural Decisions

### 1. Headless Core, Pluggable Renderers

The framework produces **render commands**, not pixels. Render commands are abstract instructions that any renderer can interpret:

- `clear` — Fill screen with color
- `draw_sprite` — Draw an image at position
- `draw_rect` — Draw a rectangle (for UI elements)
- `draw_text` — Render text
- `draw_tilemap` — Render a tile-based map
- `draw_particles` — Render particle effects

**Why this matters:**
- AI can run games without any graphics (headless testing)
- Same game runs on desktop, terminal, web, mobile
- Framework focuses purely on game logic
- Render commands are inspectable (AI can verify what's being drawn)

### 2. Entity Component System (ECS)

**Core Structure:**
- **Entities** are IDs (just numbers)
- **Components** are pure data attached to entities
- **Systems** are isolated logic that processes entities

The framework provides the ECS infrastructure. Games define their own components.

**Why ECS Matters for AI:**
- Flat structure (no deep inheritance to trace)
- Components are readable data (not hidden in object state)
- Systems are isolated (modify one without understanding others)
- Easy to query: "give me all entities with ComponentA and ComponentB"

### 3. Event Sourcing for Complete History

The game is a sequence of events, not mutable state. Every action, state change, and outcome is recorded.

**Why This Matters for AI:**
- Complete history is always available
- Debugging = "find the event that caused bad state"
- Replay by re-processing events
- AI can ask "what happened on turn 5?"

### 4. Performance Architecture: Pydantic at Boundaries

**The Problem:** Pydantic validation on every entity operation is slow.

**The Solution:** Use Pydantic only at boundaries (loading/saving), convert to plain dataclasses for runtime. Validate once on load, use fast objects during gameplay.

---

# Part 2: Semantic Types

The framework provides semantic types beyond Python primitives. These types carry meaning and enable validation:

| Type | Description | Example Use |
|------|-------------|-------------|
| `EntityId` | Reference to an entity (int at runtime) | Target of an action |
| `AssetRef` | Validated reference to an asset | Sprite name, sound effect |
| `Probability` | Float constrained to 0.0-1.0 | Critical hit chance |
| `Position` | Grid coordinate (x, y) | Entity location |
| `DiceRoll` | Parsed dice notation (e.g., "2d6+3") | Damage calculation |
| `Duration` | Time measurement in game units | Effect duration |
| `Formula` | Runtime-evaluated expression | Scaling calculations |

These types:
- Self-document what values represent
- Enable schema validation
- Provide parsing utilities (e.g., dice notation)
- Help AI understand data meaning

---

# Part 3: The Intent System (Key Innovation)

## Why Intent Fields Matter

LLMs struggle with "grounding" — connecting high-level concepts ("make it hard") to low-level integers (`hp: 500`).

The `intent` field treats design goals as testable contracts.

## How Intent Works

Every entity, rule, or system can have an `intent` field describing:
- What it should accomplish
- How it should feel
- Target metrics (if applicable)
- Design constraints

AI agents can:
1. Read the intent to understand design goals
2. Run simulations to measure actual behavior
3. Identify mismatches between intent and implementation
4. Suggest adjustments to align with stated goals

**Without intent:** AI must guess what "too easy" or "balanced" means.
**With intent:** AI has explicit design goals to validate against.

## Intent Validation in Impact Analysis

When analyzing potential changes, the framework compares:
- What the intent says should happen
- What simulation shows will happen
- Whether the change violates stated goals

---

# Part 4: Core Systems

## Schema Registry

Runtime-queryable type definitions that allow the framework to describe itself.

**Capabilities:**
- Register component and event schemas from YAML
- Query schema by name
- List all schemas (optionally filtered by type)
- Validate data against schema
- Get default values
- Introspect field definitions, constraints, and invariants

**Why This Matters:**
AI asks "what fields does this component have?" and gets an authoritative answer. No guessing, no documentation searching.

---

## ECS World

The World manages all entities and their components.

**Core Operations:**
- Create and destroy entities
- Add, remove, get, and check components
- Query entities by component types and/or tags
- Spawn entities from templates with overrides

**Snapshot/Rollback (First-Class Feature):**
- Save complete world state as a snapshot
- Restore to a previous snapshot
- Essential for AI experimentation: try an approach, see if it works, roll back if not

**Entity Lifecycle Hooks:**
- `on_spawn` — Called when entity is created
- `on_destroy` — Called when entity is removed
- Enables automatic setup and cleanup

---

## Event Bus

Event emission, subscription, and history.

**Core Operations:**
- Emit events with automatic metadata (turn, timestamp, id)
- Subscribe handlers to event types
- Query event history (by type, turn, entity, custom filter)
- Clear history when needed

**Why Events Matter:**
Events are the audit trail. They enable replay, debugging, and AI analysis of what happened.

---

## Action Pipeline

Actions flow through a pipeline: Request → Validation → Rules → Execution → Events.

**Pipeline Stages:**
1. **Request** — Action is requested with parameters
2. **Validation** — Parameters checked against schema
3. **Pre-Rules** — Rules can modify or cancel the action
4. **Execution** — Action handler runs if not cancelled
5. **Post-Rules** — Rules react to completed action
6. **Events** — Completion event emitted

**Action Context:**
Rules receive a context object allowing them to:
- Inspect action parameters
- Access world state
- Modify action parameters
- Cancel the action with a reason

---

## Rule Engine

Rules are Python functions with decorators, **NOT custom YAML DSL**.

**Why Python, Not DSL:**
- AI agents are trained on billions of lines of Python
- Almost zero training on custom YAML DSLs
- Python provides IDE support, debugging, type checking for free
- No need to build expression parser, AST evaluator, function registry

**Rule Properties:**
- Phase: pre or post action execution
- Priority: execution order within phase
- Condition: when the rule applies

---

## Turn Manager

Flexible, game-defined time structure.

**Key Concepts:**

**TimeStructure:** Hierarchical definition of time (e.g., Round → Turn → Phase)

**TimeUnit:** A single level in the hierarchy

**Phase:** A segment within a turn with specific behaviors

**Traits:** Composable behaviors for phases:
- Skippable — Can be passed
- Mandatory — Must complete
- Timed — Has time limit
- Unlimited actions — No action limit
- Single action — One action then auto-advance

**Turn Order Strategies:**
- Alternating (two players)
- Clockwise (multiplayer board game)
- Initiative-based (RPG style)
- Simultaneous (all players act, then resolve)
- Custom (game-defined)

Games define their own turn structure. The framework provides the infrastructure.

---

## Spatial Reasoning Helpers

AI is notoriously bad at 2D grids, pathfinding, and spatial calculations. The framework provides battle-tested utilities:

**Grid Operations:**
- Create grids of arbitrary size
- Mark tiles as blocked/unblocked
- Query tile properties

**Pathfinding:**
- A* pathfinding between positions
- Respects obstacles

**Visibility:**
- Line-of-sight checking
- Handles blocking terrain

**Area Queries:**
- Tiles within range (Manhattan, Euclidean)
- Tiles in cone/arc
- Tiles in rectangle
- Entities at position

**Why This Matters:**
Don't make AI implement A* from scratch. It will get it wrong. Provide utilities.

---

## Asset Management System

**The Problem:** Magic strings are error-prone. AI has to guess valid asset names.

**The Solution:**
- Auto-generated asset manifest from scanning directories
- Generated Python constants for type-safe references
- Validation of asset references in entities

AI doesn't have to guess. Constants are validated. IDEs provide autocomplete.

---

## Input System

Maps raw input to game actions.

**Core Concept:**
Input bindings translate physical input (keyboard, mouse, controller) to logical actions. This decouples input handling from game logic.

**Binding Configuration:**
Bindings are defined in YAML, allowing easy remapping without code changes.

---

# Part 5: Multiplayer Architecture

Turn-based games are inherently social. Multiplayer is a first-class concern, not an afterthought.

## Multiplayer Modes

### Local Multiplayer (Hot-Seat)
Multiple players share one device, taking turns. The simplest mode:
- Single game instance
- Turn manager handles player rotation
- No networking required

### Network Multiplayer
Players on different devices connected via network:
- Client-server or peer-to-peer architecture
- State synchronization via events
- Turn validation on authoritative source
- Handles disconnection and reconnection

### Asynchronous Multiplayer
Players don't need to be online simultaneously:
- Game state persisted between sessions
- Notification when it's your turn
- Supports very long games (play-by-email style)

## Architecture Principles

**Event-Based Synchronization:**
Since games are event-sourced, multiplayer sync is sending events:
- Local player takes action → Action event generated
- Event sent to other players/server
- Other clients apply event to their state
- All clients converge to same state

**Turn Validation:**
Server (or designated authority) validates:
- Is it this player's turn?
- Is the action legal?
- Are the parameters valid?

**Hidden Information:**
Some games require hidden information (hands of cards, fog of war):
- Server maintains complete state
- Clients receive filtered state
- Framework supports partial state views

---

# Part 6: Rendering System

## Render Command Protocol

The framework outputs render commands as a list of operations. Each command has a `type` and associated parameters.

**Command Types:**

| Type | Purpose | Key Parameters |
|------|---------|----------------|
| `clear` | Fill screen with color | color |
| `draw_sprite` | Draw image at position | sprite, x, y, flip_x, flip_y |
| `draw_rect` | Draw rectangle | x, y, w, h, color |
| `draw_text` | Render text | text, x, y, size, color |
| `draw_tilemap` | Render tile map | tilemap, offset_x, offset_y |
| `draw_image` | Draw background image | image, x, y, parallax |
| `draw_particles` | Render particle system | system, particles |

## Renderer Interface

Renderers implement a standard interface:
- `initialize(config)` — Setup (create window, load assets)
- `render(commands)` — Process render commands
- `get_input()` — Get current input state
- `shutdown()` — Cleanup resources

## Renderer Types

**Pygame Renderer:** Primary renderer for desktop games with graphics.

**Terminal Renderer:** ASCII-based rendering for debugging or terminal games.

**Headless Renderer:** No visual output—stores commands for inspection. Essential for automated testing and AI simulation.

---

# Part 7: AI-Native Tooling

## CLI Design Principles

1. **Every command has `--json` flag** — Machine-parseable output
2. **Structured output, not prose** — Consistent format
3. **Exit codes: 0 = success, 1 = error** — Scriptable
4. **Predictable output format** — AI can rely on structure

## Core Commands

**Project Management:**
- Create new project with scaffolding
- Validate files against schemas
- Run game

**Introspection:**
- List and show schemas
- Query game state
- Get info about entities, components, rules

**AI-Native:**
- Impact analysis for proposed changes
- Simulations for balance testing
- Context generation for common tasks
- REPL for interactive exploration

## Impact Analysis

Shows what breaks when you make a change, with intent validation.

**Output includes:**
- Affected files
- Affected rules
- Intent violations (if change conflicts with stated goals)
- Simulation results (before/after comparison)

**Why This Matters:**
AI knows what breaks *before* making changes. Intent validation ensures changes align with design goals.

## Simulation Engine

Run hypothetical scenarios with statistical analysis.

**Capabilities:**
- Run scenarios N times with different seeds
- Compare baseline vs. modified state
- Sweep parameter ranges
- Statistical output (averages, distributions)

**Why This Matters:**
AI can experiment with balance safely. "What if I change this value?" gets a numerical answer.

## REPL Interface

Interactive game manipulation for experimentation.

**Modes:**
- Standard mode: Human-readable output
- JSON mode: Machine-parseable for AI agents

**Why This Matters:**
AI can experiment interactively, see results immediately, iterate quickly.

---

# Part 8: File Structure

## Directory Layout

```
my_game/
├── game.yaml                    # Project manifest
├── schemas/                     # Type definitions
│   ├── components.yaml          # Component schemas
│   ├── events.yaml              # Event schemas
│   └── actions.yaml             # Action schemas
├── entities/                    # Entity templates
│   └── _templates/              # Canonical examples for AI
├── systems/                     # Game logic (Python)
├── rules/                       # Rules (Python decorators)
├── scenes/                      # Level/map definitions
├── assets/                      # Game assets
│   ├── sprites/
│   ├── sounds/
│   ├── fonts/
│   └── manifest.yaml            # Auto-generated asset registry
└── tests/                       # pytest tests
```

## File Naming Conventions

- `*.yaml` — Data definition
- `*.py` — Logic/behavior
- `_templates/` — Canonical examples for AI to copy
- `_` prefix — Internal/private

**Why Rigid Conventions Matter:**
AI agents pattern-match. Absolute conventions enable reliable automation.

## Template Directory Pattern

Templates have TODO markers for AI to fill in. This provides:
- Starting structure
- Clear indication of what needs customization
- Consistent patterns across a project

---

# Part 9: Design Principles

## 1. Everything is Text

- No binary formats
- YAML for data, Python for logic
- JSON for state export
- AI can read, modify, understand everything

## 2. Everything is Introspectable

The framework can describe itself:
- Query schemas
- Query state
- Query history
- AI always has access to authoritative information

## 3. Everything is Declarative

Describe *what*, not *how*:
- Entity definitions declare structure
- Schemas declare constraints
- Intent fields declare goals
- Framework handles implementation

## 4. Everything is Predictable

- Rigid file naming conventions
- Consistent directory structure
- Explicit patterns (templates with TODOs)
- No "magic" behavior

## 5. Provide Unique Insights

Build features that give AI insights it can't derive on its own:
- ✅ Simulation (run many iterations, get statistics)
- ✅ Intent validation (check implementation matches goals)
- ✅ Schema introspection (query component fields)
- ✅ Impact analysis (what breaks if I change this?)
- ❌ Context prediction (AI can grep)
- ❌ Semantic code understanding (AI can read)

## 6. Literate Error Messages

Every error explains **what**, **why**, and **how to fix**:
- What happened
- Why it failed
- Options to resolve

AI agents can parse structured errors and take corrective action without guessing.

---

# Part 10: Testing and Validation

## pytest Integration (Not Custom DSL)

Tests use standard pytest. AI agents already know pytest; no custom DSL needed.

**Test fixtures** set up game state for testing.
**Assertions** verify behavior matches intent.

## Deterministic Seeding

All randomness goes through framework's RNG for reproducibility:
- Set seed for reproducible tests
- Use framework RNG, not Python's random module

**Why This Matters:**
Tests are deterministic. AI can reproduce bugs reliably.

---

# Appendix A: What NOT to Build

## Avoid These Traps

### 1. Custom YAML Rule DSL
Python decorators work better. AI knows Python. Custom DSLs require parsers, have poor error messages, and have no training data.

### 2. Custom Test DSL
Use pytest. It's familiar, well-tooled, and AI-friendly.

### 3. Complex AI-Powered Context Prediction
Simple keyword-based commands work better than embeddings/vector search. Don't over-engineer.

### 4. Game-Specific Builtins
The framework provides infrastructure, not game content. Components, actions, and rules are defined by games, not hardcoded in the framework.

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
4. JSON output support

## Why Pygame?
1. Simple, well-documented
2. Pure Python (no compilation)
3. Battle-tested
4. AI training corpus includes many pygame examples

---

# Appendix C: Key Innovations Summary

1. **Intent Fields** — Natural language design goals that AI can validate against
2. **Python Decorators for Rules** — No custom DSL, use Python directly
3. **Snapshot/Rollback as First-Class** — AI experimentation is core, not afterthought
4. **Schema Registry** — Framework describes itself to AI
5. **`--json` on Everything** — Structured output for AI parsing
6. **Spatial Reasoning Helpers** — Don't make AI implement algorithms from scratch
7. **Asset Management** — Constants over magic strings
8. **Impact Analysis with Intent** — Know what breaks AND why
9. **Event Sourcing** — Complete history for debugging and replay
10. **Multiplayer as First-Class** — Turn-based games are social
11. **Genre Agnosticism** — Framework provides primitives, games define content

---

*This document is the source of truth for Renee. When in doubt, refer here.*
