"""Asset manifest management.

Provides a registry of all assets in a game with validation capabilities.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from renee.types import AssetRef


@dataclass
class AssetEntry:
    """A single asset in the manifest.

    Attributes:
        name: Unique identifier for this asset.
        category: Asset category ('sprites', 'sounds', 'fonts', 'tilemaps').
        path: Relative path to the asset file.
        metadata: Additional asset-specific metadata (dimensions, duration, etc).
    """

    name: str
    category: str
    path: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "category": self.category,
            "path": self.path,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AssetEntry:
        """Create from dictionary."""
        return cls(
            name=data["name"],
            category=data["category"],
            path=data["path"],
            metadata=data.get("metadata", {}),
        )

    def to_asset_ref(self) -> AssetRef:
        """Convert to AssetRef."""
        return AssetRef(category=self.category, name=self.name)


class AssetManifest:
    """Registry of all assets in a game.

    The manifest tracks all game assets and provides validation for asset references.
    It can be saved to/loaded from YAML files for persistence.
    """

    def __init__(self) -> None:
        """Create an empty asset manifest."""
        self._assets: dict[str, AssetEntry] = {}
        self._by_category: dict[str, list[AssetEntry]] = {}

    def register(self, entry: AssetEntry) -> None:
        """Register an asset in the manifest.

        Args:
            entry: The asset entry to register.

        Raises:
            ValueError: If an asset with this name already exists.
        """
        if entry.name in self._assets:
            existing = self._assets[entry.name]
            if existing.category != entry.category or existing.path != entry.path:
                raise ValueError(
                    f"Asset name '{entry.name}' already registered with different properties. "
                    f"Existing: {existing.category}:{existing.path}, "
                    f"New: {entry.category}:{entry.path}"
                )
            # Same asset, just update metadata
            existing.metadata.update(entry.metadata)
            return

        self._assets[entry.name] = entry

        # Update category index
        if entry.category not in self._by_category:
            self._by_category[entry.category] = []
        self._by_category[entry.category].append(entry)

    def get(self, name: str) -> AssetEntry | None:
        """Get asset by name.

        Args:
            name: The asset name to look up.

        Returns:
            The asset entry, or None if not found.
        """
        return self._assets.get(name)

    def get_by_category(self, category: str) -> list[AssetEntry]:
        """Get all assets in a category.

        Args:
            category: The category to filter by ('sprites', 'sounds', etc).

        Returns:
            List of assets in this category (may be empty).
        """
        return self._by_category.get(category, []).copy()

    def validate_ref(self, ref: AssetRef) -> bool:
        """Check if an AssetRef is valid.

        Args:
            ref: The asset reference to validate.

        Returns:
            True if the asset exists with the correct category, False otherwise.
        """
        entry = self._assets.get(ref.name)
        if entry is None:
            return False
        return entry.category == ref.category

    def list_all(self) -> list[AssetEntry]:
        """List all registered assets.

        Returns:
            All assets in the manifest.
        """
        return list(self._assets.values())

    def categories(self) -> list[str]:
        """Get all categories with registered assets.

        Returns:
            List of category names.
        """
        return list(self._by_category.keys())

    @classmethod
    def from_yaml(cls, path: str) -> AssetManifest:
        """Load manifest from YAML file.

        Args:
            path: Path to the YAML file.

        Returns:
            Loaded asset manifest.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the YAML format is invalid.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Manifest file not found: {path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError(f"Invalid manifest format: expected dict, got {type(data)}")

        manifest = cls()

        # Support two formats:
        # 1. List of assets under 'assets' key
        # 2. Assets organized by category
        if "assets" in data:
            # Format 1: flat list
            for asset_data in data["assets"]:
                entry = AssetEntry.from_dict(asset_data)
                manifest.register(entry)
        else:
            # Format 2: organized by category
            for category, assets in data.items():
                if isinstance(assets, list):
                    for asset_data in assets:
                        # Ensure category is set
                        if isinstance(asset_data, dict):
                            asset_data["category"] = category
                            entry = AssetEntry.from_dict(asset_data)
                            manifest.register(entry)

        return manifest

    def to_yaml(self, path: str) -> None:
        """Save manifest to YAML file.

        Args:
            path: Path where the YAML file should be written.
        """
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Organize by category for better readability
        data: dict[str, list[dict[str, Any]]] = {}
        for category in sorted(self._by_category.keys()):
            data[category] = [
                {
                    "name": entry.name,
                    "path": entry.path,
                    "metadata": entry.metadata,
                }
                for entry in sorted(self._by_category[category], key=lambda e: e.name)
            ]

        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def to_json(self) -> dict[str, Any]:
        """JSON representation for AI querying.

        Returns:
            Dictionary with manifest data in a queryable format.
        """
        return {
            "total_assets": len(self._assets),
            "categories": {
                category: len(assets)
                for category, assets in self._by_category.items()
            },
            "assets": {
                category: [
                    {
                        "name": entry.name,
                        "path": entry.path,
                        "metadata": entry.metadata,
                    }
                    for entry in sorted(assets, key=lambda e: e.name)
                ]
                for category, assets in sorted(self._by_category.items())
            },
        }

    def __len__(self) -> int:
        """Get total number of registered assets."""
        return len(self._assets)

    def __contains__(self, name: str) -> bool:
        """Check if an asset name is registered."""
        return name in self._assets

    def __repr__(self) -> str:
        """String representation."""
        total = len(self._assets)
        categories = len(self._by_category)
        return f"AssetManifest({total} assets across {categories} categories)"
