# pyglobegl

[AnyWidget](https://github.com/manzt/anywidget) wrapper for
[globe.gl](https://github.com/vasturiano/globe.gl) with integrations with
popular Python spatial packages.

## Goals

- Provide a modern AnyWidget-based globe.gl wrapper for Jupyter, JupyterLab,
  Colab, VS Code, and marimo.
- Ship a prebuilt JupyterLab extension via pip install (no separate lab
  build/extension install).
- Keep the Python API friendly for spatial data workflows.

## Roadmap

- **Near term**
  - Expose the base globe.gl API surface in the same order as the official API
    reference (initialisation, layout, globe layer, then the data layers).
  - Publish low-level layer bindings for: points, arcs, polygons, paths,
    heatmaps, hex bins, hexed polygons, tiles, particles, rings, labels, HTML
    elements, 3D objects, custom layer, render control, and utility options.
  - Prioritize strongly typed, overload-heavy Python APIs with flexible input
    unions (e.g., accept Pillow images, NumPy arrays, or remote URLs anywhere
    globe.gl accepts textures/images).
  - Solidify a CRS-first API: detect CRS on inputs and auto-reproject to
    EPSG:4326 before emitting lat/lng data for globe.gl layers.

- **Mid term**
  - GeoPandas adapter: map geometry types to globe.gl layers with sensible
    defaults and schema validation.
  - MovingPandas trajectories (static): accept trajectory/segment outputs and
    render via paths/arcs without time animation in v1.
  - Geometry-only inputs: accept bare geometry collections (Shapely or
    GeoJSON-like) as a convenience layer when CRS metadata is explicit.

- **Long term / research**
  - GeoPolars exploration: track maturity and define an adapter plan once CRS
    metadata and extension types are stable upstream.
  - Raster feasibility: investigate mapping rasters to globe.gl via tiles,
    heatmaps, or sampled grids; document constraints and recommended workflows.

## Development Notes / Scratchpad

- Use the uv CLI for dependency and project changes. Do not edit
  `pyproject.toml` or `uv.lock` directly.
- Solara demo: `uv run solara run examples/solara_demo.py`.
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
- Solara UI checks use `pytest-ipywidgets` in `tests/test_ui_solara.py`.

## WSL2 Test Notes

- WSL2 UI tests require WSLg with a working display socket (Wayland or X11) and
  WebGL available in the Playwright Chromium build.
- If the UI tests are meant to enforce hardware acceleration, set
  `PYGLOBEGL_REQUIRE_HW_ACCEL=1` before running pytest so software renderers
  skip early.
- On WSL2, the UI test harness retries the browser launch with the D3D12-backed
  Mesa driver if the initial WebGL probe reports a software renderer. You can
  still set `GALLIUM_DRIVER=d3d12` and `MESA_LOADER_DRIVER_OVERRIDE=d3d12`
  manually, and optionally set `PYGLOBEGL_WSL_GPU_ADAPTER=<GPU name>` to map to
  `MESA_D3D12_DEFAULT_ADAPTER_NAME` when multiple adapters are present.

## Build Assets (Release Checklist)

1) `cd frontend && pnpm run build`
2) `uv build`

## Quickstart

```python
from pyglobegl import GlobeWidget

GlobeWidget()
```
