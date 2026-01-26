# Coding Agent Instructions

Guidance on how to navigate and modify this codebase.

## What This Library Does

pyglobegl is an installable Python package that wraps globe.gl as an AnyWidget,
targeting modern notebook environments (Jupyter, JupyterLab, Colab, VS Code,
marimo). It ships a prebuilt JupyterLab extension so users can `pip install`
and immediately use the widget without rebuilding JupyterLab.

## Code Change Requirements

- Use the uv CLI for all dependency and project changes. Do not edit
  `pyproject.toml` or `uv.lock` directly.
- Update documentation whenever behaviour or features change.
- Diagnose bugs before patching; prefer minimal repros and root-cause fixes.
- When code changes land, run `prek run --all-files` and
  `uv run pytest --color=no -n 4` (local runs are more stable with 4 workers).

## Project Structure (planned)

- `src/pyglobegl/` – Library code.
- `frontend/` – Vite-based frontend sources (JS/TS) for the widget.
- `tests/` – Pytest suite (mirrors src structure).
- `.github/` – CI workflows.
- `README.md` – User guide and development scratchpad/roadmap.

## Code Style

- Follow the Google Python Style Guide with Google-style docstrings.
- Use precise type hints and avoid `Any` unless unavoidable.
- Keep comments minimal; prefer clear names and docstrings.
- Keep imports at module top unless avoiding circular imports.
- For GeoJSON polygons, ensure exterior rings are counter-clockwise (right-hand
  rule) so three.js cap triangulation renders correctly; holes should be
  clockwise.
- Stage new files before running prek so they are included in checks. If prek
  applies fixes, rerun it to confirm a clean pass.

## Frontend Notes

- Frontend assets are bundled with Vite and shipped in the wheel.
- Keep the bundle offline-friendly; avoid CDN-only dependencies by default.
- Use TypeScript for frontend code and Biome for linting/formatting.
  Frontend dependencies are managed with pnpm via mise.
- Frontend build output is committed under `src/pyglobegl/_static/`.

## Development Environment / Terminal

- Use `uv add` for dependencies and `uv run` for tools.
- When running ad-hoc Python, prefer `uv run python`.
- If a task fails due to network, file access, dependency install, or local
  system restrictions, request elevated permissions first rather than pivoting
  to work-arounds. Escalation is preferred over brittle fallback solutions.

## Automated Tests

- Use pytest for tests.
- Add smoke tests for the widget once the frontend is wired.

## Manual UI Testing (Notebook)

- Build frontend assets before testing: `cd frontend && pnpm run build`.
- JupyterLab: `uv run jupyter lab` and open `examples/jupyter_demo.ipynb`.
- Notebook: `uv run jupyter notebook` and open `examples/jupyter_demo.ipynb`.
- marimo (edit + app view):
  - `uv run marimo edit examples/marimo_demo.py --headless --port 2729`
    `--skip-update-check`.
  - After rebuilding the frontend, re-run the widget cell so marimo refreshes
    the anywidget JS bundle (stale outputs keep the old hash).

## Playwright-Assisted Validation (WSL2 + Windows GPU)

The widget uses WebGL; WSL browsers often fail to create a WebGL context. To
automate rendering checks, run Playwright on Windows and open the marimo server
on `localhost` (don’t force `--host 0.0.0.0`, which can break localhost
forwarding).

- Configure Playwright MCP to use Windows PowerShell (config in
  `~/.codex/config.toml`):
  - `command = "pwsh.exe"`
  - `args = ["-NoLogo", "-NoProfile", "-Command", "npx @playwright/mcp@latest"]`
- Start marimo (edit mode) in WSL:
  - `uv run marimo edit examples/marimo_demo.py --headless --port 2729`
    `--skip-update-check`
  - Use the printed access token URL in Windows (example):
    - `http://localhost:2729?access_token=<TOKEN>`
- In marimo, run all cells (command palette → “Re-run all cells” or click the
  run-all button) and toggle app view (Ctrl + .).
  - Re-run the widget cell after each frontend rebuild to pick up the latest
    JS bundle (the JS hash changes when the bundle changes).
  - The textured Earth should render once app view is enabled.
- For JupyterLab automation, start:
  - Run:

    ```bash
    uv run jupyter lab --no-browser --port 8890 --ip 127.0.0.1
    ```

  - Copy the tokenized URL from the logs, then open:
    - `http://127.0.0.1:8890/lab/tree/examples/jupyter_demo.ipynb?token=<TOKEN>`
  - Run the first cell and confirm the globe renders.

## UI Tests (Opt-in)

- UI tests are marked `ui` and excluded by default.
- Run marimo UI checks:
- `uv run pytest -m ui`
  - Skips on WSL because Chromium crashes.
  - Run on Windows or full Linux to execute the UI test.
  - If Playwright browsers are missing: `uv run playwright install`.

### Jupyter UI Test Notes

- The Jupyter UI test is in `tests/test_ui_jupyter.py`.
- It starts JupyterLab in-process, opens `examples/jupyter_demo.ipynb`, selects
  the Python kernel, and executes the first cell via the Jupyter command API.
- The test waits for a canvas inside the output area and fails with artifacts
  (HTML + screenshot) when the widget does not render.
- If it flakes, re-download UI artifacts from the failed CI job and inspect
  the screenshot/log tail to see whether the cell executed and produced output.

### Playwright Screenshot Path Notes

If we need to inspect Playwright screenshots, ask the user to grant read access
to the top-level Windows Temp directory so the MCP output can be read directly.
