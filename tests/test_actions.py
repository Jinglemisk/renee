"""Tests for the Action Pipeline system."""

import pytest
from dataclasses import dataclass

from renee.actions import Action, ActionContext, ActionPipeline, ActionResult
from renee.ecs.world import World
from renee.types import EntityId, Position


# Sample event for testing
@dataclass(frozen=True)
class MovedEvent:
    """Event emitted when an entity moves."""
    entity: EntityId
    from_pos: Position
    to_pos: Position


class TestAction:
    """Tests for the Action class."""

    def test_action_creation(self):
        """Test creating a basic action."""
        action = Action(
            name='move',
            params={'entity': EntityId(1), 'target': Position(5, 5)},
            source=EntityId(1)
        )
        assert action.name == 'move'
        assert action.params['entity'] == EntityId(1)
        assert action.source == EntityId(1)

    def test_action_empty_name_raises(self):
        """Test that empty action name raises ValueError."""
        with pytest.raises(ValueError, match="Action name cannot be empty"):
            Action(name='', params={})

    def test_action_invalid_params_raises(self):
        """Test that non-dict params raises TypeError."""
        with pytest.raises(TypeError, match="Action params must be dict"):
            Action(name='test', params=[])  # type: ignore


class TestActionContext:
    """Tests for the ActionContext class."""

    def test_context_creation(self):
        """Test creating an action context."""
        action = Action('test', {})
        world = World()
        ctx = ActionContext(action=action, world=world, phase='pre')

        assert ctx.action == action
        assert ctx.world == world
        assert ctx.phase == 'pre'
        assert not ctx.cancelled
        assert ctx.cancel_reason is None

    def test_context_invalid_phase_raises(self):
        """Test that invalid phase raises ValueError."""
        action = Action('test', {})
        world = World()
        with pytest.raises(ValueError, match="Invalid phase"):
            ActionContext(action=action, world=world, phase='invalid')

    def test_context_cancel(self):
        """Test cancelling an action via context."""
        action = Action('test', {})
        world = World()
        ctx = ActionContext(action=action, world=world, phase='pre')

        ctx.cancel("Not allowed")
        assert ctx.cancelled
        assert ctx.cancel_reason == "Not allowed"

    def test_context_modify_param(self):
        """Test modifying action parameters."""
        action = Action('test', {'damage': 10})
        world = World()
        ctx = ActionContext(action=action, world=world, phase='pre')

        ctx.modify_param('damage', 5)
        assert ctx.modified_params['damage'] == 5
        assert ctx.get_param('damage') == 5
        assert ctx.get_param('missing', 'default') == 'default'

    def test_context_get_param_priority(self):
        """Test that get_param returns modified value if available."""
        action = Action('test', {'value': 100})
        world = World()
        ctx = ActionContext(action=action, world=world, phase='pre')

        # Original value
        assert ctx.get_param('value') == 100

        # After modification
        ctx.modify_param('value', 50)
        assert ctx.get_param('value') == 50


class TestActionResult:
    """Tests for the ActionResult class."""

    def test_success_result(self):
        """Test creating a successful result."""
        action = Action('test', {})
        result = ActionResult.success_result(action, events=[1, 2, 3])

        assert result.success
        assert not result.cancelled
        assert result.error is None
        assert len(result.events) == 3

    def test_cancelled_result(self):
        """Test creating a cancelled result."""
        action = Action('test', {})
        result = ActionResult.cancelled_result(action, "Invalid target")

        assert not result.success
        assert result.cancelled
        assert result.cancel_reason == "Invalid target"
        assert result.error is None

    def test_error_result(self):
        """Test creating an error result."""
        action = Action('test', {})
        result = ActionResult.error_result(action, "Handler failed")

        assert not result.success
        assert not result.cancelled
        assert result.error == "Handler failed"

    def test_invalid_result_states_raise(self):
        """Test that inconsistent result states raise ValueError."""
        action = Action('test', {})

        # Success can't have error
        with pytest.raises(ValueError, match="Successful action cannot be cancelled"):
            ActionResult(success=True, action=action, cancelled=True, cancel_reason="test")

        # Cancelled must have reason
        with pytest.raises(ValueError, match="Cancelled action must have a cancel_reason"):
            ActionResult(success=False, action=action, cancelled=True)

        # Failed must have reason or error
        with pytest.raises(ValueError, match="Failed action must have either cancel_reason or error"):
            ActionResult(success=False, action=action)


