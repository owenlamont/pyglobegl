from __future__ import annotations

import pytest

from pyglobegl.movingpandas import paths_from_mpd


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

    paths = paths_from_mpd(tc, include_columns=["group"])

    assert len(paths) == 2

    path1 = next(p for p in paths if p.path[0] == (0.0, 0.0))
    assert getattr(path1, "group", None) == "A"

    path2 = next(p for p in paths if p.path[0] == (10.0, 10.0))
    assert getattr(path2, "group", None) == "B"
