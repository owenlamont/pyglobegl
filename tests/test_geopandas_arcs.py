from __future__ import annotations

from typing import Any

import pytest

from pyglobegl import arcs_from_gdf


@pytest.mark.parametrize(
    ("rows", "expected"),
    [
        pytest.param(
            [
                {"start": (0, -10), "end": (5, 20)},
                {"start": (-10, 30), "end": (0, -30)},
            ],
            [
                {"startLat": -10, "startLng": 0, "endLat": 20, "endLng": 5},
                {"startLat": 30, "startLng": -10, "endLat": -30, "endLng": 0},
            ],
            id="basic",
        )
    ],
)
def test_arcs_from_gdf_valid(
    rows: list[dict[str, tuple[float, float]]], expected: list[dict]
) -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    gdf = geopandas.GeoDataFrame(
        {
            "start": [Point(*row["start"]) for row in rows],
            "end": [Point(*row["end"]) for row in rows],
        },
        geometry="start",
        crs=4326,
    )
    arcs = arcs_from_gdf(gdf)
    assert arcs == expected


def test_arcs_from_gdf_missing_columns() -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    gdf = geopandas.GeoDataFrame({"start": [Point(0, 0)]}, geometry="start", crs=4326)

    with pytest.raises(ValueError, match="missing columns"):
        arcs_from_gdf(gdf)


def test_arcs_from_gdf_invalid_ranges() -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    gdf = geopandas.GeoDataFrame(
        {"start": [Point(0, 100)], "end": [Point(0, 0)]}, geometry="start", crs=4326
    )

    with pytest.raises(ValueError, match="invalid arc coordinates"):
        arcs_from_gdf(gdf)


def test_arcs_from_gdf_include_columns() -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    gdf = geopandas.GeoDataFrame(
        {"start": [Point(0, 0)], "end": [Point(10, 0)], "name": ["Arc"]},
        geometry="start",
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
        pytest.param("altitude", -0.2, "must be non-negative", id="altitude-negative"),
        pytest.param(
            "altitude_auto_scale",
            -0.1,
            "must be non-negative",
            id="auto-scale-negative",
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
        pytest.param("color", "notacolor", "valid CSS colors", id="color-invalid"),
        pytest.param("label", 456, "must be strings", id="label-non-string"),
    ],
)
def test_arcs_from_gdf_invalid_optional_column_types(
    column: str, value: Any, match: str
) -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    gdf = geopandas.GeoDataFrame(
        {"start": [Point(0, 0)], "end": [Point(10, 0)], column: [value]},
        geometry="start",
        crs=4326,
    )

    with pytest.raises(ValueError, match=match):
        arcs_from_gdf(gdf)
