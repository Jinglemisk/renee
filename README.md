<div align="center">

<img src="renee.jpeg" alt="Renee" width="35%" />

# Renee

</div>

Renee is a genre-agnostic framework for turn-based games designed specifically for AI-assisted development, prioritizing machine-parseable architecture and standard Python logic over traditional human-centric GUIs. It facilitates autonomous code generation and testing through self-describing schemas, intent-based validation, and deterministic simulation tools like snapshotting and rollbacks. 

Traditional game engines assume human developers with GUIs and documentation. Renee assumes your co-developer (or even the only developer) is an AI coding agent.

## Documentation

**[DESIGN.md](DESIGN.md)** is the source of truth. It covers:
- Architecture and core systems
- Design principles and philosophy
- All major subsystems (ECS, Events, Rules, Turn Management, etc.)
- Multiplayer architecture
- AI-native tooling

## Key Differentiators

**AI-Native means "AI can derive insights it couldn't get elsewhere"**

| Feature | Why It Matters |
|---------|----------------|
| Intent Fields | AI validates implementation against stated design goals |
| Schema Registry | Framework describes itself—AI asks "what fields?" and gets answers |
| `--json` on Everything | Machine-parseable output for reliable AI interaction |
| Simulation Engine | AI experiments with balance safely |
| Snapshot/Rollback | AI tries, evaluates, undoes freely |
| Python Rules | No custom DSL—AI writes logic in Python it already knows |

## Genre Agnostic

Renee provides primitives. Games define content.

Works for: Chess, card games, tactics RPGs, board games, strategy games, puzzle games—any turn-based genre.

# Current Status 15.12.2025
- I took the liberty of having both GPT-5.2-xhigh and Opus-4.5-Ultrathink in parallel and autonomously.
-- Claude: Wrote 2x more code than Codex, but it heavily diverged from the design document.
-- GPT: Implemented a much narrower scope but the framework was largely aligned with the design document.
- Now I am in the process of merging these. 