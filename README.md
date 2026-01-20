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
  - Expose globe.gl APIs in order (by section):
    - [x] Initialisation
    - [x] Container layout
    - [x] Globe layer
    - [ ] Points layer
    - [ ] Arcs layer
    - [ ] Polygons layer
    - [ ] Paths layer
    - [ ] Heatmaps layer
    - [ ] Hex bin layer
    - [ ] Hexed polygons layer
    - [ ] Tiles layer
    - [ ] Particles layer
    - [ ] Rings layer
    - [ ] Labels layer
    - [ ] HTML elements layer
    - [ ] 3D objects layer
    - [ ] Custom layer
    - [ ] Render control
    - [ ] Utility options
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

## WSL2 Test Notes

- WSL2 UI tests require WSLg with a working display socket (Wayland or X11) and
  WebGL available in the Playwright Chromium build.
- If the UI tests are meant to enforce hardware acceleration, set
  `PYGLOBEGL_REQUIRE_HW_ACCEL=1` before running pytest so software renderers
  skip early.
- Canvas reference comparisons allow a small pixel-diff tolerance. Override
  with `PYGLOBEGL_MAX_DIFF_RATIO` (e.g. `0.02` for a 2% threshold) to tighten or
  loosen comparisons across platforms.
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
from pyglobegl import GlobeWidget, image_to_data_url
from PIL import Image

GlobeWidget()
```

## Image Inputs

Globe image fields expect URLs, but you can pass a PIL image by converting it
to a PNG data URL:

```python
from pyglobegl import GlobeLayerConfig, image_to_data_url
from PIL import Image

image = Image.open("earth.png")
config = GlobeLayerConfig(globe_image_url=image_to_data_url(image))
```

## Points Layer

```python
from pyglobegl import (
    GlobeConfig,
    GlobeLayerConfig,
    GlobeWidget,
    PointDatum,
    PointsLayerConfig,
)

points = [
    PointDatum(lat=0, lng=0, size=0.25, color="#ff0000", label="Center"),
    PointDatum(lat=15, lng=-45, size=0.12, color="#00ff00", label="West"),
]

config = GlobeConfig(
    globe=GlobeLayerConfig(
        globe_image_url="https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-day.jpg"
    ),
    points=PointsLayerConfig(
        points_data=points,
        point_altitude="size",
        point_color="color",
        point_label="label",
    ),
)

GlobeWidget(config=config)
```

## GeoPandas Helper (Optional)

Install the optional GeoPandas extra:

```bash
uv add pyglobegl[geopandas]
```

Convert a GeoDataFrame of point geometries into points data. The helper
reprojects to EPSG:4326 before extracting lat/lng.

```python
import geopandas as gpd

from pyglobegl import points_from_gdf

gdf = gpd.read_file("points.geojson")
points = points_from_gdf(gdf, include_columns=["name", "population"])
```
