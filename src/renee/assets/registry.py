"""Asset registry.

The asset registry turns directories into validated names and (optionally)
generates Python constants to avoid magic strings.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping

from renee.errors import ValidationError


AssetManifest = dict[str, dict[str, str]]


@dataclass(frozen=True, slots=True)
class AssetRegistry:
    root: Path
    manifest: AssetManifest

    @classmethod
    def scan(cls, root: str | Path) -> "AssetRegistry":
        root_path = Path(root)
        if not root_path.exists():
            raise ValidationError(
                "assets_root_missing",
                f"Assets root not found: {root_path}",
                hint="Point to a directory containing sprites/sounds/fonts subfolders.",
            )

        manifest: AssetManifest = {"sprites": {}, "sounds": {}, "fonts": {}}
        for kind in manifest.keys():
            dir_path = root_path / kind
            if not dir_path.exists():
                continue
            for file in dir_path.rglob("*"):
                if not file.is_file():
                    continue
                name = file.stem
                if name in manifest[kind]:
                    raise ValidationError(
                        "asset_name_collision",
                        f"Duplicate asset name '{name}' in {kind}.",
                        hint="Rename one of the files to keep stems unique per asset type.",
                        context={"kind": kind, "name": name},
                    )
                manifest[kind][name] = str(file.relative_to(root_path).as_posix())

        return cls(root=root_path, manifest=manifest)

    def validate_ref(self, kind: str, name: str) -> None:
        if kind not in self.manifest:
            raise ValidationError(
                "asset_kind_unknown",
                f"Unknown asset kind: {kind}",
                hint=f"Known kinds: {sorted(self.manifest.keys())}",
            )
        if name not in self.manifest[kind]:
            raise ValidationError(
                "asset_not_found",
                f"Unknown {kind} asset: {name}",
                hint="Run an asset scan and ensure the file exists under the correct directory.",
                context={"kind": kind, "name": name},
            )

    def path_for(self, kind: str, name: str) -> Path:
        self.validate_ref(kind, name)
        return self.root / self.manifest[kind][name]

    def write_manifest(self, path: str | Path) -> None:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        data: Mapping[str, Any] = {"assets": self.manifest}

        if out.suffix.lower() in {".yaml", ".yml"}:
            try:
                import yaml  # type: ignore[import-not-found]
            except ModuleNotFoundError:
                # Fallback to JSON with a clear extension.
                out = out.with_suffix(".json")
                out.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
                return
            out.write_text(yaml.safe_dump(data, sort_keys=True), encoding="utf-8")  # type: ignore[attr-defined]
            return

        out.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    def generate_constants(self, path: str | Path) -> None:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)

        def _class_block(class_name: str, items: Mapping[str, str]) -> str:
            lines = [f"class {class_name}:", '    """Generated asset constants."""']
            if not items:
                lines.append("    pass")
                return "\n".join(lines)
            for name in sorted(items.keys()):
                const = re.sub(r"[^A-Z0-9_]", "_", name.upper())
                if const and const[0].isdigit():
                    const = "_" + const
                lines.append(f"    {const} = {name!r}")
            return "\n".join(lines)

        sprites = _class_block("Sprites", self.manifest.get("sprites", {}))
        sounds = _class_block("Sounds", self.manifest.get("sounds", {}))
        fonts = _class_block("Fonts", self.manifest.get("fonts", {}))

        module = "\n\n".join(
            [
                '"""Generated asset constants.\n\nDo not edit manually; regenerate from the asset manifest."""',
                sprites,
                sounds,
                fonts,
                "class Assets:\n    Sprites = Sprites\n    Sounds = Sounds\n    Fonts = Fonts\n",
            ]
        )
        out.write_text(module, encoding="utf-8")
