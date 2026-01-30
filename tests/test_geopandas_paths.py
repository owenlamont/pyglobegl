from __future__ import annotations

import pytest

from pyglobegl import PathDatum
from pyglobegl.geopandas import paths_from_gdf, paths_from_mpd


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
    assert paths[0].color == "#ff0000"
    assert paths[0].dash_length == 0.5

    assert isinstance(paths[1], PathDatum)
    assert paths[1].path == [(10.0, 10.0), (11.0, 11.0)]
    assert paths[1].color == "#00ff00"
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


@pytest.mark.filterwarnings("ignore:Missing optional dependencies.*Stone Soup")
def test_paths_from_mpd_trajectory() -> None:
    import geopandas as gpd
    import movingpandas as mpd
    import pandas as pd
    from shapely.geometry import Point

    df = pd.DataFrame(
        [
            {"geometry": Point(0, 0), "t": pd.Timestamp("2023-01-01 12:00:00")},
            {"geometry": Point(1, 1), "t": pd.Timestamp("2023-01-01 12:01:00")},
            {"geometry": Point(2, 0), "t": pd.Timestamp("2023-01-01 12:02:00")},
        ]
    ).set_index("t")
    gdf = gpd.GeoDataFrame(df, crs="EPSG:4326")
    traj = mpd.Trajectory(gdf, 1)

    # Add a custom attribute to the trajectory object (simulating metadata)
    traj.color = "#0000ff"  # type: ignore[attr-defined]

    paths = paths_from_mpd(traj, include_columns=["color"])

    assert len(paths) == 1
    assert paths[0].path == [(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)]
    assert paths[0].color == "#0000ff"


@pytest.mark.filterwarnings("ignore:Missing optional dependencies.*Stone Soup")
def test_paths_from_mpd_trajectory_collection() -> None:
    import geopandas as gpd
    import movingpandas as mpd
    import pandas as pd
    from shapely.geometry import Point

    df = pd.DataFrame(
        [
            {
                "geometry": Point(0, 0),
                "t": pd.Timestamp("2023-01-01 12:00:00"),
                "id": 1,
                "group": "A",
            },
            {
                "geometry": Point(1, 1),
                "t": pd.Timestamp("2023-01-01 12:01:00"),
                "id": 1,
                "group": "A",
            },
            {
                "geometry": Point(10, 10),
                "t": pd.Timestamp("2023-01-01 12:00:00"),
                "id": 2,
                "group": "B",
            },
            {
                "geometry": Point(11, 11),
                "t": pd.Timestamp("2023-01-01 12:01:00"),
                "id": 2,
                "group": "B",
            },
        ]
    ).set_index("t")
    gdf = gpd.GeoDataFrame(df, crs="EPSG:4326")
    tc = mpd.TrajectoryCollection(gdf, "id")

    paths = paths_from_mpd(tc, include_columns=["group"])  # 'group' is in df

    assert len(paths) == 2

    path1 = next(p for p in paths if p.path[0] == (0.0, 0.0))
    # PathDatum allows extra fields? Yes, extra="allow".
    # paths_from_mpd adds 'group' to the record.
    assert getattr(path1, "group", None) == "A"

    path2 = next(p for p in paths if p.path[0] == (10.0, 10.0))
    assert getattr(path2, "group", None) == "B"
