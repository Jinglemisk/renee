  Turn-Based vs. Time-Agnostic: An Analysis

  The Core Question

  Can a framework be agnostic to the turn-based vs. real-time distinction, or is "turn-based" a fundamental architectural commitment that can't be
  abstracted away?

  What "Turn-Based" Actually Means Architecturally

  Turn-based isn't just a game feel—it implies specific technical constraints:

  | Aspect           | Turn-Based                           | Real-Time                              |
  |------------------|--------------------------------------|----------------------------------------|
  | State Updates    | Discrete, on action                  | Continuous, every frame                |
  | Input Processing | Wait indefinitely for player         | Poll constantly                        |
  | Game Loop        | Event-driven (action → resolution)   | Time-driven (tick → update → render)   |
  | Determinism      | Natural (same inputs = same outputs) | Harder (timing variations)             |
  | Simulation       | Easy (replay actions)                | Complex (must replay at exact timings) |
  | Multiplayer Sync | Send actions                         | Send state deltas + interpolation      |
  | AI Decision Time | Unlimited                            | Must fit in frame budget               |

  The Honest Answer: They're Different Architectures

  Turn-based and real-time are not parameters you toggle—they're different runtime models.

  A turn-based game's core loop:
  while game_running:
	  action = wait_for_player_input()  # Blocks indefinitely
	  validate(action)
	  apply_rules(action)
	  update_state(action)
	  emit_events()
	  render()

  A real-time game's core loop:
  while game_running:
	  delta_time = get_elapsed_time()
	  input = poll_input()  # Non-blocking
	  update_physics(delta_time)
	  update_ai(delta_time)
	  update_animations(delta_time)
	  resolve_collisions()
	  render()

  These are fundamentally different. The turn-based loop waits. The real-time loop ticks.

  What About Hybrid Games?

  Some games blur the line:

  | Game                | Model                                                       |
  |---------------------|-------------------------------------------------------------|
  | Civilization        | Pure turn-based                                             |
  | XCOM                | Turn-based tactics, real-time base (but base is just menus) |
  | Baldur's Gate       | Real-time with pause (actually turn-based under the hood)   |
  | FTL                 | Real-time with pause                                        |
  | Into the Breach     | Pure turn-based                                             |
  | Slay the Spire      | Pure turn-based                                             |
  | Auto-battlers       | Turn setup, then automated real-time resolution             |
  | ATB (Final Fantasy) | Hybrid—time-based turn filling                              |

  Key insight: Most "hybrids" are actually turn-based with visual flourishes, or have clearly separated modes.

  Can Renee Abstract This?

  Option A: Stay Turn-Based (Recommended)

  Rationale:
  1. Clear identity — "AI-native turn-based framework" is a specific, defensible niche
  2. AI alignment — Turn-based games are perfect for AI agents:
	- Unlimited thinking time
	- Discrete state snapshots
	- Deterministic replay
	- Easy simulation
  3. Scope control — Real-time adds massive complexity (physics, interpolation, networking)
  4. The market — Turn-based games are underserved by frameworks. Unity/Godot are real-time first.

  Option B: Abstract to "Discrete Time Steps"

  You could generalize "turn" to "time step":

  TimeModel:
	- Turn-based: time_step triggered by player action
	- Real-time: time_step triggered by clock (e.g., 60/sec)
	- Hybrid: time_step triggered by either

  But this creates problems:
  - Real-time needs delta_time everywhere (turn-based doesn't)
  - Real-time needs interpolation for smooth rendering
  - Real-time needs fixed timestep physics
  - Event sourcing becomes much harder (need timestamps, not just sequence)
  - Simulation becomes non-trivial

  You'd essentially be building two frameworks sharing some utilities.

  Option C: "Discrete Event Simulation" Framework

  The most general abstraction:

  "Renee is a framework for games where state changes occur at discrete points, whether those points are player-initiated (turn-based) or clock-initiated 
  (real-time ticks)."

  This is technically accurate but:
  - Loses marketing clarity
  - Still requires different runtime modes
  - Doesn't actually simplify implementation

  My Recommendation: Stay Turn-Based, But Clarify Scope

  Keep "turn-based" but define it broadly:

  Renee supports games where:
  - Players make decisions at discrete points
  - State updates are atomic (not continuous)
  - Time advances in defined increments (turns, phases, rounds)

  This includes: traditional turn-based, phase-based, simultaneous turns, real-time-with-pause, and auto-battler resolution.

  This excludes: continuous real-time (RTS, action games, physics-based games).

  Why this works:
  1. Clear boundary (no physics, no continuous updates)
  2. Still very broad (covers 90% of strategy/tactics/card/board games)
  3. Plays to AI strengths (discrete states, deterministic simulation)
  4. Manageable scope for implementation

  What You'd Lose By Going Time-Agnostic

  1. Simplicity — Turn-based ECS is simple. Real-time ECS needs systems running every frame.
  2. Event Sourcing — Perfect for turn-based, awkward for real-time
  3. Deterministic Simulation — Trivial for turn-based, hard for real-time
  4. AI-Native Tooling — Impact analysis, simulation, snapshot/rollback all assume discrete states
  5. Multiplayer Simplicity — Turn-based sync is "send actions." Real-time sync is a nightmare.

  What You'd Gain

  Honestly? Not much for the target use case. If someone wants to build an RTS, they should use Godot or Unity. Renee's value proposition is specifically
  for the games those engines handle poorly.

  ---
  Conclusion

  Stay turn-based. It's not a limitation—it's a feature.

  The framework's AI-native innovations (intent fields, impact analysis, simulation, event sourcing) all assume discrete state transitions. Making the
  framework time-agnostic would either:
  1. Compromise these features for real-time support, or
  2. Require building two parallel systems

  "Turn-based" is the right scope. It's specific enough to be useful, broad enough to cover many genres, and aligned with the AI-native vision.

  Suggested framing:

  Renee is a framework for discrete-state games—games where time advances in defined steps and state changes are atomic. This includes turn-based strategy,
   tactics, card games, board games, roguelikes, and puzzle games.

  This is technically precise, covers the actual scope, and doesn't artificially exclude games like FTL or auto-battlers that have real-time presentation
  but discrete mechanics.