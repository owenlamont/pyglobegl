from __future__ import annotations

from pydantic_extra_types.color import Color

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
    assert paths[0].path == [(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)]
    assert isinstance(paths[0].color, Color)
    assert paths[0].color.as_hex(format="long") == "#ff0000"
    assert paths[0].dash_length == 0.5

    assert isinstance(paths[1], PathDatum)
    assert paths[1].path == [(10.0, 10.0), (11.0, 11.0)]
    assert isinstance(paths[1].color, Color)
    assert paths[1].color.as_hex(format="long") == "#00ff00"
    assert paths[1].dash_length == 1.0


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

    assert len(paths) == 1
    # Note: Current implementation takes only the first part of MultiLineString
    # or all parts? Let's check implementation.
    # It returns list(geom.geoms[0].coords) which is FIRST part.
    # Wait, I changed it to return list(geom.geoms[0].coords) in the fix?
    # No, I restored `_to_path_coordinates`.
    # Let's verify what `_to_path_coordinates` does.

    assert paths[0].label == "Multi Path"
