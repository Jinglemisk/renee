# Rule Engine File Structure

## Directory Tree

```
renee-claude/
├── src/renee/rules/                    # Main rule engine package
│   ├── __init__.py                     # Public API exports
│   ├── rule.py                         # Rule class definition
│   ├── context.py                      # ActionContext and Action classes
│   ├── engine.py                       # RuleEngine implementation
│   ├── decorators.py                   # Decorator functions (@pre_rule, @post_rule)
│   ├── README.md                       # Comprehensive documentation
│   └── QUICK_REFERENCE.md             # Quick reference guide
│
├── tests/
│   └── test_rules.py                   # Complete test suite (25+ tests)
│
├── examples/
│   └── rule_engine_demo.py            # Working demonstration
│
├── test_rule_imports.py               # Import verification script
├── RULE_ENGINE_SUMMARY.md             # Implementation summary
└── RULE_ENGINE_STRUCTURE.md           # This file
```

## Module Dependencies

```
rule.py
  └─> context.py (TYPE_CHECKING only)

context.py
  └─> ecs.world (TYPE_CHECKING only)

engine.py
  └─> rule.py
  └─> context.py (TYPE_CHECKING only)

decorators.py
  └─> rule.py
  └─> engine.py (TYPE_CHECKING only)
  └─> context.py (TYPE_CHECKING only)

__init__.py
  └─> rule.py
  └─> context.py
  └─> engine.py
  └─> decorators.py
```

## Class Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                        Rule Engine                          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐         ┌──────────┐         ┌────────────┐
   │  Rule   │         │  Engine  │         │ Decorators │
   └─────────┘         └──────────┘         └────────────┘
        │                     │                     │
        │              manages │                creates
        │                     │                     │
        │                     ▼                     │
        │              ┌──────────────┐            │
        │              │ List[Rule]   │◄───────────┘
        │              └──────────────┘
        │                     │
        │              applies to
        │                     │
        │                     ▼
        │              ┌──────────────┐
        └─────────────>│    Context   │
                       └──────────────┘
                              │
                       contains
                              │
                              ▼
                       ┌──────────┐
                       │  Action  │
                       └──────────┘
```

## Data Flow

```
1. Rule Definition
   ┌──────────────┐
   │ @pre_rule()  │
   │ def func():  │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Rule created │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Registered   │
   │ with Engine  │
   └──────────────┘

2. Rule Execution
   ┌──────────────┐
   │ Action def   │
   │ params       │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Context      │
   │ created      │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Engine.      │
   │ apply_rules  │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Get matching │
   │ rules        │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Sort by      │
   │ priority     │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Check        │
   │ condition    │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Execute      │
   │ handler      │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Context may  │
   │ be modified  │
   └──────────────┘
```

## Public API Surface

```python
# Classes
Rule                    # Rule definition
RuleEngine             # Rule management
ActionContext          # Rule context
Action                 # Action being processed

# Decorators
@pre_rule              # Pre-action rule
@post_rule             # Post-action rule
@rule                  # Base rule decorator

# Functions
set_global_engine()    # Set global engine
get_global_engine()    # Get global engine
collect_rules()        # Collect from module
register_module_rules() # Bulk register
```

## File Size and Complexity

| File | Lines | Classes | Functions | Purpose |
|------|-------|---------|-----------|---------|
| `rule.py` | ~110 | 1 | 4 methods | Rule definition |
| `context.py` | ~120 | 2 | 6 methods | Action context |
| `engine.py` | ~220 | 1 | 11 methods | Rule engine |
| `decorators.py` | ~270 | 0 | 7 functions | Decorators |
| `__init__.py` | ~70 | 0 | 0 | Exports |
| **Total** | **~790** | **4** | **28** | **Complete** |

## Test Coverage

| Test Class | Tests | Coverage |
|------------|-------|----------|
| `TestRule` | 7 | Rule class |
| `TestActionContext` | 5 | Context functionality |
| `TestRuleEngine` | 11 | Engine operations |
| `TestRuleDecorators` | 6 | Decorator usage |
| `TestIntegrationScenarios` | 1 | End-to-end |
| **Total** | **30** | **Complete** |

## Documentation

| Document | Pages | Purpose |
|----------|-------|---------|
| `README.md` | ~400 lines | Full documentation |
| `QUICK_REFERENCE.md` | ~200 lines | Quick guide |
| `RULE_ENGINE_SUMMARY.md` | ~600 lines | Implementation details |
| `RULE_ENGINE_STRUCTURE.md` | This file | Structure overview |
| **Total** | **~1400 lines** | **Comprehensive** |

## Integration Points

```
┌─────────────────────────────────────────────────────────┐
│                    Renee Framework                      │
└─────────────────────────────────────────────────────────┘
                          │
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
    ▼                     ▼                     ▼
┌────────┐         ┌──────────┐         ┌──────────┐
│  ECS   │◄────────│  Rules   │────────>│  Events  │
│ World  │  uses   │  Engine  │  emits  │   Bus    │
└────────┘         └──────────┘         └──────────┘
                          ▲
                          │
                   integrates with
                          │
                          ▼
                   ┌──────────┐
                   │  Action  │
                   │ Pipeline │
                   └──────────┘
                    (Phase 2.1)
```

## Usage Flow

```
Developer writes rules:
  @pre_rule(action='attack')
  def check_range(ctx):
      # validation logic

      ↓

Rules auto-register:
  engine.register(rule)

      ↓

Action executed:
  action = Action(...)
  ctx = ActionContext(...)

      ↓

Pre-rules applied:
  engine.apply_rules(ctx, 'pre')

      ↓

Check cancellation:
  if not ctx.is_cancelled():

      ↓

Execute action handler:
  result = handler(ctx)

      ↓

Post-rules applied:
  engine.apply_rules(ctx, 'post')

      ↓

Result returned:
  return result
```

## Key Design Patterns

1. **Decorator Pattern**: Rules defined as decorated functions
2. **Strategy Pattern**: Different rules for different actions
3. **Chain of Responsibility**: Rules process context in sequence
4. **Observer Pattern**: Rules react to action events
5. **Registry Pattern**: Central engine manages all rules

## Performance Characteristics

- **Registration**: O(n log n) due to sorting by priority
- **Rule lookup**: O(n) linear scan with filtering
- **Rule execution**: O(m) where m = matching rules
- **Total per action**: O(n + m) typically very fast

Optimizations:
- Rules sorted once at registration
- TYPE_CHECKING imports for reduced runtime overhead
- Dataclasses with slots for memory efficiency
- No unnecessary copies or allocations

## Memory Footprint

- Each Rule: ~200 bytes (dataclass + function refs)
- Engine: ~100 bytes + (n * 200) for n rules
- Context: ~150 bytes per execution
- Total for typical game: < 50 KB

## Thread Safety

Current implementation is NOT thread-safe:
- Engine modification and execution should be single-threaded
- Future: Add locking if multi-threaded action processing needed
- Turn-based games typically single-threaded, so not a concern

## Future Extensions

Potential additions (not in scope):
- Rule groups and namespaces
- Rule hot-reloading
- Visual rule editor
- Rule profiling/debugging
- Rule conflict detection
- Rule templates/macros
