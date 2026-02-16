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

Optional MovingPandas extra (includes GeoPandas + Pandera):

```bash
pip install pyglobegl[movingpandas]
```

```bash
uv add pyglobegl[movingpandas]
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

pyglobegl expects layer data as Pydantic models (for example: `PointDatum`,
`ArcDatum`, `PolygonDatum`, `PathDatum`, `HeatmapDatum`, `HexBinPointDatum`,
`HexPolygonDatum`, `TileDatum`, `ParticleDatum`, `RingDatum`, `LabelDatum`).
Dynamic accessor remapping is not supported; per-datum values are read from the
model field names. Numeric fields reject string values, and data model defaults
mirror globe.gl defaults so omitted values still render predictably.

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

### Paths Example

```python
from pyglobegl import GlobeConfig, GlobeWidget, PathDatum, PathsLayerConfig

paths = [
    PathDatum(
        path=[(0, 0), (5, 5), (10, 0)], color="#66ccff", dash_length=0.02
    ),
]

config = GlobeConfig(
    paths=PathsLayerConfig(paths_data=paths, path_transition_duration=0),
)

display(GlobeWidget(config=config))
```

## Heatmaps Layer

```python
from pyglobegl import (
    GlobeConfig,
    GlobeWidget,
    HeatmapDatum,
    HeatmapPointDatum,
    HeatmapsLayerConfig,
)

heatmap = HeatmapDatum(
    points=[
        HeatmapPointDatum(lat=0, lng=0, weight=1.0),
        HeatmapPointDatum(lat=10, lng=10, weight=0.6),
    ],
    bandwidth=0.8,
    color_saturation=2.5,
)

config = GlobeConfig(heatmaps=HeatmapsLayerConfig(heatmaps_data=[heatmap]))

display(GlobeWidget(config=config))
```

## Hex Bin Layer (MicroPython Accessors)

```python
from pyglobegl import (
    GlobeConfig,
    GlobeWidget,
    HexBinLayerConfig,
    HexBinPointDatum,
    frontend_python,
)


@frontend_python
def hex_altitude(hexbin):
    return hexbin["sumWeight"] * 0.01


@frontend_python
def point_weight(point):
    # point is an individual input row from hex_bin_points_data
    return point["weight"] * 2.0


@frontend_python
def hex_color(hexbin):
    return "#ff5500" if hexbin["sumWeight"] > 2 else "#66ccff"


@frontend_python
def hex_label(hexbin):
    return f"<b>{len(hexbin['points'])}</b> points in this hex bin"


points = [
    HexBinPointDatum(lat=0, lng=0, weight=1.0),
    HexBinPointDatum(lat=12, lng=15, weight=3.5),
]

config = GlobeConfig(
    hex_bin=HexBinLayerConfig(
        hex_bin_points_data=points,
        hex_bin_point_weight=point_weight,
        hex_altitude=hex_altitude,
        hex_top_color=hex_color,
        hex_side_color=hex_color,
        hex_label=hex_label,
    )
)

display(GlobeWidget(config=config))
```

Frontend callback arguments are normalized to plain Python values (dict/list/
str/float/bool/None) when they are JSON-serializable, so dict methods like
`.get(...)` work in callbacks such as `hex_label`.

`hex_margin`, `hex_bin_point_lat`, `hex_bin_point_lng`, and
`hex_bin_point_weight` also accept `@frontend_python` callbacks when you need
frontend-computed accessors without writing JavaScript.

## Hexed Polygons Layer

```python
from geojson_pydantic import Polygon

from pyglobegl import (
    GlobeConfig,
    GlobeWidget,
    HexPolygonDatum,
    HexedPolygonsLayerConfig,
)

geometry = Polygon(
    type="Polygon",
    coordinates=[
        [(-10, 0), (-10, 10), (10, 10), (10, 0), (-10, 0)],
    ],
)

hexed = [
    HexPolygonDatum(geometry=geometry, color="#ffcc00", altitude=0.05),
]

config = GlobeConfig(
    hexed_polygons=HexedPolygonsLayerConfig(hex_polygons_data=hexed)
)

display(GlobeWidget(config=config))
```

## Tiles Layer

```python
from pyglobegl import (
    GlobeConfig,
    GlobeMaterialSpec,
    GlobeWidget,
    TileDatum,
    TilesLayerConfig,
)

