# Renee Framework Documentation

Welcome to the Renee documentation. Renee is an AI-native turn-based game framework designed from the ground up for AI-assisted development.

## Documentation Index

### Primary Documentation (Start Here)

| Document | Purpose | Read When |
|----------|---------|-----------|
| **[DESIGN.md](DESIGN.md)** | Strategic design & architecture | Understanding Renee's philosophy, core systems, and design principles |
| **[TUTORIAL.md](TUTORIAL.md)** | Step-by-step game building guide | Building your first Renee game |
| **[PATTERNS.md](PATTERNS.md)** | Copyable patterns for AI agents | Adding entities, systems, rules, or scenes |
| **[CLI.md](CLI.md)** | Complete command reference | Looking up command syntax and options |
| **[RENDERING.md](RENDERING.md)** | Render command specification | Building custom renderers or understanding the render pipeline |
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | Packaging & distribution guide | Shipping your game to players |

### Supporting Documentation

| Document | Purpose |
|----------|---------|
| **[sysprompt.md](sysprompt.md)** | System prompt for Indy (AI development partner) |
| **[ai-engine-ORIGINAL.md](ai-engine-ORIGINAL.md)** | Original exhaustive design document (archived) |
| **[renee-engine-DRAFT.md](renee-engine-DRAFT.md)** | Intermediate draft before final DESIGN.md split (archived) |

---

## Quick Start Path

**For AI Agents Building Games:**
1. Read [DESIGN.md](DESIGN.md) - Understand architecture and principles
2. Follow [TUTORIAL.md](TUTORIAL.md) - Build your first game
3. Use [PATTERNS.md](PATTERNS.md) - Copy patterns for entities, systems, rules
4. Reference [CLI.md](CLI.md) - Look up commands as needed
5. Consult [DEPLOYMENT.md](DEPLOYMENT.md) - Ship when ready

**For Humans Understanding Renee:**
1. Read [DESIGN.md](DESIGN.md) Executive Summary - Get the big picture
2. Read [DESIGN.md](DESIGN.md) Part 1-3 - Understand core architecture
3. Follow [TUTORIAL.md](TUTORIAL.md) - Build a game to cement understanding
4. Read [DESIGN.md](DESIGN.md) Part 7-9 - Understand innovations and principles

**For AI Agents Contributing to Renee:**
1. Read [sysprompt.md](sysprompt.md) - Understand project context and goals
2. Read [DESIGN.md](DESIGN.md) completely - Understand all architectural decisions
3. Reference [PATTERNS.md](PATTERNS.md) - Follow established patterns

---

## Document Relationship

```
DESIGN.md (Strategic Architecture)
    ├── References → CLI.md (Command details)
    ├── References → RENDERING.md (Render specs)
    ├── References → TUTORIAL.md (Practical learning)
    ├── References → PATTERNS.md (Copyable examples)
    └── References → DEPLOYMENT.md (Distribution)

TUTORIAL.md (Learning Path)
    ├── Uses → PATTERNS.md (Entity/scene patterns)
    └── Uses → CLI.md (Command execution)

sysprompt.md (AI Agent Context)
    └── Points to → DESIGN.md (Source of truth)
```

---

## What's Different About Renee?

Renee is **AI-native**, meaning it's designed for AI coding agents to:
1. **Understand** - Everything is text, introspectable, with explicit schemas
2. **Modify** - Clear patterns, validation, and impact analysis
3. **Experiment** - Simulation, snapshot/rollback, REPL with JSON mode
4. **Verify** - Intent fields, automated testing, balance simulation

Traditional game engines were built for humans with GUIs and binary formats. Renee is built for AI agents with text configs, JSON output, and structured introspection.

---

## Core Innovations

1. **Intent Fields** - Natural language design goals that AI validates against implementation
2. **Python-Only Rules** - No custom DSL, AI writes game logic in Python
3. **Spatial Reasoning Helpers** - Grid utilities, pathfinding, LOS (AI is bad at 2D math)
4. **Asset Management** - Constants over magic strings (`Assets.Sprites.GOBLIN` vs `"goblin"`)
5. **Impact Analysis** - Know what breaks before making changes
6. **`--json` on Everything** - Every command outputs machine-parseable JSON

See [DESIGN.md](DESIGN.md) for complete details.

---

## File History

- **ai-engine-ORIGINAL.md** - Original exhaustive document (4079 lines) that tried to be design doc + implementation spec + reference manual all in one
- **renee-engine-DRAFT.md** - Refined version (1437 lines) incorporating architectural critique, focused on strategic design
- **DESIGN.md** - Final strategic design document with document map and complete example
- **CLI.md, RENDERING.md, TUTORIAL.md, PATTERNS.md, DEPLOYMENT.md** - Implementation details extracted into focused documents

The split follows best practices: one strategic document (DESIGN.md) with separate focused documents for implementation details.

---

*Last Updated: 2025-12-08*
