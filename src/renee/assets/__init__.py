"""Asset Management System for Renee.

Provides type-safe asset references and manifest-based asset loading.
"""

from renee.assets.manifest import AssetEntry, AssetManifest
from renee.assets.loader import AssetLoader

__all__ = [
    "AssetEntry",
    "AssetManifest",
    "AssetLoader",
]
