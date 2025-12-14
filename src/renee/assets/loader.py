"""Asset loading utilities.

Provides lazy loading and caching of game assets with optional pygame support.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from renee.assets.manifest import AssetManifest

# Optional pygame import
try:
    import pygame

    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class AssetLoader:
    """Loads and caches game assets.

    The loader uses the asset manifest to find assets and provides type-specific
    loading methods. Assets are cached after first load for performance.

    pygame imports are optional - if pygame is not available, placeholders are returned.
    """

    def __init__(self, manifest: AssetManifest, base_path: str = "assets") -> None:
        """Create an asset loader.

        Args:
            manifest: The asset manifest to use for lookups.
            base_path: Base directory for asset files (default: 'assets').
        """
        self._manifest = manifest
        self._base_path = Path(base_path)
        self._cache: dict[str, Any] = {}
        self._fonts: dict[tuple[str, int], Any] = {}  # Font cache by (name, size)

    def _get_asset_path(self, name: str) -> Path:
        """Get the full path to an asset.

        Args:
            name: Asset name.

        Returns:
            Resolved path to the asset file.

        Raises:
            ValueError: If asset is not found in manifest.
        """
        entry = self._manifest.get(name)
        if entry is None:
            raise ValueError(f"Asset '{name}' not found in manifest")
        return self._base_path / entry.path

    def load_sprite(self, name: str) -> Any:
        """Load a sprite (returns pygame Surface or placeholder).

        Args:
            name: Name of the sprite asset.

        Returns:
            pygame.Surface if pygame is available, otherwise a placeholder dict.

        Raises:
            ValueError: If asset not found or wrong category.
            FileNotFoundError: If asset file doesn't exist.
        """
        # Check cache first
        if name in self._cache:
            return self._cache[name]

        # Validate category
        entry = self._manifest.get(name)
        if entry is None:
            raise ValueError(f"Asset '{name}' not found in manifest")
        if entry.category != "sprites":
            raise ValueError(f"Asset '{name}' is not a sprite (category: {entry.category})")

        asset_path = self._get_asset_path(name)
        if not asset_path.exists():
            raise FileNotFoundError(f"Sprite file not found: {asset_path}")

        if PYGAME_AVAILABLE:
            try:
                surface = pygame.image.load(str(asset_path))
                self._cache[name] = surface
                return surface
            except pygame.error as e:
                raise ValueError(f"Failed to load sprite '{name}': {e}") from e
        else:
            # Return placeholder
            placeholder = {
                "type": "sprite",
                "name": name,
                "path": str(asset_path),
                "metadata": entry.metadata,
            }
            self._cache[name] = placeholder
            return placeholder

    def load_sound(self, name: str) -> Any:
        """Load a sound file.

        Args:
            name: Name of the sound asset.

        Returns:
            pygame.mixer.Sound if pygame is available, otherwise a placeholder dict.

        Raises:
            ValueError: If asset not found or wrong category.
            FileNotFoundError: If asset file doesn't exist.
        """
        # Check cache first
        if name in self._cache:
            return self._cache[name]

        # Validate category
        entry = self._manifest.get(name)
        if entry is None:
            raise ValueError(f"Asset '{name}' not found in manifest")
        if entry.category != "sounds":
            raise ValueError(f"Asset '{name}' is not a sound (category: {entry.category})")

        asset_path = self._get_asset_path(name)
        if not asset_path.exists():
            raise FileNotFoundError(f"Sound file not found: {asset_path}")

        if PYGAME_AVAILABLE:
            try:
                sound = pygame.mixer.Sound(str(asset_path))
                self._cache[name] = sound
                return sound
            except pygame.error as e:
                raise ValueError(f"Failed to load sound '{name}': {e}") from e
        else:
            # Return placeholder
            placeholder = {
                "type": "sound",
                "name": name,
                "path": str(asset_path),
                "metadata": entry.metadata,
            }
            self._cache[name] = placeholder
            return placeholder

    def load_font(self, name: str, size: int) -> Any:
        """Load a font at given size.

        Args:
            name: Name of the font asset.
            size: Font size in points.

        Returns:
            pygame.font.Font if pygame is available, otherwise a placeholder dict.

        Raises:
            ValueError: If asset not found or wrong category, or invalid size.
            FileNotFoundError: If asset file doesn't exist.
        """
        if size <= 0:
            raise ValueError(f"Font size must be positive, got {size}")

        # Check font cache (fonts are cached by name+size)
        cache_key = (name, size)
        if cache_key in self._fonts:
            return self._fonts[cache_key]

        # Validate category
        entry = self._manifest.get(name)
        if entry is None:
            raise ValueError(f"Asset '{name}' not found in manifest")
        if entry.category != "fonts":
            raise ValueError(f"Asset '{name}' is not a font (category: {entry.category})")

        asset_path = self._get_asset_path(name)
        if not asset_path.exists():
            raise FileNotFoundError(f"Font file not found: {asset_path}")

        if PYGAME_AVAILABLE:
            try:
                font = pygame.font.Font(str(asset_path), size)
                self._fonts[cache_key] = font
                return font
            except pygame.error as e:
                raise ValueError(f"Failed to load font '{name}' at size {size}: {e}") from e
        else:
            # Return placeholder
            placeholder = {
                "type": "font",
                "name": name,
                "size": size,
                "path": str(asset_path),
                "metadata": entry.metadata,
            }
            self._fonts[cache_key] = placeholder
            return placeholder

    def load_tilemap(self, name: str) -> dict[str, Any]:
        """Load tilemap data.

        Args:
            name: Name of the tilemap asset.

        Returns:
            Dictionary containing tilemap data.

        Raises:
            ValueError: If asset not found or wrong category.
            FileNotFoundError: If asset file doesn't exist.
        """
        # Check cache first
        if name in self._cache:
            return self._cache[name]

        # Validate category
        entry = self._manifest.get(name)
        if entry is None:
            raise ValueError(f"Asset '{name}' not found in manifest")
        if entry.category != "tilemaps":
            raise ValueError(f"Asset '{name}' is not a tilemap (category: {entry.category})")

        asset_path = self._get_asset_path(name)
        if not asset_path.exists():
            raise FileNotFoundError(f"Tilemap file not found: {asset_path}")

        # Load JSON tilemap data (assuming Tiled JSON format or similar)
        try:
            with open(asset_path, "r", encoding="utf-8") as f:
                tilemap_data = json.load(f)
            self._cache[name] = tilemap_data
            return tilemap_data
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse tilemap '{name}': {e}") from e

    def preload_all(self) -> None:
        """Preload all assets into cache.

        This loads all assets at startup to avoid load times during gameplay.
        Note: Fonts are not preloaded since they require a size parameter.
        """
        for entry in self._manifest.list_all():
            if entry.name in self._cache:
                continue  # Already loaded

            try:
                if entry.category == "sprites":
                    self.load_sprite(entry.name)
                elif entry.category == "sounds":
                    self.load_sound(entry.name)
                elif entry.category == "tilemaps":
                    self.load_tilemap(entry.name)
                # Skip fonts - they need size parameter
            except (ValueError, FileNotFoundError) as e:
                # Log warning but continue loading other assets
                print(f"Warning: Failed to preload {entry.category} '{entry.name}': {e}")

    def get_cached(self, name: str) -> Any | None:
        """Get asset from cache without loading.

        Args:
            name: Asset name.

        Returns:
            Cached asset if available, None otherwise.
        """
        return self._cache.get(name)

    def clear_cache(self) -> None:
        """Clear all cached assets to free memory."""
        self._cache.clear()
        self._fonts.clear()

    def get_manifest(self) -> AssetManifest:
        """Get the asset manifest."""
        return self._manifest

    def __repr__(self) -> str:
        """String representation."""
        cached = len(self._cache)
        fonts = len(self._fonts)
        total = len(self._manifest)
        return f"AssetLoader({cached}/{total} assets cached, {fonts} fonts)"
