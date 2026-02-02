from __future__ import annotations

from typing import Any

import pytest

from pyglobegl import ArcDatum, arcs_from_gdf


@pytest.mark.parametrize(
    ("rows", "expected"),
    [
        pytest.param(
            [
                {"start": (0, -10), "end": (5, 20)},
                {"start": (-10, 30), "end": (0, -30)},
            ],
            [
                ArcDatum(start_lat=-10, start_lng=0, end_lat=20, end_lng=5),
                ArcDatum(start_lat=30, start_lng=-10, end_lat=-30, end_lng=0),
            ],
            id="basic",
        )
    ],
)
def test_arcs_from_gdf_valid(
    rows: list[dict[str, tuple[float, float]]], expected: list[ArcDatum]
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
    assert len(arcs) == len(expected)
    for arc, expect in zip(arcs, expected, strict=True):
        assert isinstance(arc, ArcDatum)
        assert arc.start_lat == expect.start_lat
        assert arc.start_lng == expect.start_lng
        assert arc.end_lat == expect.end_lat
        assert arc.end_lng == expect.end_lng


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

    with pytest.raises(ValueError, match="arcs_from_gdf schema validation failed"):
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
    assert len(arcs) == 1
    arc = arcs[0]
    assert isinstance(arc, ArcDatum)
    assert arc.start_lat == 0
    assert arc.start_lng == 0
    assert arc.end_lat == 0
    assert arc.end_lng == 10
    payload = arc.model_dump(
        exclude={"id", "start_lat", "start_lng", "end_lat", "end_lng"}
    )
    assert payload["name"] == "Arc"


@pytest.mark.parametrize(
    ("column", "value", "match"),
    [
        pytest.param("altitude", "high", "valid number", id="altitude-string"),
        pytest.param(
            "altitude_auto_scale", "auto", "valid number", id="auto-scale-string"
        ),
        pytest.param("stroke", "wide", "valid number", id="stroke-string"),
        pytest.param("dash_length", "short", "valid number", id="dash-length-string"),
        pytest.param("dash_gap", "gap", "valid number", id="dash-gap-string"),
        pytest.param(
            "dash_initial_gap", "gap", "valid number", id="dash-initial-gap-string"
        ),
        pytest.param(
            "dash_animate_time", "fast", "valid number", id="dash-animate-time-string"
        ),
        pytest.param(
            "altitude", -0.2, "greater than or equal to 0", id="altitude-negative"
        ),
        pytest.param(
            "altitude_auto_scale",
            -0.1,
            "greater than or equal to 0",
            id="auto-scale-negative",
        ),
        pytest.param("stroke", -0.3, "greater than 0", id="stroke-negative"),
        pytest.param("dash_length", -0.1, "greater than 0", id="dash-length-negative"),
        pytest.param(
            "dash_gap", -0.1, "greater than or equal to 0", id="dash-gap-negative"
        ),
        pytest.param(
            "dash_initial_gap",
            -0.1,
            "greater than or equal to 0",
            id="dash-initial-gap-negative",
        ),
        pytest.param(
            "dash_animate_time",
            -1.0,
            "greater than or equal to 0",
            id="dash-animate-time-negative",
        ),
        pytest.param("color", 123, "valid color", id="color-non-string"),
        pytest.param("color", "notacolor", "valid color", id="color-invalid"),
        pytest.param("label", 456, "valid string", id="label-non-string"),
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
