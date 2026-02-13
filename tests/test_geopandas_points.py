from __future__ import annotations

from itertools import starmap
from typing import Any

import pytest

from pyglobegl import PointDatum, points_from_gdf


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
def test_points_from_gdf_validates_schema(
    crs: str, geometry: list[tuple[float, float]], expected: list[dict[str, Any]]
) -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    gdf = geopandas.GeoDataFrame(
        {"name": ["A", "B"], "value": [1, 2], "point": list(starmap(Point, geometry))},
        geometry="point",
        crs=crs,
    )

    points = points_from_gdf(gdf, include_columns=["name", "value"])
    assert len(points) == len(expected)
    for point, expect in zip(points, expected, strict=True):
        assert isinstance(point, PointDatum)
        assert point.lat == expect["lat"]
        assert point.lng == expect["lng"]
        assert point.altitude == pytest.approx(0.1)
        assert point.radius == pytest.approx(0.25)
        assert point.color.as_hex(format="long") == "#ffffaa"
        assert point.model_dump(
            exclude={"id", "lat", "lng", "altitude", "radius", "color", "label"}
        ) == {key: expect[key] for key in expect if key not in {"lat", "lng"}}


def test_points_from_gdf_requires_crs() -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    gdf = geopandas.GeoDataFrame(
        {"name": ["A"], "value": [1], "point": [Point(10, 5)]},
        geometry="point",
        crs=None,
    )

    with pytest.raises(ValueError, match="CRS"):
        points_from_gdf(gdf, include_columns=["name", "value"])


def test_points_from_gdf_rejects_non_point_geometry() -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import LineString

    gdf = geopandas.GeoDataFrame(
        {"name": ["A"], "value": [1], "point": [LineString([(0, 0), (1, 1)])]},
        geometry="point",
        crs="EPSG:4326",
    )

    with pytest.raises(ValueError, match="Point geometries"):
        points_from_gdf(gdf, include_columns=["name", "value"])


def test_points_from_gdf_missing_columns() -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    gdf = geopandas.GeoDataFrame(
        {"name": ["A"], "point": [Point(10, 5)]}, geometry="point", crs="EPSG:4326"
    )

    with pytest.raises(ValueError, match="missing columns"):
        points_from_gdf(gdf, include_columns=["name", "value"])


@pytest.mark.parametrize(
    ("column", "value", "match"),
    [
        pytest.param("altitude", "high", "valid number", id="altitude-string"),
        pytest.param("radius", "wide", "valid number", id="radius-string"),
        pytest.param(
            "altitude", -1.0, "greater than or equal to 0", id="altitude-negative"
        ),
        pytest.param("radius", -2.0, "greater than 0", id="radius-negative"),
        pytest.param("color", 123, "valid color", id="color-non-string"),
        pytest.param("color", "notacolor", "valid color", id="color-invalid"),
        pytest.param("label", 456, "valid string", id="label-non-string"),
    ],
)
def test_points_from_gdf_invalid_optional_column_types(
    column: str, value: Any, match: str
) -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    gdf = geopandas.GeoDataFrame(
        {"point": [Point(10, 5)], column: [value]}, geometry="point", crs="EPSG:4326"
    )

    with pytest.raises(ValueError, match=match):
        points_from_gdf(gdf)
