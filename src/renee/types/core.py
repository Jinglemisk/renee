"""Core semantic types for Renee.

These types carry meaning beyond Python primitives and enable
validation, documentation, and IDE support.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from typing import NewType, TypeVar, Any, Callable

# Entity reference - an int at runtime, but semantically meaningful
EntityId = NewType("EntityId", int)

# Generic type variable for component retrieval
T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Position:
    """A position on a 2D grid.

    Immutable to prevent accidental mutation. Use world.add_component()
    with a new Position to move an entity.
    """

    x: int
    y: int

    def __add__(self, other: Position) -> Position:
        """Add two positions (vector addition)."""
        return Position(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Position) -> Position:
        """Subtract two positions (vector subtraction)."""
        return Position(self.x - other.x, self.y - other.y)

    def manhattan_distance(self, other: Position) -> int:
        """Calculate Manhattan distance to another position."""
        return abs(self.x - other.x) + abs(self.y - other.y)

    def chebyshev_distance(self, other: Position) -> int:
        """Calculate Chebyshev distance (king's move) to another position."""
        return max(abs(self.x - other.x), abs(self.y - other.y))

    def euclidean_distance(self, other: Position) -> float:
        """Calculate Euclidean distance to another position."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def neighbors(self, diagonal: bool = False) -> list[Position]:
        """Get neighboring positions (4 cardinal or 8 with diagonals)."""
        cardinals = [
            Position(self.x + 1, self.y),
            Position(self.x - 1, self.y),
            Position(self.x, self.y + 1),
            Position(self.x, self.y - 1),
        ]
        if not diagonal:
            return cardinals
        diagonals = [
            Position(self.x + 1, self.y + 1),
            Position(self.x + 1, self.y - 1),
            Position(self.x - 1, self.y + 1),
            Position(self.x - 1, self.y - 1),
        ]
        return cardinals + diagonals

    def to_tuple(self) -> tuple[int, int]:
        """Convert to tuple for compatibility."""
        return (self.x, self.y)

    @classmethod
    def from_tuple(cls, t: tuple[int, int]) -> Position:
        """Create from tuple."""
        return cls(t[0], t[1])


@dataclass(frozen=True, slots=True)
class Probability:
    """A probability value constrained to [0.0, 1.0].

    Used for critical hit chances, dodge rates, etc.
    """

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"Probability must be between 0.0 and 1.0, got {self.value}")

    def check(self, rng: random.Random | None = None) -> bool:
        """Roll against this probability. Returns True if the check succeeds."""
        r = rng if rng else random
        return r.random() < self.value

    def __float__(self) -> float:
        return self.value

    def __mul__(self, other: float | Probability) -> Probability:
        """Multiply probabilities."""
        other_val = other.value if isinstance(other, Probability) else other
        return Probability(min(1.0, max(0.0, self.value * other_val)))

    def complement(self) -> Probability:
        """Return 1 - this probability."""
        return Probability(1.0 - self.value)


@dataclass(frozen=True, slots=True)
class DiceRoll:
    """Parsed dice notation (e.g., '2d6+3').

    Supports standard dice notation: NdS+M or NdS-M
    where N is number of dice, S is sides, M is modifier.
    """

    count: int
    sides: int
    modifier: int = 0

    _DICE_PATTERN: re.Pattern[str] = field(
        default=re.compile(r"^(\d+)d(\d+)([+-]\d+)?$", re.IGNORECASE),
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        if self.count < 1:
            raise ValueError(f"Dice count must be at least 1, got {self.count}")
        if self.sides < 1:
            raise ValueError(f"Dice sides must be at least 1, got {self.sides}")

    @classmethod
    def parse(cls, notation: str) -> DiceRoll:
        """Parse dice notation string like '2d6+3' into a DiceRoll."""
        match = re.match(r"^(\d+)d(\d+)([+-]\d+)?$", notation.strip(), re.IGNORECASE)
        if not match:
            raise ValueError(f"Invalid dice notation: {notation}")
        count = int(match.group(1))
        sides = int(match.group(2))
        modifier = int(match.group(3)) if match.group(3) else 0
        return cls(count=count, sides=sides, modifier=modifier)

    def roll(self, rng: random.Random | None = None) -> int:
        """Roll the dice and return the result."""
        r = rng if rng else random
        total = sum(r.randint(1, self.sides) for _ in range(self.count))
        return total + self.modifier

    def min_value(self) -> int:
        """Minimum possible roll."""
        return self.count + self.modifier

    def max_value(self) -> int:
        """Maximum possible roll."""
        return self.count * self.sides + self.modifier

    def average(self) -> float:
        """Expected average roll."""
        return self.count * (self.sides + 1) / 2 + self.modifier

    def __str__(self) -> str:
        base = f"{self.count}d{self.sides}"
        if self.modifier > 0:
            return f"{base}+{self.modifier}"
        elif self.modifier < 0:
            return f"{base}{self.modifier}"
        return base


@dataclass(frozen=True, slots=True)
class Duration:
    """Time measurement in game units.

    Can represent turns, rounds, phases, or abstract time units.
    """

    value: int
    unit: str = "turns"

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError(f"Duration cannot be negative, got {self.value}")

    def is_expired(self, elapsed: int) -> bool:
        """Check if this duration has expired given elapsed time."""
        return elapsed >= self.value

    def remaining(self, elapsed: int) -> int:
        """Return remaining time, minimum 0."""
        return max(0, self.value - elapsed)

    def __add__(self, other: Duration | int) -> Duration:
        if isinstance(other, Duration):
            if other.unit != self.unit:
                raise ValueError(f"Cannot add durations with different units: {self.unit} vs {other.unit}")
            return Duration(self.value + other.value, self.unit)
        return Duration(self.value + other, self.unit)

    def __sub__(self, other: Duration | int) -> Duration:
        if isinstance(other, Duration):
            if other.unit != self.unit:
                raise ValueError(f"Cannot subtract durations with different units: {self.unit} vs {other.unit}")
            return Duration(max(0, self.value - other.value), self.unit)
        return Duration(max(0, self.value - other), self.unit)

    def __str__(self) -> str:
        return f"{self.value} {self.unit}"


@dataclass(frozen=True, slots=True)
class AssetRef:
    """Validated reference to an asset (sprite, sound, font, etc.).

    Asset references are validated against the asset manifest at load time.
    """

    category: str  # e.g., 'sprites', 'sounds', 'fonts'
    name: str  # e.g., 'player_idle', 'explosion_01'

    def __post_init__(self) -> None:
        if not self.category:
            raise ValueError("Asset category cannot be empty")
        if not self.name:
            raise ValueError("Asset name cannot be empty")

    def path(self, base: str = "assets") -> str:
        """Get the relative path to this asset."""
        return f"{base}/{self.category}/{self.name}"

    def __str__(self) -> str:
        return f"{self.category}:{self.name}"

    @classmethod
    def parse(cls, ref_string: str) -> AssetRef:
        """Parse 'category:name' string into AssetRef."""
        if ":" not in ref_string:
            raise ValueError(f"Invalid asset reference format: {ref_string}. Expected 'category:name'")
        category, name = ref_string.split(":", 1)
        return cls(category=category, name=name)


@dataclass(slots=True)
class Formula:
    """Runtime-evaluated expression for scaling calculations.

    Formulas can reference variables and use basic math operations.
    Example: "base_damage * level + bonus"
    """

    expression: str
    _compiled: Any = field(default=None, init=False, repr=False, compare=False)

    # Allowed names in formula evaluation (safe subset)
    _ALLOWED_NAMES: dict[str, Any] = field(
        default_factory=lambda: {
            "abs": abs,
            "min": min,
            "max": max,
            "round": round,
            "int": int,
            "float": float,
            "pow": pow,
        },
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        # Pre-compile the expression to catch syntax errors early
        try:
            self._compiled = compile(self.expression, "<formula>", "eval")
        except SyntaxError as e:
            raise ValueError(f"Invalid formula syntax: {self.expression}") from e

    def evaluate(self, variables: dict[str, int | float]) -> float:
        """Evaluate the formula with given variables.

        Args:
            variables: Dictionary mapping variable names to values.

        Returns:
            The evaluated result as a float.

        Raises:
            ValueError: If the formula references undefined variables or uses
                       disallowed operations.
        """
        # Create safe namespace
        namespace = dict(self._ALLOWED_NAMES)
        namespace.update(variables)

        try:
            result = eval(self._compiled, {"__builtins__": {}}, namespace)
            return float(result)
        except NameError as e:
            raise ValueError(f"Undefined variable in formula: {e}") from e
        except Exception as e:
            raise ValueError(f"Error evaluating formula '{self.expression}': {e}") from e

    def __str__(self) -> str:
        return self.expression


@dataclass(frozen=True, slots=True)
class Range:
    """A numeric range with min and max values."""

    min_val: int | float
    max_val: int | float

    def __post_init__(self) -> None:
        if self.min_val > self.max_val:
            raise ValueError(f"min_val ({self.min_val}) cannot be greater than max_val ({self.max_val})")

    def contains(self, value: int | float) -> bool:
        """Check if a value is within this range (inclusive)."""
        return self.min_val <= value <= self.max_val

    def clamp(self, value: int | float) -> int | float:
        """Clamp a value to this range."""
        return max(self.min_val, min(self.max_val, value))

    def random_value(self, rng: random.Random | None = None) -> float:
        """Get a random value within this range."""
        r = rng if rng else random
        return r.uniform(float(self.min_val), float(self.max_val))

    def random_int(self, rng: random.Random | None = None) -> int:
        """Get a random integer within this range."""
        r = rng if rng else random
        return r.randint(int(self.min_val), int(self.max_val))


@dataclass(frozen=True, slots=True)
class Direction:
    """A cardinal or ordinal direction."""

    dx: int
    dy: int

    def __post_init__(self) -> None:
        if not (-1 <= self.dx <= 1 and -1 <= self.dy <= 1):
            raise ValueError(f"Direction components must be -1, 0, or 1, got ({self.dx}, {self.dy})")
        if self.dx == 0 and self.dy == 0:
            raise ValueError("Direction cannot be (0, 0)")

    def apply(self, pos: Position) -> Position:
        """Apply this direction to a position."""
        return Position(pos.x + self.dx, pos.y + self.dy)

    def opposite(self) -> Direction:
        """Get the opposite direction."""
        return Direction(-self.dx, -self.dy)

    def rotate_cw(self) -> Direction:
        """Rotate 45 degrees clockwise."""
        # Rotation matrix for 45 degrees, mapped to discrete grid
        rotations = {
            (0, -1): (1, -1),   # N -> NE
            (1, -1): (1, 0),    # NE -> E
            (1, 0): (1, 1),     # E -> SE
            (1, 1): (0, 1),     # SE -> S
            (0, 1): (-1, 1),    # S -> SW
            (-1, 1): (-1, 0),   # SW -> W
            (-1, 0): (-1, -1),  # W -> NW
            (-1, -1): (0, -1),  # NW -> N
        }
        new = rotations.get((self.dx, self.dy))
        if new:
            return Direction(new[0], new[1])
        return self

    def rotate_ccw(self) -> Direction:
        """Rotate 45 degrees counter-clockwise."""
        return self.opposite().rotate_cw().opposite()

    @classmethod
    def from_positions(cls, from_pos: Position, to_pos: Position) -> Direction | None:
        """Get direction from one position to another (None if same position)."""
        dx = to_pos.x - from_pos.x
        dy = to_pos.y - from_pos.y
        if dx == 0 and dy == 0:
            return None
        # Normalize to -1, 0, or 1
        dx = 0 if dx == 0 else (1 if dx > 0 else -1)
        dy = 0 if dy == 0 else (1 if dy > 0 else -1)
        return cls(dx, dy)


# Module-level direction constants
NORTH = Direction(0, -1)
SOUTH = Direction(0, 1)
EAST = Direction(1, 0)
WEST = Direction(-1, 0)
NORTHEAST = Direction(1, -1)
NORTHWEST = Direction(-1, -1)
SOUTHEAST = Direction(1, 1)
SOUTHWEST = Direction(-1, 1)

# All cardinal directions
CARDINAL_DIRECTIONS = [NORTH, EAST, SOUTH, WEST]
# All 8 directions
ALL_DIRECTIONS = CARDINAL_DIRECTIONS + [NORTHEAST, SOUTHEAST, SOUTHWEST, NORTHWEST]