class TestActionPipeline:
    """Tests for the ActionPipeline class."""

    def test_register_handler(self):
        """Test registering an action handler."""
        pipeline = ActionPipeline()

        def handler(action: Action, world: World) -> list:
            return []

        pipeline.register_handler('test', handler)
        # Handler should be registered
        assert 'test' in pipeline._handlers

    def test_register_handler_empty_name_raises(self):
        """Test that empty action name raises ValueError."""
        pipeline = ActionPipeline()

        def handler(action: Action, world: World) -> list:
            return []

        with pytest.raises(ValueError, match="Action name cannot be empty"):
            pipeline.register_handler('', handler)

    def test_execute_no_handler(self):
        """Test executing action with no registered handler."""
        pipeline = ActionPipeline()
        world = World()
        action = Action('unknown', {})

        result = pipeline.execute(action, world)

        assert not result.success
        assert result.error == "No handler registered for action: unknown"

    def test_execute_success(self):
        """Test successful action execution."""
        pipeline = ActionPipeline()
        world = World()
        entity = world.create_entity()
        world.add_component(entity, Position(0, 0))

        def move_handler(action: Action, world: World) -> list:
            entity = action.params['entity']
            target = action.params['target']
            old_pos = world.get_component(entity, Position)
            world.add_component(entity, target)
            return [MovedEvent(entity=entity, from_pos=old_pos, to_pos=target)]

        pipeline.register_handler('move', move_handler)

        action = Action('move', {'entity': entity, 'target': Position(5, 5)})
        result = pipeline.execute(action, world)

        assert result.success
        assert len(result.events) == 1
        assert isinstance(result.events[0], MovedEvent)

        # Verify position changed
        new_pos = world.get_component(entity, Position)
        assert new_pos.x == 5
        assert new_pos.y == 5

    def test_execute_with_validator(self):
        """Test action validation."""
        pipeline = ActionPipeline()
        world = World()

        def validator(action: Action, world: World) -> str | None:
            if 'required_param' not in action.params:
                return "Missing required_param"
            return None

        def handler(action: Action, world: World) -> list:
            return []

        pipeline.register_validator('test', validator)
        pipeline.register_handler('test', handler)

        # Missing required param
        action = Action('test', {})
        result = pipeline.execute(action, world)
        assert not result.success
        assert result.error == "Missing required_param"

        # With required param
        action = Action('test', {'required_param': 'value'})
        result = pipeline.execute(action, world)
        assert result.success

    def test_execute_with_pre_rule_cancel(self):
        """Test pre-rule cancelling an action."""
        pipeline = ActionPipeline()
        world = World()

        def pre_rule(ctx: ActionContext) -> None:
            ctx.cancel("Action not allowed")

        def handler(action: Action, world: World) -> list:
            # Should not be called
            raise AssertionError("Handler should not be called")

        pipeline.add_pre_rule('test', pre_rule)
        pipeline.register_handler('test', handler)

        action = Action('test', {})
        result = pipeline.execute(action, world)

        assert not result.success
        assert result.cancelled
        assert result.cancel_reason == "Action not allowed"

    def test_execute_with_pre_rule_modify(self):
        """Test pre-rule modifying action parameters."""
        pipeline = ActionPipeline()
        world = World()

        def pre_rule(ctx: ActionContext) -> None:
            # Halve the damage
            damage = ctx.action.params.get('damage', 0)
            ctx.modify_param('damage', damage // 2)

        def handler(action: Action, world: World) -> list:
            return [action.params['damage']]

        pipeline.add_pre_rule('attack', pre_rule)
        pipeline.register_handler('attack', handler)

        action = Action('attack', {'damage': 100})
        result = pipeline.execute(action, world)

        assert result.success
        assert result.events[0] == 50  # Damage halved

    def test_execute_with_post_rule(self):
        """Test post-rule execution."""
        pipeline = ActionPipeline()
        world = World()

        post_rule_called = []

        def post_rule(ctx: ActionContext) -> None:
            post_rule_called.append(True)

        def handler(action: Action, world: World) -> list:
            return []

        pipeline.add_post_rule('test', post_rule)
        pipeline.register_handler('test', handler)

        action = Action('test', {})
        result = pipeline.execute(action, world)

        assert result.success
        assert len(post_rule_called) == 1

    def test_rule_priority_ordering(self):
        """Test that rules execute in priority order."""
        pipeline = ActionPipeline()
        world = World()

        execution_order = []

        def rule1(ctx: ActionContext) -> None:
            execution_order.append(1)

        def rule2(ctx: ActionContext) -> None:
            execution_order.append(2)

        def rule3(ctx: ActionContext) -> None:
            execution_order.append(3)

        def handler(action: Action, world: World) -> list:
            return []

        # Add rules with different priorities (higher = earlier)
        pipeline.add_pre_rule('test', rule1, priority=0)
        pipeline.add_pre_rule('test', rule2, priority=10)  # Highest priority
        pipeline.add_pre_rule('test', rule3, priority=5)
        pipeline.register_handler('test', handler)

        action = Action('test', {})
        pipeline.execute(action, world)

        # Should execute in order: 2 (priority 10), 3 (priority 5), 1 (priority 0)
        assert execution_order == [2, 3, 1]

    def test_handler_error_handling(self):
        """Test that handler errors are caught and returned."""
        pipeline = ActionPipeline()
        world = World()

        def failing_handler(action: Action, world: World) -> list:
            raise RuntimeError("Handler failed")

        pipeline.register_handler('test', failing_handler)

        action = Action('test', {})
        result = pipeline.execute(action, world)

        assert not result.success
        assert "Handler error: RuntimeError: Handler failed" in result.error

    def test_pre_rule_error_handling(self):
        """Test that pre-rule errors are caught and returned."""
        pipeline = ActionPipeline()
        world = World()

        def failing_rule(ctx: ActionContext) -> None:
            raise ValueError("Rule validation failed")

        def handler(action: Action, world: World) -> list:
            return []

        pipeline.add_pre_rule('test', failing_rule)
        pipeline.register_handler('test', handler)

        action = Action('test', {})
        result = pipeline.execute(action, world)

        assert not result.success
        assert "Pre-rule error: ValueError: Rule validation failed" in result.error
