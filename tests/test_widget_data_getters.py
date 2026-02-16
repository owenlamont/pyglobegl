from __future__ import annotations

from uuid import UUID

from geojson_pydantic import Polygon
from geojson_pydantic.types import Position2D

from pyglobegl import (
    ArcDatum,
    ArcsLayerConfig,
    frontend_python,
    GlobeConfig,
    GlobeInitConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeWidget,
    HeatmapDatum,
    HeatmapsLayerConfig,
    HexBinLayerConfig,
    HexBinPointDatum,
    HexedPolygonsLayerConfig,
    HexPolygonDatum,
    LabelDatum,
    LabelsLayerConfig,
    ParticleDatum,
    ParticlesLayerConfig,
    PointDatum,
    PointsLayerConfig,
    PolygonDatum,
    PolygonsLayerConfig,
    RingDatum,
    RingsLayerConfig,
    TileDatum,
    TilesLayerConfig,
)


def _make_widget(
    *,
    points_data=None,
    arcs_data=None,
    polygons_data=None,
    heatmaps_data=None,
    hexbin_points_data=None,
    hex_polygons_data=None,
    tiles_data=None,
    particles_data=None,
    rings_data=None,
    labels_data=None,
) -> GlobeWidget:
    return GlobeWidget(
        config=GlobeConfig(
            init=GlobeInitConfig(animate_in=False),
            layout=GlobeLayoutConfig(width=128, height=128),
            globe=GlobeLayerConfig(show_globe=False),
            points=PointsLayerConfig(points_data=points_data),
            arcs=ArcsLayerConfig(arcs_data=arcs_data),
            polygons=PolygonsLayerConfig(polygons_data=polygons_data),
            heatmaps=HeatmapsLayerConfig(heatmaps_data=heatmaps_data),
            hex_bin=HexBinLayerConfig(hex_bin_points_data=hexbin_points_data),
            hexed_polygons=HexedPolygonsLayerConfig(
                hex_polygons_data=hex_polygons_data
            ),
            tiles=TilesLayerConfig(tiles_data=tiles_data),
            particles=ParticlesLayerConfig(particles_data=particles_data),
            rings=RingsLayerConfig(rings_data=rings_data),
            labels=LabelsLayerConfig(labels_data=labels_data),
        )
    )


def test_get_points_data_returns_copy() -> None:
    points_data = [
        PointDatum.model_validate(
            {"lat": 10, "lng": 20, "color": "#ff00cc", "meta": {"name": "Point"}}
        )
    ]
    widget = _make_widget(points_data=points_data)

    snapshot = widget.get_points_data()
    assert snapshot is not None
    assert isinstance(snapshot[0].id, UUID)
    assert snapshot[0].model_extra is not None
    snapshot[0].model_extra["meta"]["name"] = "Changed"

    refreshed = widget.get_points_data()
    assert refreshed is not None
    assert refreshed[0].model_extra is not None
    assert refreshed[0].model_extra["meta"]["name"] == "Point"


def test_get_arcs_data_returns_copy() -> None:
    arcs_data = [
        ArcDatum.model_validate(
            {
                "start_lat": 0,
                "start_lng": -10,
                "end_lat": 5,
                "end_lng": 10,
                "meta": {"name": "Arc"},
            }
        )
    ]
    widget = _make_widget(arcs_data=arcs_data)

    snapshot = widget.get_arcs_data()
    assert snapshot is not None
    assert isinstance(snapshot[0].id, UUID)
    assert snapshot[0].model_extra is not None
    snapshot[0].model_extra["meta"]["name"] = "Changed"

    refreshed = widget.get_arcs_data()
    assert refreshed is not None
    assert refreshed[0].model_extra is not None
    assert refreshed[0].model_extra["meta"]["name"] == "Arc"


def test_get_polygons_data_returns_copy() -> None:
    ring = [
        Position2D(0.0, 0.0),
        Position2D(0.0, 2.0),
        Position2D(2.0, 2.0),
        Position2D(2.0, 0.0),
        Position2D(0.0, 0.0),
    ]
    polygon = Polygon(type="Polygon", coordinates=[ring])
    polygons_data = [
        PolygonDatum.model_validate({"geometry": polygon, "meta": {"name": "Polygon"}})
    ]
    widget = _make_widget(polygons_data=polygons_data)

    snapshot = widget.get_polygons_data()
    assert snapshot is not None
    assert isinstance(snapshot[0].id, UUID)
    assert snapshot[0].model_extra is not None
    snapshot[0].model_extra["meta"]["name"] = "Changed"

    refreshed = widget.get_polygons_data()
    assert refreshed is not None
    assert refreshed[0].model_extra is not None
    assert refreshed[0].model_extra["meta"]["name"] == "Polygon"


def test_get_heatmaps_data_returns_copy() -> None:
    heatmaps_data = [
        HeatmapDatum.model_validate(
            {
                "points": [{"lat": 10, "lng": 20, "weight": 1.0}],
                "meta": {"name": "Heatmap"},
            }
        )
    ]
    widget = _make_widget(heatmaps_data=heatmaps_data)

    snapshot = widget.get_heatmaps_data()
    assert snapshot is not None
    assert isinstance(snapshot[0].id, UUID)
    assert snapshot[0].model_extra is not None
    snapshot[0].model_extra["meta"]["name"] = "Changed"

    refreshed = widget.get_heatmaps_data()
    assert refreshed is not None
    assert refreshed[0].model_extra is not None
    assert refreshed[0].model_extra["meta"]["name"] == "Heatmap"


