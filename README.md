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
    PointDatum(lat=0, lng=0, altitude=0.25, color="#ff0000", label="Center"),
    PointDatum(lat=15, lng=-45, altitude=0.12, color="#00ff00", label="West"),
]

config = GlobeConfig(
    globe=GlobeLayerConfig(
        globe_image_url="https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-day.jpg"
    ),
    points=PointsLayerConfig(points_data=points),
)

display(GlobeWidget(config=config))
```

pyglobegl expects layer data as Pydantic models (`PointDatum`, `ArcDatum`,
`PolygonDatum`). Dynamic accessor remapping is not supported; per-datum values
are read from the model field names. Numeric fields reject string values, and
data model defaults mirror globe.gl defaults so omitted values still render
predictably.

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
        color="#ffcc00",
        stroke=1.2,
    ),
    ArcDatum(
        start_lat=20,
        start_lng=10,
        end_lat=-10,
        end_lng=-50,
        altitude=0.1,
        color="#ffcc00",
        stroke=1.2,
    ),
]

config = GlobeConfig(
    globe=GlobeLayerConfig(
        globe_image_url="https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-day.jpg"
    ),
    arcs=ArcsLayerConfig(arcs_data=arcs),
)

display(GlobeWidget(config=config))
```

## Polygons Layer

```python
from IPython.display import display
from geojson_pydantic import Polygon

from pyglobegl import (
    GlobeConfig,
    GlobeLayerConfig,
    GlobeWidget,
    PolygonDatum,
    PolygonsLayerConfig,
)

polygon = Polygon(
    type="Polygon",
    coordinates=[
        [
            (-10, 0),
            (-10, 10),
            (10, 10),
            (10, 0),
            (-10, 0),
        ]
    ],
)

config = GlobeConfig(
    globe=GlobeLayerConfig(
        globe_image_url="https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-day.jpg"
    ),
    polygons=PolygonsLayerConfig(
        polygons_data=[
            PolygonDatum(geometry=polygon, cap_color="#ffcc00", altitude=0.05)
        ],
    ),
)

display(GlobeWidget(config=config))
```

## Runtime Updates and Callbacks

Use `GlobeWidget` setters to update data and accessors after the widget is
rendered. Each datum includes an auto-generated UUID4 `id` unless provided.
Callback payloads include the datum (and its `id`) so you can update visuals in
response to user input.
Runtime update helpers validate UUID4 ids; invalid ids raise a validation error.
Batch updates use the patch models (`PointDatumPatch`, `ArcDatumPatch`,
`PolygonDatumPatch`) so updates are serialized with the correct globe.gl field
names.

```python
widget = GlobeWidget(config=config)
display(widget)

def on_polygon_hover(current, previous):
    if previous:
        widget.update_polygon(
            previous["id"],
            cap_color=previous["base_color"],
            altitude=previous["altitude"],
        )
    if current:
        widget.update_polygon(
            current["id"],
            cap_color="#2f80ff",
            altitude=current["altitude"] + 0.03,
        )

widget.on_polygon_hover(on_polygon_hover)
```

## GeoPandas Helpers (Optional)

Convert GeoDataFrames into layer data using Pandera DataFrameModel validation.
These helpers return Pydantic models (`PointDatum`, `ArcDatum`, `PolygonDatum`).
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

```python
import geopandas as gpd
from shapely.geometry import Polygon

from pyglobegl import polygons_from_gdf

gdf = gpd.GeoDataFrame(
    {
        "name": ["Zone A"],
        "polygons": [
            Polygon([(-10, 0), (-10, 10), (10, 10), (10, 0), (-10, 0)]),
        ],
    },
    geometry="polygons",
    crs="EPSG:4326",
)
polygons = polygons_from_gdf(gdf, include_columns=["name"])
```

`points_from_gdf` defaults to a point geometry column named `point` if present,
otherwise it uses the active GeoDataFrame geometry column (override with
`point_geometry=`). `arcs_from_gdf` expects point geometry columns named
`start` and `end` (override with `start_geometry=` and `end_geometry=`).
`polygons_from_gdf` defaults to a geometry column named `polygons` if present,
otherwise it uses the active GeoDataFrame geometry column (override with
`geometry_column=`).

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
    - [x] Polygons layer
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

### UI Test Artifacts

- Canvas captures are saved under `ui-artifacts` as
  `{test-name}-pass-<timestamp>.png` or `{test-name}-fail-<timestamp>.png`.
- Canvas comparisons use SSIM (structural similarity) with a fixed threshold
  (currently `0.86`).
