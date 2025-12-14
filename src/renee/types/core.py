"""Core semantic types for Renee.

These types carry meaning beyond Python primitives and enable validation,
documentation, and IDE support.
"""

from __future__ import annotations

from dataclasses import dataclass
import ast
import math
import random
import re
from typing import Any, ClassVar, Mapping, NewType, TypeVar

# Entity reference - an int at runtime, but semantically meaningful
EntityId = NewType("EntityId", int)

# Asset reference - a string validated against an asset manifest
AssetRef = NewType("AssetRef", str)

# Generic type variable for component retrieval
T = TypeVar("T")


class Probability(float):
    """A float constrained to 0.0 <= p <= 1.0."""

    def __new__(cls, value: float) -> "Probability":
        if not isinstance(value, (int, float)):
            raise TypeError(f"Probability must be a number, got {type(value).__name__}")
        v = float(value)
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"Probability must be between 0.0 and 1.0, got {v}")
        return float.__new__(cls, v)  # type: ignore[return-value]


@dataclass(frozen=True, slots=True)
class DiceRoll:
    """Dice notation like ``2d6+3``."""

    count: int
    sides: int
    modifier: int = 0

    _DICE_RE = re.compile(r"^(?P<count>\d+)d(?P<sides>\d+)(?P<mod>[+-]\d+)?$")

    @classmethod
    def parse(cls, notation: str) -> "DiceRoll":
        text = notation.strip().lower()
        m = cls._DICE_RE.match(text)
        if not m:
            raise ValueError(f"Invalid dice notation: {notation!r} (expected like '2d6+3')")
        count = int(m.group("count"))
        sides = int(m.group("sides"))
        modifier = int(m.group("mod") or "0")
        if count <= 0:
            raise ValueError(f"Dice count must be > 0, got {count}")
        if sides <= 0:
            raise ValueError(f"Dice sides must be > 0, got {sides}")
        return cls(count=count, sides=sides, modifier=modifier)

    def roll(self, rng: random.Random) -> int:
        total = self.modifier
        for _ in range(self.count):
            total += rng.randint(1, self.sides)
        return total


@dataclass(frozen=True, slots=True)
class Duration:
    """A duration measured in turns (game-defined time unit)."""

    turns: int

    def __post_init__(self) -> None:
        if self.turns < 0:
            raise ValueError(f"Duration turns must be >= 0, got {self.turns}")

    @classmethod
    def parse(cls, text: str) -> "Duration":
        raw = text.strip().lower()
        if raw.endswith("turns"):
            raw = raw.removesuffix("turns").strip()
        elif raw.endswith("turn"):
            raw = raw.removesuffix("turn").strip()
        return cls(turns=int(raw))


@dataclass(frozen=True, slots=True)
class Formula:
    """A safe, evaluatable arithmetic expression.

    Supported:
    - literals: ints/floats
    - variables: names from provided mapping
    - operators: + - * / // % **, parentheses
    - functions: min, max, abs, round, floor, ceil
    """

    expr: str

    _ALLOWED_FUNCS: ClassVar[dict[str, Any]] = {
        "min": min,
        "max": max,
        "abs": abs,
        "round": round,
        "floor": math.floor,
        "ceil": math.ceil,
    }

    def evaluate(self, variables: Mapping[str, float | int]) -> float:
        tree = ast.parse(self.expr, mode="eval")
        return float(_SafeEval(variables=variables, funcs=self._ALLOWED_FUNCS).eval(tree))


class _SafeEval:
    def __init__(self, *, variables: Mapping[str, float | int], funcs: Mapping[str, Any]) -> None:
        self._variables = variables
        self._funcs = funcs

    def eval(self, node: ast.AST) -> float | int:
        if isinstance(node, ast.Expression):
            return self.eval(node.body)

        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value

        if isinstance(node, ast.Name):
            if node.id in self._variables:
                return self._variables[node.id]
            raise NameError(f"Unknown variable: {node.id}")

        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = self.eval(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value

        if isinstance(node, ast.BinOp) and isinstance(
            node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
        ):
            left = self.eval(node.left)
            right = self.eval(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.FloorDiv):
                return left // right
            if isinstance(node.op, ast.Mod):
                return left % right
            return left**right

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls are allowed")
            fn_name = node.func.id
            if fn_name not in self._funcs:
                raise ValueError(f"Function not allowed: {fn_name}")
            fn = self._funcs[fn_name]
            args = [self.eval(arg) for arg in node.args]
            if node.keywords:
                raise ValueError("Keyword arguments are not allowed")
            return fn(*args)

        raise ValueError(f"Unsupported expression element: {type(node).__name__}")

@dataclass(frozen=True, slots=True)
class Position:
    """A position on a 2D grid.

    Immutable to prevent accidental mutation. Use world.add_component()
    with a new Position to move an entity.
    """

    x: int
    y: int

    def __add__(self, other: "Position") -> "Position":
        """Add two positions (vector addition)."""
        return Position(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Position") -> "Position":
        """Subtract two positions (vector subtraction)."""
        return Position(self.x - other.x, self.y - other.y)

    def manhattan_distance(self, other: "Position") -> int:
        """Calculate Manhattan distance to another position."""
        return abs(self.x - other.x) + abs(self.y - other.y)

    def chebyshev_distance(self, other: "Position") -> int:
        """Calculate Chebyshev distance (king's move) to another position."""
        return max(abs(self.x - other.x), abs(self.y - other.y))
