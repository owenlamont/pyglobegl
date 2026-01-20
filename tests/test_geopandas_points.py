from __future__ import annotations

from itertools import starmap

import pytest

from pyglobegl import points_from_gdf


@pytest.mark.parametrize(
    ("crs", "geometry", "expected"),
    [
        pytest.param(
            "EPSG:4326",
            [(10, 5), (-20, 40)],
            [
                {"lat": 5.0, "lng": 10.0, "name": "A", "value": 1},
                {"lat": 40.0, "lng": -20.0, "name": "B", "value": 2},
            ],
            id="epsg-4326",
        ),
        pytest.param(
            "EPSG:3857",
            [(0.0, 0.0), (1_000_000.0, 1_000_000.0)],
            [
                {"lat": 0.0, "lng": 0.0, "name": "A", "value": 1},
                {
                    "lat": pytest.approx(8.9466, rel=1e-3),
                    "lng": pytest.approx(8.9831, rel=1e-3),
                    "name": "B",
                    "value": 2,
                },
            ],
            id="epsg-3857",
        ),
    ],
)
def test_points_from_gdf_requires_geopandas(
    crs: str, geometry: list[tuple[float, float]], expected: list[dict[str, object]]
) -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    gdf = geopandas.GeoDataFrame(
        {"name": ["A", "B"], "value": [1, 2]},
        geometry=list(starmap(Point, geometry)),
        crs=crs,
    )

    points = points_from_gdf(gdf, include_columns=["name", "value"])
    assert points == expected


def test_points_from_gdf_requires_crs() -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    gdf = geopandas.GeoDataFrame(
        {"name": ["A"], "value": [1]}, geometry=[Point(10, 5)], crs=None
    )

    with pytest.raises(ValueError, match="CRS"):
        points_from_gdf(gdf, include_columns=["name", "value"])
