# GeoPandas Helpers

!!! note "Optional extra"

    These helpers require the `geopandas` extra:
    `pip install "pyglobegl[geopandas]"`. See [Installation](../getting-started/installation.md).

The `*_from_gdf` helpers convert GeoDataFrames into layer data, validating input
with [Pandera](https://pandera.readthedocs.io/) `DataFrameModel` schemas and
returning the same Pydantic models the layers expect (`PointDatum`, `ArcDatum`,
`PolygonDatum`, `PathDatum`, `HeatmapDatum`, `HexPolygonDatum`, `TileDatum`,
`ParticleDatum`, `RingDatum`, `LabelDatum`).

Point geometries are reprojected to **EPSG:4326** before lat/lng are extracted.

## Geometry-column conventions

| Helper | Default geometry column | Override |
| --- | --- | --- |
| `points_from_gdf` | `point` if present, else active geometry | `point_geometry=` |
| `arcs_from_gdf` | `start` and `end` | `start_geometry=` / `end_geometry=` |
| `polygons_from_gdf` | `polygons` if present, else active geometry | `geometry_column=` |
| `paths_from_gdf` | `paths` if present, else active geometry | `geometry_column=` |

Most helpers accept `include_columns=` to carry extra attributes onto the
resulting models as metadata.

## Points

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

## Arcs

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

## Polygons

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

## Paths

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

## Heatmaps

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

## Hex bin points

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

## Hexed polygons

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

## Tiles

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

## Particles

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
particles = particles_from_gdf(gdf, altitude_column="altitude", color="palegreen")
```

## Rings

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

## Labels

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
