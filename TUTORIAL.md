# Building Your First Renee Game

> **Before you start:** See [DESIGN.md](DESIGN.md) for strategic architecture and [CLI.md](CLI.md) for commands reference.

Let's walk through building **Dungeon Crawl** - a simple turn-based dungeon crawler. This tutorial will teach you the core concepts of the Renee game engine by building a complete working example from scratch.

## Step 1: Project Setup

Start by creating a new Renee project:

```bash
$ renee new dungeon_crawl
$ cd dungeon_crawl
```

This scaffolds a basic project structure with directories for entities, rules, scenes, and tests.

## Step 2: Define Core Entities

Entities are the building blocks of your game. Let's define the Player, a basic enemy (Goblin), and a collectible (Gold Coin).

### Player Entity

```yaml
# entities/player.yaml

name: Player
description: "The hero exploring the dungeon"
intent: |
  The player-controlled character. Should feel powerful but vulnerable.
  - Can take 3-4 hits from basic enemies before dying
  - Defeats basic enemies in 2-3 hits
  - Has limited inventory for strategic decisions
  - Starts weak but can find equipment to improve

tags: [player, hero, controllable]

components:
  Position: {}

  Health:
    current: 50
    max: 50

  Combat:
    attack: 12
    defense: 3
    attack_range: 1

  Inventory:
    items: []
    capacity: 5

  Sprite:
    idle: hero_idle
    walk: hero_walk
    attack: hero_attack
    hurt: hero_hurt
    death: hero_death

on_spawn:
  - emit: {event: "player_spawned"}

on_death:
  - emit: {event: "player_died"}
  - emit: {event: "game_over", data: {result: "defeat"}}
```

**What's happening here:**
- **Components** define what the Player can do (move, take damage, fight, carry items)
- **Health** tracks HP (current out of max)
- **Combat** defines attack and defense stats
- **Inventory** limits what the player can carry
- **on_spawn/on_death** hooks trigger when events happen

### Goblin Enemy

```yaml
# entities/goblin.yaml

name: Goblin
description: "A small, green-skinned creature with a rusty dagger"
intent: |
  Basic early-game enemy. Teaches combat without being threatening.
  - Player should defeat in 2 hits
  - Deals ~10 damage per hit (5 hits to kill player)
  - No special abilities
  - Drops gold occasionally

tags: [enemy, creature, melee, early_game]

components:
  Position: {}

  Health:
    current: 20
    max: 20

  Combat:
    attack: 10
    defense: 2
    attack_range: 1

  AI:
    behavior: aggressive
    detection_range: 5

  Sprite:
    idle: goblin_idle
    walk: goblin_walk
    attack: goblin_attack
    hurt: goblin_hurt
    death: goblin_death

on_death:
  - emit: {event: "enemy_killed", data: {type: "goblin", xp: 10}}
  - chance: 0.5
    spawn: {type: "GoldCoin", at: "self.position"}
```

**Key differences:**
- Enemies have an **AI** component for autonomous behavior
- The **intent** field documents design goals (very important for AI collaboration!)
- **on_death** spawns loot with a 50% chance
- **attack_range** of 1 means melee only

### Gold Coin Collectible

```yaml
# entities/gold_coin.yaml

name: GoldCoin
description: "A shiny gold coin"
intent: |
  Basic collectible. Rewards exploration and combat.
  - Automatically collected on contact
  - Worth 10 gold
  - Satisfying pickup (sound + particles)

tags: [collectible, treasure, auto_pickup]

components:
  Position: {}

  Collectible:
    type: gold
    value: 10
    auto_pickup: true

  Sprite:
    idle: coin_spin

on_collect:
  - modify_state: {path: "global.gold", add: 10}
  - emit: {event: "gold_collected", data: {amount: 10}}
  - emit: {event: "play_sound", data: {sound: "coin_pickup"}}
  - destroy: self
```

**What's special:**
- **auto_pickup** means the player collects it just by touching it
- **on_collect** hooks add gold to the global state and play a sound
- Very simple entity - just position and collectible mechanics

## Step 3: Define Rules

Rules are the "game logic" layer - they handle combat resolution, win conditions, and other system-level mechanics.

### Combat Rules

```yaml
# rules/combat.yaml

rules:
  - id: basic_melee_attack
    description: "Standard melee attack resolution"
    when:
      - "action.type == 'melee_attack'"
      - "distance(source.Position, target.Position) <= source.Combat.attack_range"
    then:
      - calculate:
          name: damage
          formula: "max(1, source.Combat.attack - target.Combat.defense)"
      - modify: "target.Health.current"
        subtract: "damage"
      - emit:
          event: "damage_dealt"
          data: {source: "source.id", target: "target.id", amount: "damage"}

  - id: death_check
    description: "Destroy entities at 0 or less health"
    when:
      - "entity.Health.current <= 0"
    then:
      - emit: {event: "entity_died", data: {entity: "entity.id"}}
      - trigger: "entity.on_death"
      - destroy: "entity"
```

**How combat works:**
1. When a melee attack action happens AND the target is within range
2. Calculate damage = attacker's attack minus defender's defense (min 1)
3. Subtract damage from target's health
4. Emit an event so other systems know damage happened

**Death check:**
- Whenever any entity hits 0 HP, trigger their `on_death` hooks
- Then remove the entity from the game world

### Win Condition Rules

```yaml
# rules/win_conditions.yaml

rules:
  - id: reach_exit
    description: "Win by reaching the dungeon exit"
    when:
      - "event.type == 'tile_entered'"
      - "event.entity == player"
      - "event.tile_type == 'exit'"
    then:
      - emit: {event: "level_complete"}
      - modify_state: {path: "scene.completed", set: true}

  - id: player_death
    description: "Lose when player dies"
    when:
      - "event.type == 'entity_died'"
      - "event.entity == player"
    then:
      - emit: {event: "game_over", data: {result: "defeat"}}
```

