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
- `docs/` + `zensical.toml` – Zensical documentation site sources (published to
  Cloudflare Pages). Keep pages in sync when behaviour or features change.

## Documentation Site

- The docs site is built with Zensical (Material-for-MkDocs style) from `docs/`
  and `zensical.toml`, and is published to Cloudflare Pages from `main`.
- Build/preview locally with the `docs` dependency group:
  `uv run --group docs zensical build --clean` (output in `site/`, gitignored)
  or `uv run --group docs zensical serve`.
- `docs/**` is excluded from rumdl (Material/Zensical Markdown extensions trip
  it); there is no docs CI/prek build step (Cloudflare builds on merge).

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

## Decision Log

- Prefer strong Pydantic models over dynamic globe.gl accessors. Layer data
  must be `PointDatum`/`ArcDatum`/`PolygonDatum` (no raw dicts for public APIs).
- Do not expose accessor remapping or string field-name accessors in Python.
  We keep the mapping internal to bridge Pythonic names to globe.gl keys.
  - Where it lives: `GlobeWidget.__init__` (`src/pyglobegl/widget.py`) injects
    the per-datum accessor bindings into the synced `config` (e.g.
    `_rings_props.update({"ringColor": "color", "ringMaxRadius": "maxRadius",
    ...})`). The Pydantic `*LayerConfig` models intentionally do **not** carry
    these accessor fields, and the frontend never sets them as field-name
    strings or arrow functions — so a raw `GlobeConfig.model_dump()` omits them;
    inspect `GlobeWidget(...).config` to see the real payload. three-globe's
    own accessor defaults are mostly constants (`ringColor: () => '#ffffaa'`,
    `ringMaxRadius: 2`, …), so without this injection per-datum styling would be
    silently ignored. The initial-config path (`applyRingsProps`) and the
    runtime-message path (`rings_set_data` → `globe.ringsData(...)`) are
    equivalent — both rely on the same injected bindings.
- Type hints must mirror the Python API, not JS accessors; avoid `str`
  field-name accessor types in public models.
- Defaults in data models mirror globe.gl so omitted values still render
  predictably.
- Avoid `None`/`Optional` unless `null` has a specific, documented meaning in
  globe.gl/three-globe; otherwise set the globe.gl default value directly.
- Extra fields are allowed on models for metadata, but canonical fields are
  fixed (no aliasing to alternate names).

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
- Never `git commit`, `git push`, or open/create pull requests unless the user
  explicitly asks or gives consent for those actions.
- Keep local reference clones in `/tmp` for:
  - `https://github.com/vasturiano/globe.gl`
  - `https://github.com/vasturiano/three-globe`
  - `https://github.com/movingpandas/movingpandas`
  - `https://github.com/geopandas/geopandas`
  - `https://github.com/manzt/anywidget`
  to cross-check behavior/docs.

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

The widget uses WebGL. Under WSLg with Google Chrome installed, the pytest UI
tests render with GPU-accelerated WebGL directly in WSL (see the UI Tests
section below), so this Windows route is now an alternative — useful when WSL
GPU rendering is unavailable, or for interactive/manual visual checks. To use
it, run Playwright on Windows and open the marimo server on `localhost` (don’t
force `--host 0.0.0.0`, which can break localhost forwarding).

- Start marimo (edit mode) in WSL:
  - `uv run marimo edit examples/marimo_demo.py --headless --port 2729`
    `--skip-update-check`
  - Use the printed access token URL in Windows (example):
    - `http://localhost:2729?access_token=<TOKEN>`
- In marimo, run all cells (command palette → “Re-run all cells” or click the
  run-all button) and toggle app view (Ctrl + .).
  - Driving via Playwright MCP: press `Control+k` to open the command palette,
    then `Enter` — “Re-run all cells” is the first entry. Wait a few seconds for
    the WebGL context + globe texture to load before sampling.
  - Re-run the widget cell after each frontend rebuild to pick up the latest
    JS bundle (the JS hash changes when the bundle changes).
  - The textured Earth should render once app view is enabled.
- Reading canvas pixels (not just eyeballing screenshots): the anywidget canvas
  is inside a **shadow root**, so `document.querySelector('canvas')` returns
  nothing — recurse through `el.shadowRoot` to find it. For JS pixel readback
  (`drawImage` → `getImageData`) set `GlobeInitConfig(renderer_config=`
  `{"preserveDrawingBuffer": True})`; otherwise the buffer reads back blank
  (Playwright `page.screenshot` works without it because the compositor
  captures the frame).
- Verifying **animated** layers (rings, arc dashes, ripples): a single still
  frame is unreliable. A ripple's visible lifetime is
  `transitionTime = |maxRadius / propagationSpeed| * 1000 ms`, repeated every
  `repeat_period` ms, so fast/short/transparent rings have a low duty cycle and
  are frequently absent from any one capture. Sample the canvas over several
  seconds (e.g. count target-colour pixels every ~120 ms) and assert the layer
  appears in some fraction of frames, rather than expecting every frame to show
  it. See closed issue #60 for a worked example (montage rings were a false
  “not rendering” report).
- For JupyterLab automation, start:
  - Run:

    ```bash
    uv run jupyter lab --no-browser --port 8890 --ip 127.0.0.1
    ```

  - Copy the tokenized URL from the logs, then open:
    - `http://127.0.0.1:8890/lab/tree/examples/jupyter_demo.ipynb?token=<TOKEN>`
  - Run the first cell and confirm the globe renders.

## UI Tests

- The Playwright reference-image tests (those using the `page`/`page_session`
  fixtures, e.g. `tests/test_heatmaps_layer.py`) and the marimo/Jupyter UI tests
  (`tests/test_ui_marimo.py`, `tests/test_ui_jupyter.py`) are not gated behind a
  marker — they run as part of the default `uv run pytest` suite whenever a
  Playwright browser is available (otherwise they error at browser launch).
- They need a Playwright browser. On this WSL setup (Ubuntu 26.04) the bundled
  Chromium is unavailable (`playwright install chromium` reports the OS is
  unsupported), so install Google Chrome and run against that channel instead:
  - `uv run playwright install --with-deps chrome` — needs sudo for the system
    libraries (run it in a real terminal for the password prompt). The trailing
    `ffmpeg` failure is harmless: ffmpeg is only used for video recording, not
    canvas screenshots.
  - `uv run pytest --browser-channel chrome` — the conftest defaults to the
    `chromium` channel on WSL, so pass `chrome` explicitly to use the install
    above.
- Under WSLg (`/mnt/wslg` present, with `DISPLAY`/`WAYLAND_DISPLAY` set) these
  tests render with GPU-accelerated WebGL; they no longer crash or skip on WSL.
  They also run on Windows and full Linux. Software WebGL is accepted by default
  (set `PYGLOBEGL_REQUIRE_HW_ACCEL=1` to require a hardware renderer).
- Reference baselines auto-generate: on a missing baseline the capture is saved
  to `tests/reference-images/<test>-<label>.png` and the test fails with a
  "verify and re-run" message. Inspect the saved PNG, then re-run to confirm it
  passes the comparison threshold. Cross-OS CI runners rely on the SSIM
  tolerance to absorb renderer differences, so a baseline captured locally is
  expected to be close enough across runners.

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

Do **not** pass a `filename` (or relative path) to `browser_take_screenshot` /
`browser_evaluate`: the MCP server resolves it against a bogus path (the WSL cwd
remapped under `C:\`) and errors. Omit `filename` so output lands in the default
Windows temp dir (`%LOCALAPPDATA%\Temp\.playwright-mcp\`), and return
`browser_evaluate` results inline instead of writing them to a file.
