"""Schema registry.

This module intentionally avoids hard dependencies on third-party libraries at
import time. YAML/Pydantic integration is used when installed, but the core
registry remains usable with the standard library.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field, make_dataclass
import json
from pathlib import Path
import re
from typing import Any, Iterable, Literal, Mapping, Sequence, TypeAlias, cast

from renee.errors import SchemaError
from renee.types import AssetRef, DiceRoll, Duration, EntityId, Formula, Position, Probability

SchemaKind: TypeAlias = Literal["component", "event", "action"]

SCHEMA_MISSING: Any = object()


@dataclass(frozen=True, slots=True)
class SchemaField:
    name: str
    type: str
    required: bool = True
    default: Any = SCHEMA_MISSING
    description: str | None = None
    constraints: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SchemaDefinition:
    name: str
    kind: SchemaKind
    fields: tuple[SchemaField, ...]
    intent: str | None = None

    def field_map(self) -> dict[str, SchemaField]:
        return {f.name: f for f in self.fields}


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    field: str
    message: str


@dataclass(frozen=True, slots=True)
class ValidationReport:
    ok: bool
    issues: tuple[ValidationIssue, ...] = ()

    @classmethod
    def success(cls) -> "ValidationReport":
        return cls(ok=True, issues=())

    @classmethod
    def failure(cls, issues: Iterable[ValidationIssue]) -> "ValidationReport":
        return cls(ok=False, issues=tuple(issues))


_TYPE_RE = re.compile(r"^(?P<outer>\w+)\[(?P<inner>.+)\]$")

_BUILTIN_COMPONENT_TYPES: dict[str, type] = {
    "Position": Position,
}


class SchemaRegistry:
    """Registry for component/event/action schemas.

    Key features:
    - Load schemas from YAML/JSON/TOML files
    - Introspect schemas at runtime
    - Validate and coerce data at boundaries
    - Generate fast runtime dataclasses from schemas
    """

    def __init__(self) -> None:
        self._schemas: dict[tuple[SchemaKind, str], SchemaDefinition] = {}
        self._generated_types: dict[str, type] = {}

    def register(self, schema: SchemaDefinition) -> None:
        key = (schema.kind, schema.name)
        if key in self._schemas:
            raise SchemaError(
                "schema_already_registered",
                f"Schema already registered: {schema.kind}:{schema.name}",
                hint="Use a unique name per kind, or unregister first.",
                context={"kind": schema.kind, "name": schema.name},
            )
        self._schemas[key] = schema

    def get(self, name: str, *, kind: SchemaKind) -> SchemaDefinition:
        key = (kind, name)
        if key not in self._schemas:
            raise SchemaError(
                "schema_not_found",
                f"Schema not found: {kind}:{name}",
                hint="Load schemas first or check the schema name.",
                context={"kind": kind, "name": name, "available": self.list(kind=kind)},
            )
        return self._schemas[key]

    def list(self, *, kind: SchemaKind | None = None) -> list[str]:
        names: list[str] = []
        for (k, name), _schema in self._schemas.items():
            if kind is None or k == kind:
                names.append(name)
        names.sort()
        return names

    def as_json(self, name: str, *, kind: SchemaKind) -> dict[str, Any]:
        schema = self.get(name, kind=kind)
        return {
            "name": schema.name,
            "kind": schema.kind,
            "intent": schema.intent,
            "fields": [
                {
                    "name": f.name,
                    "type": f.type,
                    "required": f.required,
                    "default": None if f.default is SCHEMA_MISSING else f.default,
                    "description": f.description,
                    "constraints": dict(f.constraints),
                }
                for f in schema.fields
            ],
        }

    def load_from_path(self, path: str | Path) -> None:
        p = Path(path)
        data = self._load_data(p)
        self.load_from_mapping(data)

    def load_from_mapping(self, data: Mapping[str, Any]) -> None:
        """Load schemas from a mapping (already parsed YAML/JSON/TOML)."""

        for kind_key, kind in (("components", "component"), ("events", "event"), ("actions", "action")):
            block = data.get(kind_key, {})
            if not block:
                continue
            if not isinstance(block, Mapping):
                raise SchemaError(
                    "schema_invalid_format",
                    f"Top-level '{kind_key}' must be a mapping.",
                    hint=f"Expected {kind_key}: {{ Name: {{ fields: ... }} }}",
                )
            for name, raw in block.items():
                self.register(self._parse_schema(name=str(name), kind=cast(SchemaKind, kind), raw=raw))

    def validate(self, name: str, raw: Mapping[str, Any], *, kind: SchemaKind) -> ValidationReport:
        schema = self.get(name, kind=kind)
        issues: list[ValidationIssue] = []
        fields = schema.field_map()

        for field_name, field_def in fields.items():
            if field_name not in raw:
                if field_def.required and field_def.default is SCHEMA_MISSING:
                    issues.append(ValidationIssue(field=field_name, message="Missing required field."))
                continue
            try:
                _ = self._coerce(field_def.type, raw[field_name])
            except Exception as e:  # noqa: BLE001 - boundary error capture
                issues.append(ValidationIssue(field=field_name, message=str(e)))
                continue
            issues.extend(self._validate_constraints(field_name, field_def, raw[field_name]))

        for extra in raw.keys():
            if extra not in fields:
                issues.append(ValidationIssue(field=str(extra), message="Unknown field."))

        return ValidationReport.success() if not issues else ValidationReport.failure(issues)

    def instantiate(self, name: str, raw: Mapping[str, Any], *, kind: SchemaKind) -> Any:
        """Validate and coerce data to a generated dataclass instance."""

        report = self.validate(name, raw, kind=kind)
        if not report.ok:
            raise SchemaError(
                "schema_validation_failed",
                f"Validation failed for {kind}:{name}",
                hint="Fix the reported fields, or update the schema to match your data.",
                context={"kind": kind, "name": name, "issues": [i.__dict__ for i in report.issues]},
            )

        schema = self.get(name, kind=kind)
        cls = self.generated_type(name, kind=kind)
        kwargs: dict[str, Any] = {}
        for field_def in schema.fields:
            if field_def.name in raw:
                kwargs[field_def.name] = self._coerce(field_def.type, raw[field_def.name])
            elif field_def.default is not SCHEMA_MISSING:
                kwargs[field_def.name] = field_def.default
            else:
                kwargs[field_def.name] = None if not field_def.required else None
        return cls(**kwargs)

    def generated_type(self, name: str, *, kind: SchemaKind) -> type:
        """Get (or generate) the runtime dataclass type for a schema."""

        if kind == "component" and name in _BUILTIN_COMPONENT_TYPES:
            # If a schema is provided for a builtin runtime type, validate it matches.
            try:
                schema = self.get(name, kind=kind)
            except SchemaError:
                return _BUILTIN_COMPONENT_TYPES[name]

            dc_fields = {f.name for f in dataclasses.fields(_BUILTIN_COMPONENT_TYPES[name])}
            schema_fields = {f.name for f in schema.fields}
            if dc_fields != schema_fields:
                raise SchemaError(
                    "schema_builtin_mismatch",
                    f"Schema for builtin component '{name}' does not match runtime fields.",
                    hint=f"Expected fields {sorted(dc_fields)!r}, got {sorted(schema_fields)!r}.",
                    context={"name": name, "expected": sorted(dc_fields), "got": sorted(schema_fields)},
                )
            return _BUILTIN_COMPONENT_TYPES[name]

        cache_key = f"{kind}:{name}"
        if cache_key in self._generated_types:
            return self._generated_types[cache_key]
        schema = self.get(name, kind=kind)
        cls = self._make_dataclass(schema)
        self._generated_types[cache_key] = cls
        return cls

    def _make_dataclass(self, schema: SchemaDefinition) -> type:
        non_default_fields_spec: list[tuple[str, Any] | tuple[str, Any, Any]] = []
        default_fields_spec: list[tuple[str, Any] | tuple[str, Any, Any]] = []
        for f in schema.fields:
            t = self._python_type(f.type)
            if not f.required:
                t = t | None
            if f.required and f.default is SCHEMA_MISSING:
                non_default_fields_spec.append((f.name, t))
                continue

            if f.default is SCHEMA_MISSING:
                default_fields_spec.append((f.name, t, field(default=None)))
            else:
                default_fields_spec.append((f.name, t, field(default=f.default)))

        cls = make_dataclass(
            schema.name,
            list(non_default_fields_spec) + list(default_fields_spec),
            frozen=True,
            slots=True,
            namespace={"__doc__": f"{schema.kind} schema {schema.name}"},
        )
        cls.__module__ = "renee.schema.generated"
        return cls

    def _parse_schema(self, *, name: str, kind: SchemaKind, raw: Any) -> SchemaDefinition:
        if not isinstance(raw, Mapping):
            raise SchemaError(
                "schema_invalid_definition",
                f"Schema '{name}' must be a mapping with a 'fields' key.",
                hint="Example: Move: { fields: { entity: {type: EntityId}, to: {type: Position} } }",
            )
        raw_fields = raw.get("fields", {})
        if not isinstance(raw_fields, Mapping):
            raise SchemaError(
                "schema_invalid_fields",
                f"Schema '{name}'.fields must be a mapping.",
                hint="Example: fields: { amount: {type: int, min: 0} }",
            )

        intent = raw.get("intent")
        if intent is not None and not isinstance(intent, str):
            raise SchemaError("schema_invalid_intent", f"Schema '{name}'.intent must be a string.")

        fields: list[SchemaField] = []
        for field_name, field_raw in raw_fields.items():
            fields.append(self._parse_field(str(field_name), field_raw))
        fields.sort(key=lambda f: f.name)
        return SchemaDefinition(name=name, kind=kind, fields=tuple(fields), intent=cast(str | None, intent))

    def _parse_field(self, field_name: str, raw: Any) -> SchemaField:
        if isinstance(raw, str):
            return SchemaField(name=field_name, type=raw)
        if not isinstance(raw, Mapping):
            raise SchemaError(
                "schema_invalid_field",
                f"Field '{field_name}' must be a type string or mapping.",
                hint="Example: x: int  or  x: {type: int, min: 0, default: 1}",
            )
        t = raw.get("type")
        if not isinstance(t, str):
            raise SchemaError(
                "schema_invalid_field_type",
                f"Field '{field_name}'.type must be a string.",
            )
        required = raw.get("required", True)
        if not isinstance(required, bool):
            raise SchemaError("schema_invalid_required", f"Field '{field_name}'.required must be boolean.")
        default = raw.get("default", SCHEMA_MISSING)
        description = raw.get("description")
        if description is not None and not isinstance(description, str):
            raise SchemaError("schema_invalid_description", f"Field '{field_name}'.description must be string.")

        constraints: dict[str, Any] = {}
        for key in ("min", "max", "enum", "pattern", "min_length", "max_length"):
            if key in raw:
                constraints[key] = raw[key]

        return SchemaField(
            name=field_name,
            type=t,
            required=required,
            default=default,
            description=cast(str | None, description),
            constraints=constraints,
        )

    def _validate_constraints(self, field_name: str, field_def: SchemaField, value: Any) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        c = field_def.constraints

        if "enum" in c:
            enum = c["enum"]
            if isinstance(enum, Sequence) and value not in enum:
                issues.append(ValidationIssue(field=field_name, message=f"Value must be one of {list(enum)!r}."))

        if isinstance(value, (int, float)):
            if "min" in c and value < c["min"]:
                issues.append(ValidationIssue(field=field_name, message=f"Value must be >= {c['min']}."))
            if "max" in c and value > c["max"]:
                issues.append(ValidationIssue(field=field_name, message=f"Value must be <= {c['max']}."))

        if isinstance(value, str):
            if "min_length" in c and len(value) < int(c["min_length"]):
                issues.append(ValidationIssue(field=field_name, message="String is too short."))
            if "max_length" in c and len(value) > int(c["max_length"]):
                issues.append(ValidationIssue(field=field_name, message="String is too long."))
            if "pattern" in c:
                pattern = str(c["pattern"])
                if re.match(pattern, value) is None:
                    issues.append(ValidationIssue(field=field_name, message=f"String must match /{pattern}/."))

        return issues

    def _python_type(self, type_str: str) -> Any:
        outer, inner = self._parse_generic(type_str)
        if outer == "list":
            return list[self._python_type(inner)]
        if outer == "dict":
            key_str, value_str = self._split_dict_args(inner)
            return dict[self._python_type(key_str), self._python_type(value_str)]
        return self._base_python_type(type_str)

    def _base_python_type(self, type_str: str) -> type:
        primitives: dict[str, type] = {"int": int, "float": float, "str": str, "bool": bool, "any": object}
        if type_str in primitives:
            return primitives[type_str]
        semantic: dict[str, type] = {
            "EntityId": int,
            "AssetRef": str,
            "Probability": float,
            "Position": Position,
            "DiceRoll": DiceRoll,
            "Duration": Duration,
            "Formula": Formula,
        }
        if type_str in semantic:
            return semantic[type_str]
        raise SchemaError(
            "schema_unknown_type",
            f"Unknown type: {type_str}",
            hint="Use a primitive (int/float/str/bool) or a known semantic type.",
            context={"type": type_str},
        )

    def _coerce(self, type_str: str, value: Any) -> Any:
        outer, inner = self._parse_generic(type_str)
        if outer == "list":
            if not isinstance(value, list):
                raise TypeError(f"Expected list[{inner}], got {type(value).__name__}")
            return [self._coerce(inner, v) for v in value]
        if outer == "dict":
            if not isinstance(value, Mapping):
                raise TypeError(f"Expected dict[{inner}], got {type(value).__name__}")
            key_str, value_str = self._split_dict_args(inner)
            return {self._coerce(key_str, k): self._coerce(value_str, v) for k, v in value.items()}
        return self._coerce_base(type_str, value)

    def _coerce_base(self, type_str: str, value: Any) -> Any:
        if type_str == "int":
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError("Expected int")
            return value
        if type_str == "float":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError("Expected float")
            return float(value)
        if type_str == "str":
            if not isinstance(value, str):
                raise TypeError("Expected str")
            return value
        if type_str == "bool":
            if not isinstance(value, bool):
                raise TypeError("Expected bool")
            return value
        if type_str == "any":
            return value
        if type_str == "EntityId":
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError("Expected EntityId (int)")
            return EntityId(value)
        if type_str == "AssetRef":
            if not isinstance(value, str):
                raise TypeError("Expected AssetRef (str)")
            return AssetRef(value)
        if type_str == "Probability":
            return Probability(cast(float, value))
        if type_str == "Position":
            if isinstance(value, Position):
                return value
            if isinstance(value, Mapping):
                return Position(x=int(value["x"]), y=int(value["y"]))
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) == 2:
                return Position(x=int(value[0]), y=int(value[1]))
            raise TypeError("Expected Position (mapping with x/y or sequence of 2 ints)")
        if type_str == "DiceRoll":
            if isinstance(value, DiceRoll):
                return value
            if isinstance(value, str):
                return DiceRoll.parse(value)
            raise TypeError("Expected DiceRoll (string like '2d6+3')")
        if type_str == "Duration":
            if isinstance(value, Duration):
                return value
            if isinstance(value, int):
                return Duration(turns=value)
            if isinstance(value, str):
                return Duration.parse(value)
            raise TypeError("Expected Duration (int turns or string like '3 turns')")
        if type_str == "Formula":
            if isinstance(value, Formula):
                return value
            if isinstance(value, str):
                return Formula(value)
            raise TypeError("Expected Formula (string expression)")

        raise SchemaError("schema_unknown_type", f"Unknown type: {type_str}")

    def _parse_generic(self, type_str: str) -> tuple[str | None, str]:
        s = type_str.strip()
        m = _TYPE_RE.match(s)
        if not m:
            return (None, s)
        outer = m.group("outer").lower()
        inner = m.group("inner").strip()
        return (outer, inner)

    def _split_dict_args(self, inner: str) -> tuple[str, str]:
        # Split "K, V" while allowing nested generics.
        depth = 0
        for i, ch in enumerate(inner):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
            elif ch == "," and depth == 0:
                left = inner[:i].strip()
                right = inner[i + 1 :].strip()
                if not left or not right:
                    break
                return left, right
        raise SchemaError(
            "schema_invalid_dict_type",
            f"Invalid dict type arguments: {inner!r}",
            hint="Use dict[key_type, value_type], e.g. dict[str, int]",
        )

    def _load_data(self, path: Path) -> Mapping[str, Any]:
        if not path.exists():
            raise SchemaError(
                "schema_file_not_found",
                f"Schema file not found: {path}",
                hint="Provide a valid schema path.",
            )

        suffix = path.suffix.lower()
        text = path.read_text(encoding="utf-8")

        if suffix in {".json"}:
            return cast(Mapping[str, Any], json.loads(text))
        if suffix in {".toml"}:
            import tomllib  # stdlib in 3.11+

            return cast(Mapping[str, Any], tomllib.loads(text))
        if suffix in {".yaml", ".yml"}:
            try:
                import yaml  # type: ignore[import-not-found]
            except ModuleNotFoundError as e:
                raise SchemaError(
                    "yaml_dependency_missing",
                    "YAML support requires PyYAML.",
                    hint="Install with: pip install pyyaml",
                    context={"path": str(path)},
                ) from e
            data = yaml.safe_load(text)  # type: ignore[attr-defined]
            if not isinstance(data, Mapping):
                raise SchemaError(
                    "schema_invalid_yaml",
                    f"Schema file must parse to a mapping, got {type(data).__name__}",
                )
            return cast(Mapping[str, Any], data)

        raise SchemaError(
            "schema_unsupported_format",
            f"Unsupported schema file format: {suffix}",
            hint="Use .yaml/.yml, .json, or .toml.",
            context={"path": str(path)},
        )
