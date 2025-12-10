# Renee Development Patterns

**Copyable patterns for AI agents**

See [DESIGN.md](DESIGN.md) for strategic architecture

---

## Why Pattern-First Documentation?

Traditional documentation explains concepts, then shows code. **AI-native documentation inverts this**: show the pattern first, explain second.

### Why This Order Matters

1. **Template first** — AI can immediately copy and modify
2. **Required changes as checklist** — AI knows exactly what to edit
3. **Validation command** — AI can verify its work
4. **Expected results** — AI can check if output matches intent
5. **Reference values** — AI has concrete numbers, not vague descriptions

---

## PATTERN: Adding a New Enemy

### 1. Copy This Template

```yaml
# entities/YOUR_ENEMY.yaml

name: YOUR_ENEMY_NAME
description: "One-line description"
intent: |
  Design goals:
  - Difficulty level (early/mid/late game)
  - Role (swarm, tank, glass cannon, etc.)
  - Special behaviors

tags: [enemy, creature, YOUR_TAGS]

components:
  Position: {}
  Health:
    current: 20  # Adjust for difficulty
    max: 20
  Combat:
    attack: 8    # Adjust for difficulty
    defense: 2   # Adjust for difficulty
  AI:
    behavior: aggressive
  Sprite:
    idle: your_sprite_idle
```

### 2. Required Changes (in order)

| Line | Field | What to Change |
|------|-------|----------------|
| 3 | `name` | Unique entity name |
| 4 | `description` | Flavor text |
| 5-9 | `intent` | Design goals for AI to check against |
| 11 | `tags` | Add relevant tags |
| 16-17 | `Health` | Set HP based on difficulty tier |
| 19-21 | `Combat` | Set attack/defense based on role |
| 23 | `AI.behavior` | Choose: aggressive, defensive, patrol |
| 25 | `Sprite.idle` | Reference to sprite asset |

### 3. Validate

```bash
renee validate entities/your_enemy.yaml
```

### 4. Test Combat Balance

```bash
renee simulate combat --entity YourEnemy --vs Player --iterations 100
```

Expected results for early game enemy:
- Player win rate: > 90%
- Average turns to defeat: 2-3
- Player health remaining: > 50%

### 5. Reference Values

| Tier | HP | Attack | Defense | Player Wins |
|------|----|--------|---------|-------------|
| Early | 15-25 | 5-10 | 0-3 | >90% |
| Mid | 30-50 | 12-18 | 3-6 | 70-85% |
| Late | 60-100 | 20-30 | 8-12 | 50-70% |
| Boss | 150+ | varies | varies | 40-60% |

---

## PATTERN: Adding a New System

### 1. Copy This Template

[Template to be filled in]

### 2. Required Changes

[Changes checklist to be filled in]

### 3. Validate

[Validation command to be filled in]

### 4. Test

[Testing approach to be filled in]

### 5. Reference Values

[Reference values table to be filled in]

---

## PATTERN: Adding a New Rule

### 1. Copy This Template

[Template to be filled in]

### 2. Required Changes

[Changes checklist to be filled in]

### 3. Validate

[Validation command to be filled in]

### 4. Test

[Testing approach to be filled in]

### 5. Reference Values

[Reference values table to be filled in]

---

## PATTERN: Creating a Scene

### 1. Copy This Template

[Template to be filled in]

### 2. Required Changes

[Changes checklist to be filled in]

### 3. Validate

[Validation command to be filled in]

### 4. Test

[Testing approach to be filled in]

### 5. Reference Values

[Reference values table to be filled in]

---

## Anti-Pattern: Human-Style Documentation

```markdown
# ❌ DON'T: Concept-first documentation

## Understanding the Entity System

The Entity-Component-System (ECS) architecture separates data from behavior.
Entities are unique identifiers, components are pure data, and systems
contain logic. This approach offers several benefits...

[500 words of explanation]

## Creating Entities

To create an entity, you'll need to understand the component schemas first.
Let's explore each component type...

[300 more words before showing any code]
```

This wastes AI context on concepts it likely already knows. **Show the pattern. Let AI ask if it needs explanation.**

---

## Documentation Format Guidelines

When adding new patterns to this document:

1. Lead with a copyable template (YAML, code, or configuration)
2. Provide a numbered checklist of required changes
3. Include a validation or testing command
4. Show expected results or success criteria
5. Provide reference values for common scenarios

This format enables AI agents to work efficiently and autonomously while maintaining code quality and consistency.