**Victory condition:** Touch the exit tile to win.
**Defeat condition:** Die and it's game over.

## Step 4: Create a Scene

A scene is a playable level - it has a tilemap, entity spawns, and optional scene-specific rules.

```yaml
# scenes/level_1.yaml

name: "Dungeon Entrance"
description: "The first level - learn the basics"
intent: |
  Tutorial level that teaches:
  - Movement
  - Combat (1 goblin)
  - Collecting items (health potion)
  - Reaching the exit
  Should be completable in 1-2 minutes.

tilemap:
  width: 10
  height: 8
  tiles: |
    ##########
    #........#
    #..G.....#
    #........#
    #....H...#
    #........#
    #@......E#
    ##########
  legend:
    "#": wall
    ".": floor
    "@": player_spawn
    "G": goblin_spawn
    "H": health_potion_spawn
    "E": exit

entities:
  - type: Player
    id: player
    spawn_at: player_spawn

  - type: Goblin
    id: goblin_1
    spawn_at: goblin_spawn

  - type: HealthPotion
    id: potion_1
    spawn_at: health_potion_spawn

initial_state:
  enemies_defeated: 0
  items_collected: 0

rules:
  - id: tutorial_hint_combat
    description: "Show combat hint when near goblin"
    when:
      - "distance(player.Position, goblin_1.Position) <= 3"
      - "not 'combat_hint' in state.hints_shown"
    then:
      - emit: {event: "show_hint", data: {text: "Press SPACE to attack!"}}
      - modify_state: {path: "scene.hints_shown", append: "combat_hint"}
```

**Breaking it down:**

- **Tilemap:** 10x8 grid with walls (#), walkable floor (.), spawn points (@, G, H), and exit (E)
- **Entities:** Spawn instances of Player, Goblin, and HealthPotion at their marked positions
- **initial_state:** Starting values for scene variables
- **rules:** Scene-specific logic (like tutorial hints)

This level is designed to be completable in 1-2 minutes - a perfect tutorial.

## Step 5: Write Tests

Tests verify that your game works as designed. Renee uses standard pytest with custom fixtures for game simulation.

```yaml
# tests/level_1.test.yaml

name: "Level 1 Tests"

tests:
  - name: "Player can complete level"
    setup:
      load_scene: level_1
    steps:
      # Move toward goblin
      - do: {action: move, direction: up}
      - do: {action: move, direction: up}
      - do: {action: move, direction: up}
      - do: {action: move, direction: up}
      # Fight goblin
      - do: {action: move, direction: right}
      - do: {action: move, direction: right}
      - do: {action: attack, target: goblin_1}
      - do: {action: attack, target: goblin_1}
      - assert: goblin_1 not in entities
      # Get potion and exit
      - do: {action: move, direction: right}
      - do: {action: move, direction: right}
      - do: {action: move, direction: down}
      - do: {action: move, direction: down}
      - repeat: 5
        do: {action: move, direction: right}
      - assert: event_emitted("level_complete")

  - name: "Goblin dies in 2 hits"
    intent: "Verify goblin matches design intent"
    setup:
      load_scene: test_arena
      spawn:
        - {type: Player, id: player, position: {x: 0, y: 0}}
        - {type: Goblin, id: goblin, position: {x: 1, y: 0}}
    steps:
      - do: {action: attack, target: goblin}
      - assert: goblin.Health.current == 10  # 20 - (12 - 2)
      - do: {action: attack, target: goblin}
      - assert: goblin not in entities
```

**Test 1: Full Level Completion**
- Sets up the complete level
- Simulates the player moving, fighting, collecting items, and winning
- Verifies the level_complete event is emitted

**Test 2: Combat Balance**
- Tests in isolation that damage calculation matches design intent
- Goblin has 20 HP, takes 10 damage per hit (player attack 12 - goblin defense 2)
- Verifies it dies on the 2nd hit, as intended

## Step 6: Run and Test

Now let's see it all work together:

### Validate All Files

```bash
$ renee validate
All files valid.
```

This checks that:
- All YAML is syntactically correct
- Entity references exist
- Scenes reference valid entities
- Rules don't have obvious errors

### Run Tests

```bash
$ renee test
Running tests...
  ✓ Player can complete level (0.5s)
  ✓ Goblin dies in 2 hits (0.1s)
2/2 tests passed
```

Green tests mean your game mechanics work as designed!

### Play the Game

```bash
$ renee run scenes/level_1.yaml
Starting game...
```

This launches the actual playable game. Use arrow keys to move, SPACE to attack.

## What You've Learned

You now understand the core Renee architecture:

1. **Entities** are objects with components (Health, Combat, Position, etc.)
2. **Components** define capabilities and stats
3. **Rules** are the game logic that triggers on events
4. **Scenes** combine entities and rules into playable levels
5. **Tests** verify mechanics match design intent
6. **intent** fields document design goals for AI collaboration

## Next Steps

To expand your game:

- **Add more enemies:** Create new entity types with different stats and behaviors
- **Add power-ups:** New collectibles that modify the player
- **Create more levels:** Copy level_1.yaml and modify the tilemap
- **Implement special abilities:** Add conditional combat modifiers in rules
- **Add visual feedback:** Update sprite references to match your art assets

For detailed information about each component type and available actions, see [DESIGN.md](DESIGN.md).

For CLI command options and advanced workflows, see [CLI.md](CLI.md).
