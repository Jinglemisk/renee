"""Tests for schema registry."""

import pytest

from renee.errors import SchemaError
from renee.schema import SchemaRegistry
from renee.types import EntityId, Position


class TestSchemaRegistry:
    def test_load_list_get(self) -> None:
        reg = SchemaRegistry()
        reg.load_from_mapping(
            {
                "components": {
                    "Health": {
                        "fields": {
                            "current": {"type": "int", "min": 0},
                            "max": {"type": "int", "min": 0},
                        }
                    }
                },
                "actions": {
                    "Move": {"fields": {"entity": {"type": "EntityId"}, "to": {"type": "Position"}}}
                },
            }
        )

        assert reg.list(kind="component") == ["Health"]
        assert reg.list(kind="action") == ["Move"]
        assert reg.get("Health", kind="component").name == "Health"

    def test_validate_and_instantiate(self) -> None:
        reg = SchemaRegistry()
        reg.load_from_mapping(
            {
                "actions": {
                    "Move": {
                        "fields": {
                            "entity": {"type": "EntityId"},
                            "to": {"type": "Position"},
                            "speed": {"type": "int", "required": False, "default": 1},
                        }
                    }
                }
            }
        )

        report = reg.validate("Move", {"entity": 1, "to": {"x": 2, "y": 3}}, kind="action")
        assert report.ok

        move = reg.instantiate("Move", {"entity": 1, "to": {"x": 2, "y": 3}}, kind="action")
        assert move.entity == EntityId(1)
        assert move.to == Position(x=2, y=3)
        assert move.speed == 1

    def test_unknown_type_raises(self) -> None:
        reg = SchemaRegistry()
        reg.load_from_mapping({"components": {"Bad": {"fields": {"x": {"type": "NotAType"}}}}})
        with pytest.raises(SchemaError):
            reg.generated_type("Bad", kind="component")

