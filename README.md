# pyglobegl

[anywidget](https://github.com/manzt/anywidget) wrapper for
[globe.gl](https://github.com/vasturiano/globe.gl) with integrations with
popular Python spatial packages.

## Installation

```bash
pip install pyglobegl
```

Or with uv:

```bash
uv add pyglobegl
```

Optional GeoPandas + Pandera extra:

```bash
pip install pyglobegl[geopandas]
```

```bash
uv add pyglobegl[geopandas]
```

## Quickstart

```python
from IPython.display import display

from pyglobegl import GlobeWidget

display(GlobeWidget())
```

## Image Inputs

Globe image fields expect URLs, but you can pass a PIL image by converting it
to a PNG data URL:

```python
from PIL import Image

from pyglobegl import GlobeLayerConfig, image_to_data_url

image = Image.open("earth.png")
config = GlobeLayerConfig(globe_image_url=image_to_data_url(image))
```

## Points Layer

```python
from IPython.display import display

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

display(GlobeWidget(config=config))
```

## Arcs Layer

```python
from IPython.display import display

from pyglobegl import (
    ArcDatum,
    ArcsLayerConfig,
    GlobeConfig,
    GlobeLayerConfig,
    GlobeWidget,
)

arcs = [
    ArcDatum(
        start_lat=0,
        start_lng=-30,
        end_lat=10,
        end_lng=40,
        altitude=0.2,
    ),
    ArcDatum(
        start_lat=20,
        start_lng=10,
        end_lat=-10,
        end_lng=-50,
        altitude=0.1,
    ),
]

config = GlobeConfig(
    globe=GlobeLayerConfig(
        globe_image_url="https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-day.jpg"
    ),
    arcs=ArcsLayerConfig(
        arcs_data=arcs,
        arc_altitude="altitude",
        arc_color="#ffcc00",
        arc_stroke=1.2,
    ),
)

display(GlobeWidget(config=config))
```

## GeoPandas Helpers (Optional)

Convert GeoDataFrames into layer data using Pandera DataFrameModel validation.
Point geometries are reprojected to EPSG:4326 before extracting lat/lng.

```python
import geopandas as gpd
from shapely.geometry import Point

from pyglobegl import points_from_gdf

gdf = gpd.GeoDataFrame(
    {
        "name": ["A", "B"],
        "population": [1000, 2000],
        "point": [Point(0, 0), Point(5, 5)],
    },
    geometry="point",
    crs="EPSG:4326",
)
points = points_from_gdf(gdf, include_columns=["name", "population"])
```

```python
import geopandas as gpd
from shapely.geometry import Point

from pyglobegl import arcs_from_gdf

gdf = gpd.GeoDataFrame(
    {
        "name": ["Route A", "Route B"],
        "value": [1, 2],
        "start": [Point(0, 0), Point(10, 5)],
        "end": [Point(20, 10), Point(-5, -5)],
    },
    geometry="start",
    crs="EPSG:4326",
)
arcs = arcs_from_gdf(gdf, include_columns=["name", "value"])
```

`points_from_gdf` defaults to a point geometry column named `point` if present,
otherwise it uses the active GeoDataFrame geometry column (override with
`point_geometry=`). `arcs_from_gdf` expects point geometry columns named
`start` and `end` (override with `start_geometry=` and `end_geometry=`).

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
    - [x] Points layer
    - [x] Arcs layer
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

## Contributing

### Build Assets (Release Checklist)

1) `cd frontend && pnpm run build`
2) `uv build`

### WSL2 Test Notes

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

### Windows Test Notes

- The Playwright Chromium launch adds ANGLE GPU flags on Windows to prefer
  hardware acceleration (D3D11 via ANGLE). If the GPU path is unavailable,
  Chromium can still fall back to software rendering.

### UI Test Artifacts

- Canvas captures are saved under `ui-artifacts` as
  `{test-name}-pass-<timestamp>.png` or `{test-name}-fail-<timestamp>.png`.
- Canvas comparisons use SSIM (structural similarity) with a fixed threshold
  (currently `0.86`).
