# Heatmaps Layer

![Population-density heatmap on the globe](../images/layers/heatmaps.png)

The heatmaps layer renders weighted density fields over the surface. Each
`HeatmapDatum` holds a collection of `HeatmapPointDatum` samples plus bandwidth
and colour controls.

```python
from IPython.display import display

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

## `HeatmapDatum` and `HeatmapPointDatum`

- `HeatmapPointDatum` &mdash; one sample with `lat`, `lng`, and `weight`.
- `HeatmapDatum` &mdash; a group of points plus `bandwidth` (kernel width) and
  `color_saturation` controlling how intensity maps to colour.

!!! tip "From a GeoDataFrame"

    `heatmaps_from_gdf` builds heatmap points from point geometries with a
    `weight_column`. See [GeoPandas helpers](../integrations/geopandas.md).
