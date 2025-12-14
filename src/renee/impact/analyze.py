"""Minimal impact analysis.

Given a schema name, find other schemas that reference it via field type strings.
This is intentionally conservative and designed to be predictable for AI tools.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from renee.schema import SchemaKind, SchemaRegistry


@dataclass(frozen=True, slots=True)
class ImpactReport:
    kind: SchemaKind
    name: str
    referenced_by: dict[SchemaKind, list[str]]


def analyze_schema_impact(registry: SchemaRegistry, *, kind: SchemaKind, name: str) -> ImpactReport:
    _ = registry.get(name, kind=kind)  # validates existence
    needle = re.compile(rf"\\b{re.escape(name)}\\b")
    referenced_by: dict[SchemaKind, list[str]] = {"component": [], "event": [], "action": []}

    for other_kind in ("component", "event", "action"):
        for other_name in registry.list(kind=other_kind):  # type: ignore[arg-type]
            if other_kind == kind and other_name == name:
                continue
            schema = registry.get(other_name, kind=other_kind)  # type: ignore[arg-type]
            for f in schema.fields:
                if needle.search(f.type):
                    referenced_by[other_kind].append(other_name)  # type: ignore[index]
                    break
        referenced_by[other_kind].sort()  # type: ignore[index]

    return ImpactReport(kind=kind, name=name, referenced_by=referenced_by)

