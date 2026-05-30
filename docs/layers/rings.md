# Rings Layer

The rings layer animates expanding concentric rings outward from a coordinate,
useful for pings, pulses, or highlighting locations. Each ring is a `RingDatum`.

```python
from IPython.display import display

from pyglobegl import GlobeConfig, GlobeWidget, RingDatum, RingsLayerConfig

rings = [
    RingDatum(lat=0, lng=0, max_radius=4, color="#ff66cc"),
    RingDatum(lat=20, lng=10, max_radius=6, color="#66ccff"),
]

config = GlobeConfig(rings=RingsLayerConfig(rings_data=rings))

display(GlobeWidget(config=config))
```

## `RingDatum`

A ring is defined by `lat`, `lng`, `max_radius`, and `color`, with animation
controls (propagation speed, repeat period) available on `RingsLayerConfig`.

!!! tip "From a GeoDataFrame"

    `rings_from_gdf` builds rings from point geometries, carrying through columns
    such as `max_radius` and `color`. See
    [GeoPandas helpers](../integrations/geopandas.md).
