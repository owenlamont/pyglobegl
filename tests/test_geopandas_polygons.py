from __future__ import annotations

from geojson_pydantic import (
    MultiPolygon as GeoJsonMultiPolygon,
    Polygon as GeoJsonPolygon,
)
import geopandas as gpd
from pydantic_extra_types.color import Color
import pytest
from shapely.geometry import MultiPolygon, Point, Polygon

from pyglobegl import PolygonDatum, polygons_from_gdf


def _square(west: float, south: float, east: float, north: float) -> Polygon:
    return Polygon(
        [(west, south), (west, north), (east, north), (east, south), (west, south)]
    )


def test_polygons_from_gdf_validates_schema() -> None:
    gdf = gpd.GeoDataFrame(
        {
            "name": ["Zone A"],
            "population": [120],
            "polygons": [_square(-10, -5, 10, 5)],
            "altitude": [0.05],
            "cap_color": ["#ffcc00"],
        },
        geometry="polygons",
        crs="EPSG:4326",
    )

    polygons = polygons_from_gdf(
        gdf, include_columns=["name", "population", "altitude", "cap_color"]
    )
    assert len(polygons) == 1
    polygon = polygons[0]
    assert isinstance(polygon, PolygonDatum)
    assert polygon.name == "Zone A"
    assert polygon.model_dump(exclude={"id", "geometry"})["population"] == 120
    assert polygon.altitude == 0.05
    assert isinstance(polygon.cap_color, Color)
    assert polygon.cap_color.as_hex(format="long") == "#ffcc00"
    assert isinstance(polygon.geometry, GeoJsonPolygon)


def test_polygons_from_gdf_reprojects_geometry() -> None:
    polygon = _square(-10, -5, 10, 5)
    gdf = gpd.GeoDataFrame(
        {"name": ["Zone A"], "polygons": [polygon]},
        geometry="polygons",
        crs="EPSG:4326",
    ).to_crs(3857)

    polygons = polygons_from_gdf(gdf, include_columns=["name"])
    polygon = polygons[0]
    assert isinstance(polygon, PolygonDatum)
    geometry = polygon.geometry
    assert isinstance(geometry, GeoJsonPolygon)
    coords = geometry.coordinates[0][0]
    assert coords[0] == pytest.approx(-10, abs=1e-6)
    assert coords[1] == pytest.approx(-5, abs=1e-6)


def test_polygons_from_gdf_requires_crs() -> None:
    gdf = gpd.GeoDataFrame(
        {"name": ["Zone A"], "polygons": [_square(-10, -5, 10, 5)]}, geometry="polygons"
    )

    with pytest.raises(ValueError, match="CRS"):
        polygons_from_gdf(gdf)


def test_polygons_from_gdf_rejects_non_polygon_geometry() -> None:
    gdf = gpd.GeoDataFrame(
        {"name": ["Zone A"], "polygons": [Point(0, 0)]},
        geometry="polygons",
        crs="EPSG:4326",
    )

    with pytest.raises(ValueError, match="Polygon"):
        polygons_from_gdf(gdf)


def test_polygons_from_gdf_missing_columns() -> None:
    gdf = gpd.GeoDataFrame(
        {"name": ["Zone A"], "polygons": [_square(-10, -5, 10, 5)]},
        geometry="polygons",
        crs="EPSG:4326",
    )

    with pytest.raises(ValueError, match="missing columns"):
        polygons_from_gdf(gdf, include_columns=["missing"])


def test_polygons_from_gdf_invalid_optional_column_types() -> None:
    gdf = gpd.GeoDataFrame(
        {
            "name": ["Zone A"],
            "polygons": [_square(-10, -5, 10, 5)],
            "altitude": [-1],
            "cap_curvature_resolution": [0],
            "cap_color": ["not-a-color"],
        },
        geometry="polygons",
        crs="EPSG:4326",
    )

    with pytest.raises(ValueError, match="polygons_from_gdf"):
        polygons_from_gdf(gdf)


def test_polygons_from_gdf_accepts_multipolygon() -> None:
    polygon = _square(-10, -5, 10, 5)
    multipolygon = MultiPolygon([polygon, _square(15, -5, 25, 5)])
    gdf = gpd.GeoDataFrame(
        {"name": ["Zone A"], "polygons": [multipolygon]},
        geometry="polygons",
        crs="EPSG:4326",
    )

    polygons = polygons_from_gdf(gdf, include_columns=["name"])
    assert isinstance(polygons[0], PolygonDatum)
    assert isinstance(polygons[0].geometry, GeoJsonMultiPolygon)
