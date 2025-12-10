# Deploying Renee Games

See [DESIGN.md](DESIGN.md) for strategic architecture.

How to package and distribute games built with Renee.

## Development Setup

```bash
# Create project with virtual environment
mkdir my_game && cd my_game
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install renee pygame pyyaml

# Or with requirements.txt
pip install -r requirements.txt
```

## requirements.txt

```
# Core framework
pydantic>=2.0
pyyaml>=6.0
typer>=0.9
rich>=13.0

# Rendering
pygame>=2.5

# Development
pytest>=7.0
watchdog>=3.0  # For hot-reload
```

## pyproject.toml

```toml
[project]
name = "my-game"
version = "0.1.0"
description = "A turn-based game built with Renee"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.0",
    "pyyaml>=6.0",
    "typer>=0.9",
    "rich>=13.0",
    "pygame>=2.5",
]

[project.scripts]
my-game = "my_game.main:main"

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "watchdog>=3.0",
    "pyinstaller>=6.0",
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
```

## Creating Executables

### PyInstaller (Recommended)

```bash
# Install
pip install pyinstaller

# Basic executable
pyinstaller --onefile main.py

# With game assets and data
pyinstaller --onefile --windowed \
    --add-data "entities:entities" \
    --add-data "scenes:scenes" \
    --add-data "rules:rules" \
    --add-data "assets:assets" \
    --name "MyGame" \
    main.py

# Result: dist/MyGame.exe (or MyGame on Mac/Linux)
```

### Nuitka (Faster, Smaller)

```bash
# Install
pip install nuitka

# Compile to standalone executable
nuitka --standalone --onefile \
    --include-data-dir=entities=entities \
    --include-data-dir=scenes=scenes \
    --include-data-dir=assets=assets \
    --output-filename=MyGame \
    main.py
```

### Comparison

| Tool | Output Size | Startup Time | Compile Time |
|------|-------------|--------------|--------------|
| PyInstaller | ~40-60MB | Slower | Fast |
| Nuitka | ~25-40MB | Faster | Slower |

## Distribution Checklist

```
my_game_release/
├── MyGame.exe           # Standalone executable
├── README.txt           # How to play
├── LICENSE.txt          # Your license
└── saves/               # Empty saves directory
```

Users double-click the executable — no Python installation required.

## Platform-Specific Notes

### Windows
- Use `--windowed` flag to hide console
- Sign executable for Windows SmartScreen

### macOS
- Creates `.app` bundle with PyInstaller
- May need to codesign for Gatekeeper

### Linux
- AppImage format recommended for distribution
- Use `--strip` flag for smaller binary