tiles = [
    TileDatum(
        lat=0,
        lng=0,
        width=10,
        height=10,
        material=GlobeMaterialSpec(
            type="MeshLambertMaterial",
            params={"color": "#66ccff", "opacity": 0.6, "transparent": True},
        ),
    )
]

config = GlobeConfig(tiles=TilesLayerConfig(tiles_data=tiles))

display(GlobeWidget(config=config))
```

## Particles Layer

```python
from pyglobegl import (
    GlobeConfig,
    GlobeWidget,
    ParticleDatum,
    ParticlePointDatum,
    ParticlesLayerConfig,
)

particles = [
    ParticleDatum(
        particles=[
            ParticlePointDatum(lat=0, lng=0, altitude=0.2, label="Alpha"),
            ParticlePointDatum(lat=10, lng=10, altitude=0.2, label="Beta"),
        ],
        color="palegreen",
        size=2.0,
    )
]

config = GlobeConfig(particles=ParticlesLayerConfig(particles_data=particles))

display(GlobeWidget(config=config))
```

## Rings Layer

```python
from pyglobegl import GlobeConfig, GlobeWidget, RingDatum, RingsLayerConfig

rings = [
    RingDatum(lat=0, lng=0, max_radius=4, color="#ff66cc"),
    RingDatum(lat=20, lng=10, max_radius=6, color="#66ccff"),
]

config = GlobeConfig(rings=RingsLayerConfig(rings_data=rings))

display(GlobeWidget(config=config))
```

## Labels Layer

```python
from pyglobegl import GlobeConfig, GlobeWidget, LabelDatum, LabelsLayerConfig

labels = [
    LabelDatum(lat=0, lng=0, text="Center", color="#ffcc00"),
    LabelDatum(lat=15, lng=20, text="North", color="#66ccff", include_dot=True),
]

config = GlobeConfig(labels=LabelsLayerConfig(labels_data=labels))

display(GlobeWidget(config=config))
```

## Runtime Updates and Callbacks

Use `GlobeWidget` setters to update data and accessors after the widget is
rendered. Each datum includes an auto-generated UUID4 `id` unless provided.
Callback payloads include the datum (and its `id`) so you can update visuals in
response to user input.
Runtime update helpers validate UUID4 ids; invalid ids raise a validation error.
Batch updates use the patch models (`PointDatumPatch`, `ArcDatumPatch`,
`PolygonDatumPatch`, `PathDatumPatch`, `HeatmapDatumPatch`,
`HexPolygonDatumPatch`, `TileDatumPatch`, `ParticleDatumPatch`,
`RingDatumPatch`, `LabelDatumPatch`) so updates are
serialized with the correct globe.gl field names.

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

Hover callbacks are only wired when you register a hover handler. This avoids
continuous hover traffic for layers you are not interacting with, and matches
globe.gl behavior (no hover cursor when no hover callback is registered).

## GeoPandas Helpers (Optional)

Convert GeoDataFrames into layer data using Pandera DataFrameModel validation.
These helpers return Pydantic models (`PointDatum`, `ArcDatum`, `PolygonDatum`,
`PathDatum`, `HeatmapDatum`, `HexPolygonDatum`, `TileDatum`, `ParticleDatum`,
`RingDatum`, `LabelDatum`).
Point geometries are reprojected to EPSG:4326 before extracting lat/lng.
`points_from_gdf` defaults to a point geometry column named `point` if present,
otherwise it uses the active GeoDataFrame geometry column (override with
`point_geometry=`). `arcs_from_gdf` expects point geometry columns named
`start` and `end` (override with `start_geometry=` and `end_geometry=`).
`polygons_from_gdf` defaults to a geometry column named `polygons` if present,
otherwise it uses the active GeoDataFrame geometry column (override with
`geometry_column=`). `paths_from_gdf` defaults to a geometry column named
`paths` if present, otherwise it uses the active GeoDataFrame geometry column
(override with `geometry_column=`).

### Points Example

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

### Arcs Example

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

### Polygons Example

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

### Paths Example

```python
import geopandas as gpd
from shapely.geometry import LineString

from pyglobegl import paths_from_gdf

