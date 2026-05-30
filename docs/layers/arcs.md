# Arcs Layer

The arcs layer draws great-circle arcs between two coordinates, lifted off the
surface by `altitude`. Each arc is an `ArcDatum`.

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

## `ArcDatum`

An arc is defined by its endpoints (`start_lat`, `start_lng`, `end_lat`,
`end_lng`) plus appearance fields such as `altitude`, `color`, and `stroke`.

!!! tip "From a GeoDataFrame"

    `arcs_from_gdf` expects point geometry columns named `start` and `end`
    (override with `start_geometry=` / `end_geometry=`). See
    [GeoPandas helpers](../integrations/geopandas.md).
