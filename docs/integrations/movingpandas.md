# MovingPandas Helpers

!!! note "Optional extra"

    These helpers require the `movingpandas` extra (which also pulls in GeoPandas
    and Pandera): `pip install "pyglobegl[movingpandas]"`. See
    [Installation](../getting-started/installation.md).

`paths_from_mpd` turns a [MovingPandas](https://movingpandas.org/) `Trajectory`
into [paths-layer](../layers/paths.md) data (`PathDatum`), so movement tracks can
be drawn on the globe. The trajectory's ordered point geometries become the path
vertices.

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

The result is a list of `PathDatum` you can hand to a
[`PathsLayerConfig`](../layers/paths.md). Trajectories are rendered statically
(no time animation) in this version.
