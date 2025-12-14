"""Impact analysis for proposed game changes.

The ImpactAnalyzer helps AI agents understand the consequences of changes
before making them, including dependency analysis and intent validation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from renee.simulation.statistics import ComparisonResult

if TYPE_CHECKING:
    from renee.ecs.world import World
    from renee.schema.registry import SchemaRegistry
    from renee.rules.engine import RuleEngine


@dataclass
class ImpactReport:
    """Report analyzing the impact of a proposed change.

    Provides AI agents with information about what a change will affect,
    potential risks, and suggestions for testing.

    Attributes:
        change_description: Human-readable description of the change
        affected_files: List of file paths that might be affected
        affected_rules: List of rule names that reference this change
        affected_entities: List of entity types/templates affected
        intent_violations: List of intents that might be violated
        simulation_comparison: Statistical comparison if simulation was run
        risk_level: 'low', 'medium', or 'high'
        suggestions: List of suggested test scenarios or actions

    Example:
        change = {
            "type": "modify_component",
            "target": "Health",
            "field": "max",
            "old_value": 100,
            "new_value": 150
        }
        report = analyzer.analyze_change(change)
        print(f"Risk level: {report.risk_level}")
        print(f"Affected rules: {report.affected_rules}")
    """

    change_description: str
    affected_files: list[str]
    affected_rules: list[str]
    affected_entities: list[str]
    intent_violations: list[str]
    simulation_comparison: ComparisonResult | None
    risk_level: str  # 'low', 'medium', 'high'
    suggestions: list[str]

    def __post_init__(self) -> None:
        """Validate risk level."""
        if self.risk_level not in ('low', 'medium', 'high'):
            raise ValueError(
                f"Risk level must be 'low', 'medium', or 'high', got '{self.risk_level}'"
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation
        """
        return {
            "change_description": self.change_description,
            "affected_files": self.affected_files,
            "affected_rules": self.affected_rules,
            "affected_entities": self.affected_entities,
            "intent_violations": self.intent_violations,
            "simulation_comparison": (
                self.simulation_comparison.to_dict()
                if self.simulation_comparison
                else None
            ),
            "risk_level": self.risk_level,
            "suggestions": self.suggestions,
        }

    def to_json(self, indent: int | None = 2) -> str:
        """Export as JSON string.

        Args:
            indent: JSON indentation level (None for compact)

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=indent)

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"ImpactReport: {self.change_description}\n"
            f"  Risk: {self.risk_level.upper()}\n"
            f"  Affected: {len(self.affected_files)} files, "
            f"{len(self.affected_rules)} rules, "
            f"{len(self.affected_entities)} entities\n"
            f"  Intent violations: {len(self.intent_violations)}"
        )


class ImpactAnalyzer:
    """Analyzer for understanding the impact of proposed changes.

    The ImpactAnalyzer helps AI agents make informed decisions by showing:
    - What components, rules, and entities are affected by a change
    - Whether the change violates stated design intents
    - What tests should be run to validate the change

    Example:
        analyzer = ImpactAnalyzer(schema_registry, rule_engine, world)

        change = {
            "type": "modify_component",
            "target": "Health",
            "field": "max",
            "old_value": 100,
            "new_value": 150
        }

        report = analyzer.analyze_change(change)
        if report.risk_level == 'high':
            print("Warning: High-risk change detected!")
            print(f"Suggestions: {report.suggestions}")
    """

    def __init__(
        self,
        schema_registry: SchemaRegistry,
        rule_engine: RuleEngine,
        world: World
    ) -> None:
        """Initialize the impact analyzer.

        Args:
            schema_registry: Registry of component/event/action schemas
            rule_engine: Engine managing game rules
            world: Current game world state
        """
        self.schema_registry = schema_registry
        self.rule_engine = rule_engine
        self.world = world

    def analyze_change(self, change: dict[str, Any]) -> ImpactReport:
        """Analyze the impact of a proposed change.

        Args:
            change: Dictionary describing the change with keys:
                - type: 'modify_component', 'add_rule', 'change_value', etc.
                - target: Name of the component/rule/entity being changed
                - Additional fields depending on change type

        Returns:
            ImpactReport describing the change's effects

        Example:
            change = {
                "type": "modify_component",
                "target": "Health",
                "field": "max",
                "old_value": 100,
                "new_value": 150
            }
            report = analyzer.analyze_change(change)
        """
        change_type = change.get("type", "unknown")
        target = change.get("target", "unknown")

        # Build change description
        description = self._build_description(change)

        # Find affected components
        affected_files = self._find_affected_files(change)
        affected_rules = self._find_affected_rules(change)
        affected_entities = self._find_affected_entities(change)

        # Check for intent violations
        intent_violations = self.check_intents(change)

        # Assess risk level
        risk_level = self._assess_risk(
            change,
            affected_files,
            affected_rules,
            affected_entities,
            intent_violations
        )

        # Generate suggestions
        suggestions = self.suggest_tests(change)

        return ImpactReport(
            change_description=description,
            affected_files=affected_files,
            affected_rules=affected_rules,
            affected_entities=affected_entities,
            intent_violations=intent_violations,
            simulation_comparison=None,  # Could be populated by running simulations
            risk_level=risk_level,
            suggestions=suggestions,
        )

    def find_dependencies(self, component: str) -> list[str]:
        """Find what depends on a component.

        Searches for:
        - Rules that reference the component
        - Other components that reference it
        - Entities that use the component

        Args:
            component: Name of the component

        Returns:
            List of dependency names

        Example:
            deps = analyzer.find_dependencies("Health")
            print(f"Health is used by: {deps}")
        """
        dependencies = []

        # Find rules that use this component
        for rule in self.rule_engine.list_rules():
            # Check if rule name or intent mentions this component
            if component.lower() in rule.name.lower():
                dependencies.append(f"rule:{rule.name}")
            if rule.intent and component.lower() in rule.intent.lower():
                dependencies.append(f"rule:{rule.name}")

        # Find entity templates that use this component
        # (This would require access to entity templates, which we don't have here)
        # In a full implementation, you would scan entity definitions

        # Find other components that might reference this one
        # (This would require introspecting component field types)

        return list(set(dependencies))  # Remove duplicates

    def check_intents(self, change: dict[str, Any]) -> list[str]:
        """Check if a change violates any stated intents.

        Compares the proposed change against intent fields in schemas
        and rules to identify potential design conflicts.

        Args:
            change: Dictionary describing the proposed change

        Returns:
            List of intent violation descriptions

        Example:
            violations = analyzer.check_intents({
                "type": "modify_component",
                "target": "Health",
                "field": "max",
                "new_value": 10
            })
            # Might return: ["Violates Health intent: 'should support varied playstyles'"]
        """
        violations = []
        target = change.get("target", "")

        # Check component schema intent
        if self.schema_registry.has(target):
            schema = self.schema_registry.get(target)
            if hasattr(schema, 'intent') and schema.intent:
                # In a full implementation, you would use LLM or heuristics
                # to check if the change conflicts with the intent
                # For now, we'll do simple keyword matching

                field = change.get("field", "")
                new_value = change.get("new_value")
                old_value = change.get("old_value")

                # Example heuristic: large numeric changes might violate balance intents
                if isinstance(new_value, (int, float)) and isinstance(old_value, (int, float)):
                    if old_value > 0:
                        percent_change = abs((new_value - old_value) / old_value) * 100
                        if percent_change > 50 and "balanced" in schema.intent.lower():
                            violations.append(
                                f"Large change to {target}.{field} ({percent_change:.0f}%) "
                                f"may violate intent: '{schema.intent}'"
                            )

        # Check rule intents
        affected_rules = self._find_affected_rules(change)
        for rule_name in affected_rules:
            rule = self.rule_engine.get_rule(rule_name)
            if rule and rule.intent:
                # Check if change might affect rule's purpose
                if target.lower() in rule.intent.lower():
                    violations.append(
                        f"Change to {target} may affect rule '{rule_name}' "
                        f"intent: '{rule.intent}'"
                    )

        return violations

    def suggest_tests(self, change: dict[str, Any]) -> list[str]:
        """Suggest test scenarios for a proposed change.

        Based on the type of change and what it affects, generates
        suggestions for validating the change.

        Args:
            change: Dictionary describing the proposed change

        Returns:
            List of test suggestions

        Example:
            suggestions = analyzer.suggest_tests({
                "type": "modify_component",
                "target": "Health",
                "field": "max",
            })
            # Returns: ["Test entity survival in combat", "Verify healing mechanics", ...]
        """
        suggestions = []
        change_type = change.get("type", "")
        target = change.get("target", "")

        # Generic suggestions based on change type
        if change_type == "modify_component":
            suggestions.append(
                f"Run simulation with entities using {target} component"
            )
            suggestions.append(
                f"Test all actions that interact with {target}"
            )

            # Specific suggestions based on common component types
            if "health" in target.lower() or "hp" in target.lower():
                suggestions.extend([
                    "Test combat scenarios to ensure entities can still die",
                    "Verify healing mechanics work correctly",
                    "Check damage calculations are balanced",
                ])
            elif "damage" in target.lower():
                suggestions.extend([
                    "Test damage output across different scenarios",
                    "Verify damage scaling matches design intent",
                    "Check critical hit and bonus damage calculations",
                ])
            elif "speed" in target.lower() or "movement" in target.lower():
                suggestions.extend([
                    "Test pathfinding and movement range",
                    "Verify turn order and initiative calculations",
                    "Check for movement exploits or edge cases",
                ])

        elif change_type == "add_rule":
            suggestions.append(
                f"Test rule '{target}' in isolation"
            )
            suggestions.append(
                "Test rule interactions with existing rules"
            )
            suggestions.append(
                "Verify rule priority and execution order"
            )

        elif change_type == "change_value":
            field = change.get("field", "")
            suggestions.append(
                f"Test scenarios where {target}.{field} is critical"
            )
            suggestions.append(
                "Compare before/after values in simulation"
            )

        # Add affected rule tests
        affected_rules = self._find_affected_rules(change)
        if affected_rules:
            suggestions.append(
                f"Test all affected rules: {', '.join(affected_rules[:3])}"
            )

        return suggestions

    def _build_description(self, change: dict[str, Any]) -> str:
        """Build human-readable description of a change.

        Args:
            change: Change dictionary

        Returns:
            Description string
        """
        change_type = change.get("type", "unknown")
        target = change.get("target", "unknown")

        if change_type == "modify_component":
            field = change.get("field", "")
            old_value = change.get("old_value")
            new_value = change.get("new_value")
            return f"Modify {target}.{field}: {old_value} → {new_value}"

        elif change_type == "add_rule":
            return f"Add new rule: {target}"

        elif change_type == "change_value":
            field = change.get("field", "")
            return f"Change {target}.{field}"

        else:
            return f"{change_type}: {target}"

    def _find_affected_files(self, change: dict[str, Any]) -> list[str]:
        """Find files that might be affected by the change.

        Args:
            change: Change dictionary

        Returns:
            List of file paths
        """
        affected = []
        target = change.get("target", "")

        # In a full implementation, you would scan the codebase
        # For now, return likely file locations
        if change.get("type") == "modify_component":
            affected.append(f"schemas/components.yaml")
            affected.append(f"entities/templates/{target.lower()}.yaml")
        elif change.get("type") == "add_rule":
            affected.append(f"rules/{target.lower()}.py")

        return affected

    def _find_affected_rules(self, change: dict[str, Any]) -> list[str]:
        """Find rules that might be affected by the change.

        Args:
            change: Change dictionary

        Returns:
            List of rule names
        """
        affected = []
        target = change.get("target", "")

        # Search rule names and intents for references to target
        for rule in self.rule_engine.list_rules():
            if target.lower() in rule.name.lower():
                affected.append(rule.name)
            elif rule.intent and target.lower() in rule.intent.lower():
                affected.append(rule.name)

        return affected

    def _find_affected_entities(self, change: dict[str, Any]) -> list[str]:
        """Find entity types/templates affected by the change.

        Args:
            change: Change dictionary

        Returns:
            List of entity type names
        """
        affected = []
        target = change.get("target", "")

        # In a full implementation, you would:
        # 1. Scan entity templates for components matching target
        # 2. Query world for entities with that component
        # 3. Return list of entity types

        # For now, return placeholder
        if change.get("type") == "modify_component":
            affected.append(f"entities_with_{target.lower()}")

        return affected

    def _assess_risk(
        self,
        change: dict[str, Any],
        affected_files: list[str],
        affected_rules: list[str],
        affected_entities: list[str],
        intent_violations: list[str]
    ) -> str:
        """Assess the risk level of a change.

        Args:
            change: Change dictionary
            affected_files: List of affected files
            affected_rules: List of affected rules
            affected_entities: List of affected entities
            intent_violations: List of intent violations

        Returns:
            Risk level: 'low', 'medium', or 'high'
        """
        # High risk if there are intent violations
        if intent_violations:
            return 'high'

        # High risk if many things are affected
        total_affected = len(affected_files) + len(affected_rules) + len(affected_entities)
        if total_affected > 10:
            return 'high'
        elif total_affected > 5:
            return 'medium'

        # High risk for large value changes
        if change.get("type") == "modify_component":
            old_value = change.get("old_value")
            new_value = change.get("new_value")
            if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
                if old_value > 0:
                    percent_change = abs((new_value - old_value) / old_value) * 100
                    if percent_change > 50:
                        return 'high'
                    elif percent_change > 20:
                        return 'medium'

        # Default to low risk
        return 'low'
