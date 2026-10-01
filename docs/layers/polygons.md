# Polygons Layer

![Choropleth country polygons extruded on the globe](../images/layers/polygons.png)

The polygons layer extrudes GeoJSON polygons into 3D caps and sides. Geometry is
supplied as a [`geojson_pydantic.Polygon`](https://github.com/developmentseed/geojson-pydantic)
inside a `PolygonDatum`.

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

## `PolygonDatum`

A polygon carries its `geometry` plus appearance fields such as `cap_color`,
`side_color`, `stroke_color`, and `altitude` (extrusion height).

!!! note "Ring winding order"

    Either winding renders correctly. globe.gl follows d3-geo's spherical
    convention, which is the reverse of the GeoJSON spec's right-hand rule, so
    pyglobegl rewinds each polygon in the browser before drawing it. The geometry
    on your `PolygonDatum` is left as you supplied it, and the GeoPandas helpers
    emit spec-compliant rings: exteriors counter-clockwise, holes clockwise.
    Each ring is read as the smaller of the two regions it divides the sphere into,
    so a single polygon cannot cover more than half the globe.

## Custom tooltip

`PolygonDatum.label` is each polygon's hover tooltip. To compute one from the datum
or share a constant across the layer, set a layer-level `polygon_label` &mdash; a
[frontend Python callback](../guides/frontend-callbacks.md) (datum &rarr; string),
a plain string (one tooltip for every polygon), or `None` (the default) to use each
datum's `label`. Swap it at runtime with `GlobeWidget.set_polygon_label(...)`.

!!! tip "From a GeoDataFrame"

    `polygons_from_gdf` defaults to a geometry column named `polygons` if present,
    otherwise the active geometry column. See
    [GeoPandas helpers](../integrations/geopandas.md).
