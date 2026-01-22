from __future__ import annotations

import pytest

from pyglobegl import arcs_from_gdf


@pytest.mark.parametrize(
    ("rows", "expected"),
    [
        pytest.param(
            [
                {"start_lat": 0, "start_lng": -10, "end_lat": 5, "end_lng": 20},
                {"start_lat": -10, "start_lng": 30, "end_lat": 0, "end_lng": -30},
            ],
            [
                {"startLat": 0, "startLng": -10, "endLat": 5, "endLng": 20},
                {"startLat": -10, "startLng": 30, "endLat": 0, "endLng": -30},
            ],
            id="basic",
        )
    ],
)
def test_arcs_from_gdf_valid(
    rows: list[dict[str, float]], expected: list[dict]
) -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    gdf = geopandas.GeoDataFrame(rows, geometry=[Point(0, 0)] * len(rows), crs=4326)
    arcs = arcs_from_gdf(gdf)
    assert arcs == expected


def test_arcs_from_gdf_missing_columns() -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    gdf = geopandas.GeoDataFrame(
        {"start_lat": [0], "start_lng": [0], "end_lat": [0]},
        geometry=[Point(0, 0)],
        crs=4326,
    )

    with pytest.raises(ValueError, match="missing columns"):
        arcs_from_gdf(gdf)


def test_arcs_from_gdf_invalid_ranges() -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    gdf = geopandas.GeoDataFrame(
        {"start_lat": [100], "start_lng": [0], "end_lat": [0], "end_lng": [0]},
        geometry=[Point(0, 0)],
        crs=4326,
    )

    with pytest.raises(ValueError, match="invalid arc coordinates"):
        arcs_from_gdf(gdf)


def test_arcs_from_gdf_include_columns() -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    gdf = geopandas.GeoDataFrame(
        {
            "start_lat": [0],
            "start_lng": [0],
            "end_lat": [0],
            "end_lng": [10],
            "name": ["Arc"],
        },
        geometry=[Point(0, 0)],
        crs=4326,
    )

    arcs = arcs_from_gdf(gdf, include_columns=["name"])
    assert arcs == [
        {"name": "Arc", "startLat": 0, "startLng": 0, "endLat": 0, "endLng": 10}
    ]


@pytest.mark.parametrize(
    ("column", "value", "match"),
    [
        pytest.param("altitude", "high", "must be numeric", id="altitude-string"),
        pytest.param(
            "altitude_auto_scale", "auto", "must be numeric", id="auto-scale-string"
        ),
        pytest.param("stroke", "wide", "must be numeric", id="stroke-string"),
        pytest.param(
            "dash_length", "short", "must be numeric", id="dash-length-string"
        ),
        pytest.param("dash_gap", "gap", "must be numeric", id="dash-gap-string"),
        pytest.param(
            "dash_initial_gap", "gap", "must be numeric", id="dash-initial-gap-string"
        ),
        pytest.param(
            "dash_animate_time",
            "fast",
            "must be numeric",
            id="dash-animate-time-string",
        ),
        pytest.param("altitude", -0.2, "must be positive", id="altitude-negative"),
        pytest.param(
            "altitude_auto_scale", -0.1, "must be positive", id="auto-scale-negative"
        ),
        pytest.param("stroke", -0.3, "must be positive", id="stroke-negative"),
        pytest.param(
            "dash_length", -0.1, "must be positive", id="dash-length-negative"
        ),
        pytest.param("dash_gap", -0.1, "must be positive", id="dash-gap-negative"),
        pytest.param(
            "dash_initial_gap", -0.1, "must be positive", id="dash-initial-gap-negative"
        ),
        pytest.param(
            "dash_animate_time",
            -1.0,
            "must be positive",
            id="dash-animate-time-negative",
        ),
        pytest.param("color", 123, "must be strings", id="color-non-string"),
        pytest.param("label", 456, "must be strings", id="label-non-string"),
    ],
)
def test_arcs_from_gdf_invalid_optional_column_types(
    column: str, value: object, match: str
) -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    gdf = geopandas.GeoDataFrame(
        {
            "start_lat": [0],
            "start_lng": [0],
            "end_lat": [0],
            "end_lng": [10],
            column: [value],
        },
        geometry=[Point(0, 0)],
        crs=4326,
    )

    with pytest.raises(ValueError, match=match):
        arcs_from_gdf(gdf)
