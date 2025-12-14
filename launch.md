# Launch / Verification Checklist

Run these commands from the repo root.

1. Create a virtual environment
   ```bash
   python3 -m venv .venv
   ```

2. Activate it (macOS/Linux)
   ```bash
   source .venv/bin/activate
   ```

3. Install Renee (editable) + test tooling
   ```bash
   pip install -e ".[dev]"
   ```

4. Run the test suite (includes multiplayer integration test)
   ```bash
   pytest -q
   ```

5. Verify the CLI entrypoint works
   ```bash
   renee --version
   ```

6. Run the demo in headless mode (non-interactive smoke test)
   ```bash
   renee demo local --renderer headless
   ```

7. Run the demo locally in the terminal (interactive)
   ```bash
   renee demo local --renderer terminal
   ```

8. Install pygame support (for the pygame renderer)
   ```bash
   pip install -e ".[pygame]"
   ```

9. Run the demo locally with pygame (interactive)
   ```bash
   renee demo local --renderer pygame
   ```

10. Multiplayer demo (requires 3 terminals)
    - Terminal A (server):
      ```bash
      renee demo server
      ```
    - Terminal B (client 1):
      ```bash
      renee demo client
      ```
    - Terminal C (client 2):
      ```bash
      renee demo client
      ```
    - In each client terminal, enter moves (`w`/`a`/`s`/`d`) and take turns; quit clients with `q`, stop server with `Ctrl+C`.

