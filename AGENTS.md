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
  `uv run pytest --color=no`.
  If running in a sandboxed Codex session, request elevated permissions so the
  commands can reach the full workspace and any required local services.
- Always run `prek` with elevated permissions so it can fetch hook repos and
  access the full workspace.

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

## Automated Tests

- Use pytest for tests.
- Add smoke tests for the widget once the frontend is wired.

## Manual UI Testing (Notebook)

- Build frontend assets before testing: `cd frontend && pnpm run build`.
- JupyterLab: `uv run jupyter lab` and open `examples/jupyter_demo.ipynb`.
- Notebook: `uv run jupyter notebook` and open `examples/jupyter_demo.ipynb`.
- marimo: `uv run marimo edit examples/marimo_demo.py`.

## Playwright-Assisted Validation (WSL2 + Windows GPU)

The widget uses WebGL; WSL browsers often fail to create a WebGL context. To
automate rendering checks, run Playwright on Windows and point it at the WSL
servers bound to `0.0.0.0`.

- Configure Playwright MCP to use Windows PowerShell (config in
  `~/.codex/config.toml`):
  - `command = "pwsh.exe"`
  - `args = ["-NoLogo", "-NoProfile", "-Command", "npx @playwright/mcp@latest"]`
- Start marimo on all interfaces so Windows can reach it:
  - `uv run marimo run --host 0.0.0.0 --port 2726 examples/marimo_demo.py`
- Find the WSL IP for Windows access:
  - `hostname -I` (use the first IP)
- In Playwright, open: `http://<WSL_IP>:2726`
  - Wait a few seconds for the widget to render.
  - Verify a `<canvas>` exists via Playwright evaluation.
  - A black sphere with blue haze is expected unless a globe texture is set.
- For JupyterLab automation, start:
  - Run:
    ```bash
    uv run jupyter lab --ip 0.0.0.0 --ServerApp.port=8888 \
      --ServerApp.token=devtoken
    ```
  - Open `http://<WSL_IP>:8888/lab?token=devtoken` in Playwright and run the
    first cell in `examples/jupyter_demo.ipynb`.

### Playwright Screenshot Path Notes

The MCP server only writes inside its own temp output directory. To keep copies
in a stable Windows path, copy after capture:

- Screenshot is created under:
  - `C:\Users\<USER>\AppData\Local\Temp\playwright-mcp-output\<run>\`
  - `artifacts\...`
- Copy to a stable folder visible from WSL:
  - Run:
    ```bash
    mkdir -p /mnt/c/Users/<USER>/AppData/Local/Temp/pyglobegl
    src="/mnt/c/Users/<USER>/AppData/Local/Temp/playwright-mcp-output/<run>/"
    src="${src}artifacts/<file>.png"
    dst="/mnt/c/Users/<USER>/AppData/Local/Temp/pyglobegl/<file>.png"
    cp "$src" "$dst"
    ```
