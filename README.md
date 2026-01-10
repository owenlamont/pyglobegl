# pyglobegl

AnyWidget wrapper for globe.gl with integrations with popular Python spatial
packages.

## Goals

- Provide a modern AnyWidget-based globe.gl wrapper for Jupyter, JupyterLab,
  Colab, VS Code, and marimo.
- Ship a prebuilt JupyterLab extension via pip install (no separate lab
  build/extension install).
- Keep the Python API friendly for spatial data workflows.

## Roadmap (Short Term)

- Initialize the project via `uv init --package pyglobegl`.
- Add baseline Python package structure and minimal widget class.
- Add frontend build pipeline using Vite + @anywidget/vite and bundle globe.gl
  assets.
- Package prebuilt labextension assets (install.json, labextension files,
  classifiers).
- Add smoke tests and a minimal demo notebook.

## Development Notes / Scratchpad

- Use the uv CLI for dependency and project changes. Do not edit
  `pyproject.toml` or `uv.lock` directly.
- Bundle globe.gl and required assets for offline-friendly installs while
  staying under PyPI size limits.
- Start with Python linting/tooling (ruff, ty, typos, yamllint, zizmor). Use
  Biome for frontend linting/formatting.
- Frontend uses TypeScript, Vite, and @anywidget/vite. HMR is useful during
  widget iteration but not required for end users.
- Node.js tooling is managed with mise; pnpm is the package manager for
  frontend deps.
- Frontend lives in `frontend/`; build output goes to
  `src/pyglobegl/_static/`.
- Static frontend assets are bundled into the Python package and referenced via
  `_esm` from `src/pyglobegl/_static/index.js`.

## Open Questions

- Default asset set (earth textures) and size budget for bundled assets.
- Whether to include optional CDN fallback for large assets.

## Build Assets (Release Checklist)

1) `cd frontend && pnpm run build`
2) `uv build`

## Quickstart

```python
from pyglobegl import GlobeWidget

GlobeWidget()
```
