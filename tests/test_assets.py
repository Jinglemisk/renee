"""Tests for asset registry."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from renee.assets import AssetRegistry


class TestAssetRegistry:
    def test_scan_and_validate(self, tmp_path: Path) -> None:
        assets = tmp_path / "assets"
        (assets / "sprites").mkdir(parents=True)
        (assets / "sounds").mkdir(parents=True)

        (assets / "sprites" / "hero.png").write_bytes(b"not an image")
        (assets / "sounds" / "hit.wav").write_bytes(b"not a sound")

        reg = AssetRegistry.scan(assets)
        reg.validate_ref("sprites", "hero")
        reg.validate_ref("sounds", "hit")

        manifest_path = tmp_path / "manifest.json"
        reg.write_manifest(manifest_path)
        assert manifest_path.exists()

    def test_generate_constants(self, tmp_path: Path) -> None:
        assets = tmp_path / "assets"
        (assets / "sprites").mkdir(parents=True)
        (assets / "sprites" / "goblin_idle.png").write_bytes(b"x")

        reg = AssetRegistry.scan(assets)
        out = tmp_path / "assets_constants.py"
        reg.generate_constants(out)

        spec = importlib.util.spec_from_file_location("assets_constants", out)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[assignment]
        assert mod.Assets.Sprites.GOBLIN_IDLE == "goblin_idle"

