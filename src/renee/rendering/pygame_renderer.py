"""Pygame renderer backend.

Import is lazy so the core framework can be used without pygame installed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from renee.assets import AssetRegistry
from renee.errors import ValidationError
from renee.input import InputState
from renee.rendering.commands import RenderCommand, normalize_command
from renee.rendering.renderer import Renderer


class PygameRenderer(Renderer):
    def __init__(self, *, assets: AssetRegistry | None = None, asset_root: str | Path | None = None) -> None:
        self._assets = assets
        self._asset_root = Path(asset_root) if asset_root is not None else (assets.root if assets else None)
        self._pygame: Any | None = None
        self._screen: Any | None = None
        self._clock: Any | None = None
        self._fonts: dict[int, Any] = {}
        self._images: dict[str, Any] = {}
        self._input = InputState()
        self._scale: int = 1

    def initialize(self, config: Mapping[str, Any] | None = None) -> None:
        try:
            import pygame  # type: ignore[import-not-found]
        except ModuleNotFoundError as e:
            raise ValidationError(
                "pygame_missing",
                "pygame is required for the PygameRenderer backend.",
                hint="Install with: pip install pygame",
            ) from e

        self._pygame = pygame
        pygame.init()

        cfg = dict(config or {})
        self._scale = int(cfg.get("scale", 1))
        width = int(cfg.get("width", 800))
        height = int(cfg.get("height", 600))
        title = str(cfg.get("title", "Renee"))
        self._screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self._clock = pygame.time.Clock()

    def render(self, commands: Sequence[RenderCommand]) -> None:
        pygame = self._require_pygame()
        screen = self._require_screen()

        # Basic input polling for quit; key state is refreshed in get_input().
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self._input.quit_requested = True

        for raw in commands:
            cmd = normalize_command(raw)
            t = cmd["type"]
            if t == "clear":
                color = cmd.get("color", [0, 0, 0])
                screen.fill(tuple(color))
            elif t == "draw_rect":
                rect = pygame.Rect(
                    int(cmd["x"]) * self._scale,
                    int(cmd["y"]) * self._scale,
                    int(cmd["w"]) * self._scale,
                    int(cmd["h"]) * self._scale,
                )
                color = tuple(cmd.get("color", [255, 255, 255]))
                filled = bool(cmd.get("filled", True))
                pygame.draw.rect(screen, color, rect, 0 if filled else 1)
            elif t == "draw_text":
                text = str(cmd.get("text", ""))
                x = int(cmd.get("x", 0)) * self._scale
                y = int(cmd.get("y", 0)) * self._scale
                size = int(cmd.get("size", 16))
                color = tuple(cmd.get("color", [255, 255, 255]))
                font = self._font(size)
                surf = font.render(text, True, color)
                screen.blit(surf, (x, y))
            elif t == "draw_sprite":
                sprite = str(cmd.get("sprite", ""))
                x = int(cmd.get("x", 0)) * self._scale
                y = int(cmd.get("y", 0)) * self._scale
                flip_x = bool(cmd.get("flip_x", False))
                flip_y = bool(cmd.get("flip_y", False))
                img = self._image(sprite)
                if flip_x or flip_y:
                    img = pygame.transform.flip(img, flip_x, flip_y)
                screen.blit(img, (x, y))
            elif t == "draw_image":
                image = str(cmd.get("image", ""))
                x = int(cmd.get("x", 0)) * self._scale
                y = int(cmd.get("y", 0)) * self._scale
                img = self._image(image)
                screen.blit(img, (x, y))

        pygame.display.flip()
        if self._clock is not None:
            self._clock.tick(60)

    def get_input(self) -> InputState:
        pygame = self._require_pygame()

        pressed = pygame.key.get_pressed()
        keys_down: set[str] = set()
        for key_code, is_down in enumerate(pressed):
            if is_down:
                keys_down.add(pygame.key.name(key_code))

        # Capture keys pressed this frame using event queue.
        keys_pressed: set[str] = set()
        mouse_buttons_down: set[int] = set()
        for ev in pygame.event.get():
            if ev.type == pygame.KEYDOWN:
                keys_pressed.add(pygame.key.name(ev.key))
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                mouse_buttons_down.add(int(ev.button))
            elif ev.type == pygame.QUIT:
                self._input.quit_requested = True

        mouse_pos = pygame.mouse.get_pos()

        self._input.keys_down = keys_down
        self._input.keys_pressed = keys_pressed
        self._input.mouse_buttons_down = mouse_buttons_down
        self._input.mouse_pos = (int(mouse_pos[0]), int(mouse_pos[1]))
        return self._input

    def shutdown(self) -> None:
        if self._pygame is not None:
            self._pygame.quit()

    def _require_pygame(self) -> Any:
        if self._pygame is None:
            raise RuntimeError("PygameRenderer not initialized")
        return self._pygame

    def _require_screen(self) -> Any:
        if self._screen is None:
            raise RuntimeError("PygameRenderer not initialized")
        return self._screen

    def _font(self, size: int) -> Any:
        pygame = self._require_pygame()
        if size not in self._fonts:
            self._fonts[size] = pygame.font.Font(None, size)
        return self._fonts[size]

    def _image(self, ref: str) -> Any:
        pygame = self._require_pygame()
        if ref in self._images:
            return self._images[ref]

        path = self._resolve_asset_path(ref)
        surf = pygame.image.load(str(path)).convert_alpha()
        self._images[ref] = surf
        return surf

    def _resolve_asset_path(self, ref: str) -> Path:
        # If an AssetRegistry is provided and the ref matches a sprite name, use it.
        if self._assets is not None and ref in self._assets.manifest.get("sprites", {}):
            return self._assets.path_for("sprites", ref)

        if self._asset_root is None:
            raise ValidationError(
                "asset_root_missing",
                f"Cannot resolve image '{ref}' without an asset root.",
                hint="Provide AssetRegistry or asset_root when constructing PygameRenderer.",
                context={"ref": ref},
            )
        candidate = Path(ref)
        if candidate.is_absolute():
            return candidate
        return self._asset_root / candidate