def test_get_hexbin_points_data_returns_copy() -> None:
    points = [
        HexBinPointDatum.model_validate(
            {"lat": 10, "lng": 20, "weight": 2.5, "meta": {"name": "HexPoint"}}
        )
    ]
    widget = _make_widget(hexbin_points_data=points)

    snapshot = widget.get_hex_bin_points_data()
    assert snapshot is not None
    assert isinstance(snapshot[0].id, UUID)
    assert snapshot[0].model_extra is not None
    snapshot[0].model_extra["meta"]["name"] = "Changed"

    refreshed = widget.get_hex_bin_points_data()
    assert refreshed is not None
    assert refreshed[0].model_extra is not None
    assert refreshed[0].model_extra["meta"]["name"] == "HexPoint"


def test_get_hex_polygons_data_returns_copy() -> None:
    ring = [
        Position2D(0.0, 0.0),
        Position2D(0.0, 2.0),
        Position2D(2.0, 2.0),
        Position2D(2.0, 0.0),
        Position2D(0.0, 0.0),
    ]
    polygon = Polygon(type="Polygon", coordinates=[ring])
    hex_polygons = [
        HexPolygonDatum.model_validate(
            {"geometry": polygon, "meta": {"name": "HexPolygon"}}
        )
    ]
    widget = _make_widget(hex_polygons_data=hex_polygons)

    snapshot = widget.get_hex_polygons_data()
    assert snapshot is not None
    assert isinstance(snapshot[0].id, UUID)
    assert snapshot[0].model_extra is not None
    snapshot[0].model_extra["meta"]["name"] = "Changed"

    refreshed = widget.get_hex_polygons_data()
    assert refreshed is not None
    assert refreshed[0].model_extra is not None
    assert refreshed[0].model_extra["meta"]["name"] == "HexPolygon"


def test_get_tiles_data_returns_copy() -> None:
    tiles = [
        TileDatum.model_validate(
            {"lat": 0, "lng": 0, "width": 5, "height": 5, "meta": {"name": "Tile"}}
        )
    ]
    widget = _make_widget(tiles_data=tiles)

    snapshot = widget.get_tiles_data()
    assert snapshot is not None
    assert isinstance(snapshot[0].id, UUID)
    assert snapshot[0].model_extra is not None
    snapshot[0].model_extra["meta"]["name"] = "Changed"

    refreshed = widget.get_tiles_data()
    assert refreshed is not None
    assert refreshed[0].model_extra is not None
    assert refreshed[0].model_extra["meta"]["name"] == "Tile"


def test_get_particles_data_returns_copy() -> None:
    particles = [
        ParticleDatum.model_validate(
            {
                "particles": [{"lat": 0, "lng": 0, "altitude": 0.01}],
                "meta": {"name": "Particles"},
            }
        )
    ]
    widget = _make_widget(particles_data=particles)

    snapshot = widget.get_particles_data()
    assert snapshot is not None
    assert isinstance(snapshot[0].id, UUID)
    assert snapshot[0].model_extra is not None
    snapshot[0].model_extra["meta"]["name"] = "Changed"

    refreshed = widget.get_particles_data()
    assert refreshed is not None
    assert refreshed[0].model_extra is not None
    assert refreshed[0].model_extra["meta"]["name"] == "Particles"


def test_get_rings_data_returns_copy() -> None:
    rings = [RingDatum.model_validate({"lat": 0, "lng": 0, "meta": {"name": "Ring"}})]
    widget = _make_widget(rings_data=rings)

    snapshot = widget.get_rings_data()
    assert snapshot is not None
    assert isinstance(snapshot[0].id, UUID)
    assert snapshot[0].model_extra is not None
    snapshot[0].model_extra["meta"]["name"] = "Changed"

    refreshed = widget.get_rings_data()
    assert refreshed is not None
    assert refreshed[0].model_extra is not None
    assert refreshed[0].model_extra["meta"]["name"] == "Ring"


def test_get_labels_data_returns_copy() -> None:
    labels = [
        LabelDatum.model_validate(
            {"lat": 0, "lng": 0, "text": "Label", "meta": {"name": "Label"}}
        )
    ]
    widget = _make_widget(labels_data=labels)

    snapshot = widget.get_labels_data()
    assert snapshot is not None
    assert isinstance(snapshot[0].id, UUID)
    assert snapshot[0].model_extra is not None
    snapshot[0].model_extra["meta"]["name"] = "Changed"

    refreshed = widget.get_labels_data()
    assert refreshed is not None
    assert refreshed[0].model_extra is not None
    assert refreshed[0].model_extra["meta"]["name"] == "Label"


@frontend_python
def _hexbin_lat_accessor(point):
    return float(point["lat"])


@frontend_python
def _hexbin_lng_accessor(point):
    return float(point["lng"])


@frontend_python
def _hexbin_weight_accessor(point):
    return float(point["weight"]) * 2.0


@frontend_python
def _hexbin_margin_accessor(hexbin):
    return 0.12 if float(hexbin["sumWeight"]) > 1 else 0.02


def test_hexbin_accessor_getters_setters_support_frontend_python() -> None:
    widget = _make_widget(
        hexbin_points_data=[HexBinPointDatum(lat=1.0, lng=2.0, weight=3.0)]
    )
    widget.set_hex_bin_point_lat(_hexbin_lat_accessor)
    widget.set_hex_bin_point_lng(_hexbin_lng_accessor)
    widget.set_hex_bin_point_weight(_hexbin_weight_accessor)
    widget.set_hex_margin(_hexbin_margin_accessor)

    assert widget.get_hex_bin_point_lat() is not None
    assert widget.get_hex_bin_point_lng() is not None
    assert widget.get_hex_bin_point_weight() is not None
    assert widget.get_hex_margin() is not None
