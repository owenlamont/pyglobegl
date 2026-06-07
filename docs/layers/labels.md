# Labels Layer

![World-city labels on the globe](../images/layers/labels.png)

The labels layer places text labels (optionally with a marker dot) at
coordinates on the surface. Each label is a `LabelDatum`.

```python
from IPython.display import display

from pyglobegl import GlobeConfig, GlobeWidget, LabelDatum, LabelsLayerConfig

labels = [
    LabelDatum(lat=0, lng=0, text="Center", color="#ffcc00"),
    LabelDatum(lat=15, lng=20, text="North", color="#66ccff", include_dot=True),
]

config = GlobeConfig(labels=LabelsLayerConfig(labels_data=labels))

display(GlobeWidget(config=config))
```

## `LabelDatum`

A label carries `lat`, `lng`, `text`, and `color`, plus styling fields such as
`size`, `dot_radius`, `include_dot`, and `label_orientation`.

## Custom tooltip

`LabelDatum.label` is each label's hover tooltip (distinct from the rendered 3D
`text`). To compute one from the datum or share a constant across the layer, set a
layer-level `label_label` &mdash; a
[frontend Python callback](../guides/frontend-callbacks.md) (datum &rarr; string),
a plain string (one tooltip for all), or `None` (the default) to use each datum's
`label`. Swap it at runtime with `GlobeWidget.set_label_label(...)`.

!!! tip "From a GeoDataFrame"

    `labels_from_gdf` builds labels from point geometries with a `text` column;
    pass extra columns through `include_columns=`. See
    [GeoPandas helpers](../integrations/geopandas.md).
