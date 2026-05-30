# Paths Layer

![Path lines traced across the globe](../images/layers/paths.png)

The paths layer draws a polyline that follows a sequence of coordinates along the
surface. Each line is a `PathDatum`.

```python
from IPython.display import display

from pyglobegl import GlobeConfig, GlobeWidget, PathDatum, PathsLayerConfig

paths = [
    PathDatum(path=[(0, 0), (5, 5), (10, 0)], color="#66ccff", dash_length=0.02),
]

config = GlobeConfig(
    paths=PathsLayerConfig(paths_data=paths, path_transition_duration=0),
)

display(GlobeWidget(config=config))
```

## `PathDatum`

A path is a list of `(lat, lng)` (or `(lat, lng, altitude)`) coordinates plus
appearance fields such as `color`, `stroke`, `dash_length`, `dash_gap`, and
`dash_animate_time`. Layer-level options like `path_transition_duration` live on
`PathsLayerConfig`.

!!! tip "From a GeoDataFrame or trajectory"

    `paths_from_gdf` builds paths from `LineString` geometries, and
    `paths_from_mpd` builds them from MovingPandas trajectories. See
    [GeoPandas helpers](../integrations/geopandas.md) and
    [MovingPandas helpers](../integrations/movingpandas.md).