gdf = gpd.GeoDataFrame(
    {
        "name": ["Route A"],
        "paths": [LineString([(0, 0), (5, 5), (10, 0)])],
    },
    geometry="paths",
    crs="EPSG:4326",
)
paths = paths_from_gdf(gdf, include_columns=["name"])
```

### Heatmaps Example

```python
import geopandas as gpd
from shapely.geometry import Point

from pyglobegl import heatmaps_from_gdf

gdf = gpd.GeoDataFrame(
    {
        "weight": [1.0, 0.6],
        "point": [Point(0, 0), Point(10, 10)],
    },
    geometry="point",
    crs="EPSG:4326",
)
heatmaps = heatmaps_from_gdf(gdf, weight_column="weight", bandwidth=0.8)
```

### Hex Bin Points Example

```python
import geopandas as gpd
from shapely.geometry import Point

from pyglobegl import hexbin_points_from_gdf

gdf = gpd.GeoDataFrame(
    {
        "population": [2_100_000, 450_000],
        "point": [Point(0, 0), Point(10, 10)],
    },
    geometry="point",
    crs="EPSG:4326",
)
hex_points = hexbin_points_from_gdf(gdf, weight_column="population")
```

### Hexed Polygons Example

```python
import geopandas as gpd
from shapely.geometry import Polygon

from pyglobegl import hexed_polygons_from_gdf

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
hexed = hexed_polygons_from_gdf(gdf, include_columns=["name"])
```

### Tiles Example

```python
import geopandas as gpd
from shapely.geometry import Point

from pyglobegl import tiles_from_gdf

gdf = gpd.GeoDataFrame(
    {
        "width": [10.0],
        "height": [10.0],
        "point": [Point(0, 0)],
    },
    geometry="point",
    crs="EPSG:4326",
)
tiles = tiles_from_gdf(gdf, include_columns=["width", "height"])
```

### Particles Example

```python
import geopandas as gpd
from shapely.geometry import Point

from pyglobegl import particles_from_gdf

gdf = gpd.GeoDataFrame(
    {
        "altitude": [0.2, 0.2],
        "point": [Point(0, 0), Point(10, 10)],
    },
    geometry="point",
    crs="EPSG:4326",
)
particles = particles_from_gdf(
    gdf, altitude_column="altitude", color="palegreen"
)
```

### Rings Example

```python
import geopandas as gpd
from shapely.geometry import Point

from pyglobegl import rings_from_gdf

gdf = gpd.GeoDataFrame(
    {
        "max_radius": [4.0, 6.0],
        "color": ["#ff66cc", "#66ccff"],
        "point": [Point(0, 0), Point(20, 10)],
    },
    geometry="point",
    crs="EPSG:4326",
)
rings = rings_from_gdf(gdf, include_columns=["max_radius", "color"])
```

### Labels Example

```python
import geopandas as gpd
from shapely.geometry import Point

from pyglobegl import labels_from_gdf

gdf = gpd.GeoDataFrame(
    {
        "text": ["Center", "North"],
        "color": ["#ffcc00", "#66ccff"],
        "point": [Point(0, 0), Point(15, 20)],
    },
    geometry="point",
    crs="EPSG:4326",
)
labels = labels_from_gdf(gdf, include_columns=["color"])
```

## MovingPandas Helpers (Optional)

### MovingPandas Example

```python
import geopandas as gpd
import movingpandas as mpd
import pandas as pd
from shapely.geometry import Point

from pyglobegl import paths_from_mpd

df = pd.DataFrame(
    [
        {"geometry": Point(0, 0), "t": pd.Timestamp("2023-01-01 12:00:00")},
        {"geometry": Point(1, 1), "t": pd.Timestamp("2023-01-01 12:01:00")},
        {"geometry": Point(2, 0), "t": pd.Timestamp("2023-01-01 12:02:00")},
    ]
).set_index("t")
gdf = gpd.GeoDataFrame(df, crs="EPSG:4326")
traj = mpd.Trajectory(gdf, 1)

paths = paths_from_mpd(traj)
```

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
    - [x] Paths layer
    - [x] Heatmaps layer
    - [x] Hex bin layer
    - [x] Hexed polygons layer
    - [x] Tiles layer
    - [x] Particles layer
    - [x] Rings layer
    - [x] Labels layer
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
