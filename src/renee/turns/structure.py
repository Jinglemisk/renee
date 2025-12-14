"""Time structure definitions for turn-based games.

Provides hierarchical time units (rounds, turns, phases) and phase traits.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TimeUnit:
    """Hierarchical time unit (e.g., round → turn → phase).

    Attributes:
        name: Unit identifier (e.g., "round", "turn", "phase")
        children: Nested time units within this unit
    """
    name: str
    children: list["TimeUnit"] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate time unit configuration."""
        if not self.name:
            raise ValueError("TimeUnit name cannot be empty")

    def depth(self) -> int:
        """Calculate the depth of this time unit hierarchy."""
        if not self.children:
            return 1
        return 1 + max(child.depth() for child in self.children)

    def find_unit(self, name: str) -> Optional["TimeUnit"]:
        """Find a time unit by name in the hierarchy.

        Args:
            name: Name of the time unit to find

        Returns:
            TimeUnit if found, None otherwise
        """
        if self.name == name:
            return self
        for child in self.children:
            result = child.find_unit(name)
            if result:
                return result
        return None


@dataclass
class Phase:
    """A phase within a turn with specific traits and constraints.

    Traits:
        - 'skippable': Phase can be skipped
        - 'mandatory': Phase must execute
        - 'timed': Phase has a time limit
        - 'unlimited_actions': Player can perform unlimited actions
        - 'single_action': Player can perform exactly one action

    Attributes:
        name: Phase identifier
        traits: Set of phase traits
        duration: Duration for timed phases (in seconds/ticks)
    """
    name: str
    traits: set[str] = field(default_factory=set)
    duration: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate phase configuration."""
        if not self.name:
            raise ValueError("Phase name cannot be empty")

        # Validate trait combinations
        if "mandatory" in self.traits and "skippable" in self.traits:
            raise ValueError("Phase cannot be both mandatory and skippable")

        if "unlimited_actions" in self.traits and "single_action" in self.traits:
            raise ValueError("Phase cannot have both unlimited_actions and single_action")

        if "timed" in self.traits and self.duration is None:
            raise ValueError("Timed phase must have a duration")

    def is_skippable(self) -> bool:
        """Check if this phase can be skipped."""
        return "skippable" in self.traits

    def is_mandatory(self) -> bool:
        """Check if this phase must execute."""
        return "mandatory" in self.traits

    def is_timed(self) -> bool:
        """Check if this phase has a time limit."""
        return "timed" in self.traits

    def allows_unlimited_actions(self) -> bool:
        """Check if unlimited actions are allowed."""
        return "unlimited_actions" in self.traits

    def is_single_action(self) -> bool:
        """Check if only one action is allowed."""
        return "single_action" in self.traits


class TimeStructure:
    """Defines the hierarchical structure of time in a game.

    Example:
        Round → Turn → Phase
        where each round contains multiple turns,
        and each turn contains multiple phases.
    """

    def __init__(self, units: list[TimeUnit], phases: list[Phase]) -> None:
        """Initialize time structure.

        Args:
            units: Hierarchical time units
            phases: Available phases within the smallest time unit

        Raises:
            ValueError: If configuration is invalid
        """
        if not units:
            raise ValueError("TimeStructure requires at least one time unit")
        if not phases:
            raise ValueError("TimeStructure requires at least one phase")

        self.units = units
        self.phases = phases
        self._phase_map = {phase.name: phase for phase in phases}

        # Validate unique phase names
        if len(self._phase_map) != len(phases):
            raise ValueError("Phase names must be unique")

    def get_phase(self, name: str) -> Optional[Phase]:
        """Get a phase by name.

        Args:
            name: Phase name

        Returns:
            Phase if found, None otherwise
        """
        return self._phase_map.get(name)

    def get_phase_index(self, name: str) -> int:
        """Get the index of a phase in the sequence.

        Args:
            name: Phase name

        Returns:
            Phase index

        Raises:
            ValueError: If phase not found
        """
        for i, phase in enumerate(self.phases):
            if phase.name == name:
                return i
        raise ValueError(f"Phase '{name}' not found")

    def get_next_phase(self, current_phase: str) -> Optional[Phase]:
        """Get the next phase after the current one.

        Args:
            current_phase: Current phase name

        Returns:
            Next phase, or None if at the end
        """
        try:
            index = self.get_phase_index(current_phase)
            if index + 1 < len(self.phases):
                return self.phases[index + 1]
        except ValueError:
            pass
        return None

    def get_root_unit(self) -> Optional[TimeUnit]:
        """Get the root (top-level) time unit.

        Returns:
            First time unit if available
        """
        return self.units[0] if self.units else None

    def find_unit(self, name: str) -> Optional[TimeUnit]:
        """Find a time unit by name.

        Args:
            name: Time unit name

        Returns:
            TimeUnit if found, None otherwise
        """
        for unit in self.units:
            result = unit.find_unit(name)
            if result:
                return result
        return None

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary.

        Returns:
            Dictionary representation
        """
        def unit_to_dict(unit: TimeUnit) -> dict:
            return {
                "name": unit.name,
                "children": [unit_to_dict(child) for child in unit.children]
            }

        return {
            "units": [unit_to_dict(unit) for unit in self.units],
            "phases": [
                {
                    "name": phase.name,
                    "traits": list(phase.traits),
                    "duration": phase.duration
                }
                for phase in self.phases
            ]
        }
