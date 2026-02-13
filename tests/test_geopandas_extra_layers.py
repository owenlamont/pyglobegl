from __future__ import annotations

import pytest

from pyglobegl import (
    HeatmapDatum,
    heatmaps_from_gdf,
    hexed_polygons_from_gdf,
    HexPolygonDatum,
    LabelDatum,
    labels_from_gdf,
    ParticleDatum,
    particles_from_gdf,
    RingDatum,
    rings_from_gdf,
    TileDatum,
    tiles_from_gdf,
)


def test_heatmaps_from_gdf_builds_single_heatmap() -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    gdf = geopandas.GeoDataFrame(
        {"weight": [1.5, 2.0], "point": [Point(10, 5), Point(-20, 40)]},
        geometry="point",
        crs="EPSG:4326",
    )

    heatmaps = heatmaps_from_gdf(gdf, weight_column="weight")
    assert len(heatmaps) == 1
    heatmap = heatmaps[0]
    assert isinstance(heatmap, HeatmapDatum)
    assert len(heatmap.points) == 2
    assert heatmap.points[0].lat == pytest.approx(5.0)
    assert heatmap.points[0].lng == pytest.approx(10.0)
    assert heatmap.points[0].weight == pytest.approx(1.5)


def test_hexed_polygons_from_gdf_builds_polygons() -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Polygon

    geom = Polygon([(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)])
    gdf = geopandas.GeoDataFrame(
        {"geometry": [geom], "label": ["A"]}, geometry="geometry", crs="EPSG:4326"
    )

    polygons = hexed_polygons_from_gdf(gdf, include_columns=["label"])
    assert len(polygons) == 1
    assert isinstance(polygons[0], HexPolygonDatum)
    assert polygons[0].label == "A"


def test_tiles_from_gdf_builds_tiles() -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    gdf = geopandas.GeoDataFrame(
        {"width": [10], "height": [20], "point": [Point(10, 5)]},
        geometry="point",
        crs="EPSG:4326",
    )

    tiles = tiles_from_gdf(gdf, include_columns=["width", "height"])
    assert len(tiles) == 1
    assert isinstance(tiles[0], TileDatum)
    assert tiles[0].width == 10
    assert tiles[0].height == 20


def test_particles_from_gdf_builds_particle_group() -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    gdf = geopandas.GeoDataFrame(
        {"point": [Point(10, 5), Point(-20, 40)]}, geometry="point", crs="EPSG:4326"
    )

    particles = particles_from_gdf(gdf)
    assert len(particles) == 1
    assert isinstance(particles[0], ParticleDatum)
    assert len(particles[0].particles) == 2


def test_rings_from_gdf_builds_rings() -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    gdf = geopandas.GeoDataFrame(
        {"point": [Point(10, 5)]}, geometry="point", crs="EPSG:4326"
    )

    rings = rings_from_gdf(gdf)
    assert len(rings) == 1
    assert isinstance(rings[0], RingDatum)
    assert rings[0].lat == pytest.approx(5.0)
    assert rings[0].lng == pytest.approx(10.0)


def test_labels_from_gdf_builds_labels() -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    gdf = geopandas.GeoDataFrame(
        {"name": ["A"], "point": [Point(10, 5)]}, geometry="point", crs="EPSG:4326"
    )

    labels = labels_from_gdf(gdf, text_column="name")
    assert len(labels) == 1
    assert isinstance(labels[0], LabelDatum)
    assert labels[0].text == "A"


def test_labels_from_gdf_requires_text_column() -> None:
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import Point

    gdf = geopandas.GeoDataFrame(
        {"point": [Point(10, 5)]}, geometry="point", crs="EPSG:4326"
    )

    with pytest.raises(ValueError, match="missing columns"):
        labels_from_gdf(gdf, text_column="name")
