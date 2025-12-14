"""Python-decorator rule engine (no custom DSL)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal, Protocol, TYPE_CHECKING

RulePhase = Literal["pre", "post"]

if TYPE_CHECKING:  # pragma: no cover
    from renee.actions.types import ActionContext


class RuleFn(Protocol):
    def __call__(self, ctx: "ActionContext") -> Any: ...


RulePredicate = Callable[["ActionContext"], bool]


@dataclass(frozen=True, slots=True)
class Rule:
    name: str
    phase: RulePhase
    priority: int
    fn: RuleFn
    when: RulePredicate | None = None

    def applies(self, ctx: "ActionContext") -> bool:
        return True if self.when is None else bool(self.when(ctx))


def rule(*, phase: RulePhase = "pre", priority: int = 0, when: RulePredicate | None = None) -> Callable[[RuleFn], RuleFn]:
    """Decorator to mark a function as a rule."""

    def decorator(fn: RuleFn) -> RuleFn:
        r = Rule(name=getattr(fn, "__name__", "rule"), phase=phase, priority=priority, fn=fn, when=when)
        setattr(fn, "__renee_rule__", r)
        return fn

    return decorator


class RuleEngine:
    """Stores and executes pre/post rules in priority order."""

    def __init__(self) -> None:
        self._rules: list[Rule] = []

    def register(self, rule_or_fn: Rule | RuleFn) -> None:
        if isinstance(rule_or_fn, Rule):
            self._rules.append(rule_or_fn)
            return
        r = getattr(rule_or_fn, "__renee_rule__", None)
        if not isinstance(r, Rule):
            raise TypeError("Expected a Rule or a function decorated with @rule")
        self._rules.append(r)

    def rules(self, *, phase: RulePhase | None = None) -> list[Rule]:
        if phase is None:
            return list(self._rules)
        return [r for r in self._rules if r.phase == phase]

    def run(self, ctx: "ActionContext", *, phase: RulePhase) -> None:
        # Higher priority first; stable sort keeps registration order for ties.
        ordered = sorted((r for r in self._rules if r.phase == phase), key=lambda r: r.priority, reverse=True)
        for r in ordered:
            if ctx.cancelled and phase == "pre":
                return
            if r.applies(ctx):
                r.fn(ctx)

