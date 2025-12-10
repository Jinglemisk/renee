# Renee Rendering Interface

> See [DESIGN.md](DESIGN.md) for strategic architecture

## Render Command Format

The framework outputs render commands as a list of operations:

```python
render_commands = [
    # Clear screen
    {"type": "clear", "color": "#1a1a2e"},

    # Draw background layers (parallax)
    {"type": "draw_image", "image": "background_1", "x": 0, "y": 0, "parallax": 0.5},

    # Draw tilemap
    {"type": "draw_tilemap", "tilemap": "level_1", "offset_x": 0, "offset_y": 0},

    # Draw entities (sorted by y for depth)
    {"type": "draw_sprite", "id": "goblin_1", "sprite": "goblin_idle_2", "x": 160, "y": 192, "flip_x": false},
    {"type": "draw_sprite", "id": "player", "sprite": "knight_walk_3", "x": 96, "y": 224, "flip_x": false},

    # Draw UI elements
    {"type": "draw_rect", "x": 10, "y": 10, "w": 100, "h": 12, "color": "#333333"},  # Health bar bg
    {"type": "draw_rect", "x": 10, "y": 10, "w": 75, "h": 12, "color": "#ff4444"},   # Health bar fill
    {"type": "draw_text", "text": "HP: 75/100", "x": 12, "y": 11, "size": 10, "color": "#ffffff"},

    {"type": "draw_text", "text": "Turn 3 - Player's Turn", "x": 10, "y": 580, "size": 14, "color": "#ffffff"},

    # Draw effects
    {"type": "draw_particles", "system": "damage_numbers", "particles": [
        {"text": "-15", "x": 165, "y": 180, "color": "#ff0000", "age": 0.3}
    ]},
]
```

## Renderer Implementation Interface

```python
# renderers/base.py

from abc import ABC, abstractmethod

class BaseRenderer(ABC):
    """Base class for renee renderers."""

    @abstractmethod
    def initialize(self, config: dict) -> None:
        """Set up the renderer (create window, load assets, etc.)"""
        pass

    @abstractmethod
    def render(self, commands: list) -> None:
        """Process render commands and display frame."""
        pass

    @abstractmethod
    def get_input(self) -> dict:
        """Get player input for this frame."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Clean up renderer resources."""
        pass


# renderers/pygame_renderer.py

import pygame
from .base import BaseRenderer

class PygameRenderer(BaseRenderer):
    def initialize(self, config):
        pygame.init()
        self.screen = pygame.display.set_mode((config["width"], config["height"]))
        self.sprites = {}  # Loaded sprite cache

    def render(self, commands):
        for cmd in commands:
            if cmd["type"] == "clear":
                self.screen.fill(self._parse_color(cmd["color"]))
            elif cmd["type"] == "draw_sprite":
                sprite = self._get_sprite(cmd["sprite"])
                self.screen.blit(sprite, (cmd["x"], cmd["y"]))
            elif cmd["type"] == "draw_rect":
                pygame.draw.rect(self.screen,
                    self._parse_color(cmd["color"]),
                    (cmd["x"], cmd["y"], cmd["w"], cmd["h"]))
            elif cmd["type"] == "draw_text":
                # ... text rendering
                pass
        pygame.display.flip()

    def get_input(self):
        events = pygame.event.get()
        return {
            "quit": any(e.type == pygame.QUIT for e in events),
            "keys": pygame.key.get_pressed(),
            "mouse": pygame.mouse.get_pos(),
            "clicks": [e for e in events if e.type == pygame.MOUSEBUTTONDOWN]
        }

    def shutdown(self):
        pygame.quit()


# renderers/terminal_renderer.py (ASCII art!)

class TerminalRenderer(BaseRenderer):
    def render(self, commands):
        # Convert to ASCII grid
        grid = [[' ' for _ in range(80)] for _ in range(24)]

        for cmd in commands:
            if cmd["type"] == "draw_sprite":
                char = self._sprite_to_char(cmd["sprite"])
                x, y = cmd["x"] // 10, cmd["y"] // 20  # Scale down
                if 0 <= x < 80 and 0 <= y < 24:
                    grid[y][x] = char

        # Print grid
        print("\033[2J\033[H")  # Clear terminal
        for row in grid:
            print(''.join(row))

    def _sprite_to_char(self, sprite_name):
        mapping = {
            "player": "@",
            "goblin": "g",
            "skeleton": "s",
            "wall": "#",
            "floor": ".",
            "chest": "$",
        }
        for key, char in mapping.items():
            if key in sprite_name.lower():
                return char
        return "?"


# renderers/headless.py (for testing)

class HeadlessRenderer(BaseRenderer):
    """Renderer that does nothing - for testing and AI simulation."""

    def __init__(self):
        self.last_commands = []
        self.input_queue = []

    def render(self, commands):
        self.last_commands = commands  # Store for inspection

    def get_input(self):
        if self.input_queue:
            return self.input_queue.pop(0)
        return {"quit": False, "keys": {}, "mouse": (0, 0), "clicks": []}

    def queue_input(self, input_data):
        """For testing: queue input to be returned by get_input()"""
        self.input_queue.append(input_data)

    def get_last_render(self):
        """For testing: inspect what was rendered"""
        return self.last_commands
```

## Using Renderers

```python
# main.py

from renee import Game
from renee.renderers import PygameRenderer, TerminalRenderer, HeadlessRenderer

# Choose renderer based on environment
import os
if os.environ.get("HEADLESS"):
    renderer = HeadlessRenderer()
elif os.environ.get("TERMINAL"):
    renderer = TerminalRenderer()
else:
    renderer = PygameRenderer()

# Create and run game
game = Game("game.yaml", renderer=renderer)
game.run()
```

```bash
# Run with different renderers
$ renee run                    # Default: Pygame
$ TERMINAL=1 renee run         # ASCII art in terminal
$ HEADLESS=1 renee run         # No display (for testing)
```
