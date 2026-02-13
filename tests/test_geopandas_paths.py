from __future__ import annotations

from pydantic_extra_types.color import Color
import pytest

from pyglobegl import PathDatum
from pyglobegl.geopandas import paths_from_gdf


def test_paths_from_gdf_linestring() -> None:
    import geopandas as gpd
    import pandas as pd
    from shapely.geometry import LineString

    df = pd.DataFrame(
        {
            "geometry": [
                LineString([(0, 0), (1, 1), (2, 0)]),
                LineString([(10, 10), (11, 11)]),
            ],
            "color": ["#ff0000", "#00ff00"],
            "dash_length": [0.5, 1.0],
        }
    )
    gdf = gpd.GeoDataFrame(df, crs="EPSG:4326")

    paths = paths_from_gdf(gdf, include_columns=["color", "dash_length"])

    assert len(paths) == 2
    assert isinstance(paths[0], PathDatum)
    assert paths[0].path == [(0.0, 0.0), (1.0, 1.0), (0.0, 2.0)]
    assert isinstance(paths[0].color, Color)
    assert paths[0].color.as_hex(format="long") == "#ff0000"
    assert paths[0].dash_length == pytest.approx(0.5)

    assert isinstance(paths[1], PathDatum)
    assert paths[1].path == [(10.0, 10.0), (11.0, 11.0)]
    assert isinstance(paths[1].color, Color)
    assert paths[1].color.as_hex(format="long") == "#00ff00"
    assert paths[1].dash_length == pytest.approx(1.0)


def test_paths_from_gdf_multilinestring() -> None:
    import geopandas as gpd
    import pandas as pd
    from shapely.geometry import MultiLineString

    df = pd.DataFrame(
        {
            "geometry": [MultiLineString([[(0, 0), (1, 1)], [(2, 2), (3, 3)]])],
            "label": ["Multi Path"],
        }
    )
    gdf = gpd.GeoDataFrame(df, crs="EPSG:4326")

    paths = paths_from_gdf(gdf, include_columns=["label"])

    assert len(paths) == 2
    assert paths[0].path == [(0.0, 0.0), (1.0, 1.0)]
    assert paths[1].path == [(2.0, 2.0), (3.0, 3.0)]
    assert all(path.label == "Multi Path" for path in paths)
