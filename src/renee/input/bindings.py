"""Input bindings loaded from YAML/JSON.

Bindings map physical inputs (key names) to logical actions (strings).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from renee.errors import ValidationError


class InputBindings:
    def __init__(self, *, bindings: Mapping[str, str] | None = None) -> None:
        self._bindings: dict[str, str] = dict(bindings or {})

    def action_for_key(self, key: str) -> str | None:
        return self._bindings.get(key)

    def set(self, key: str, action: str) -> None:
        self._bindings[key] = action

    def as_dict(self) -> dict[str, str]:
        return dict(self._bindings)

    @classmethod
    def load(cls, path: str | Path) -> "InputBindings":
        p = Path(path)
        if not p.exists():
            raise ValidationError(
                "bindings_not_found",
                f"Bindings file not found: {p}",
                hint="Provide a valid bindings YAML/JSON path.",
            )
        suffix = p.suffix.lower()
        text = p.read_text(encoding="utf-8")
        if suffix == ".json":
            data = json.loads(text)
        elif suffix in {".yaml", ".yml"}:
            try:
                import yaml  # type: ignore[import-not-found]
            except ModuleNotFoundError as e:
                raise ValidationError(
                    "yaml_dependency_missing",
                    "YAML bindings require PyYAML.",
                    hint="Install with: pip install pyyaml",
                    context={"path": str(p)},
                ) from e
            data = yaml.safe_load(text)  # type: ignore[attr-defined]
        else:
            raise ValidationError(
                "bindings_unsupported_format",
                f"Unsupported bindings file format: {suffix}",
                hint="Use .yaml/.yml or .json.",
            )

        if not isinstance(data, Mapping):
            raise ValidationError("bindings_invalid", "Bindings file must parse to a mapping.")

        raw = data.get("bindings", data)
        if not isinstance(raw, Mapping):
            raise ValidationError("bindings_invalid", "Bindings must be a mapping of key->action.")

        bindings: dict[str, str] = {}
        for k, v in raw.items():
            if not isinstance(k, str) or not isinstance(v, str):
                raise ValidationError("bindings_invalid", "Bindings keys and values must be strings.")
            bindings[k] = v
        return cls(bindings=bindings)

    def match_pressed(self, keys_pressed: set[str]) -> set[str]:
        actions: set[str] = set()
        for key in keys_pressed:
            action = self.action_for_key(key)
            if action is not None:
                actions.add(action)
        return actions

