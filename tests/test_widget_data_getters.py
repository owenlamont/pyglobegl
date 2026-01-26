from __future__ import annotations

from uuid import UUID

from geojson_pydantic import Polygon
from geojson_pydantic.types import Position2D

from pyglobegl import (
    ArcDatum,
    ArcsLayerConfig,
    GlobeConfig,
    GlobeInitConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeWidget,
    PointDatum,
    PointsLayerConfig,
    PolygonDatum,
    PolygonsLayerConfig,
)


def _make_widget(
    *, points_data=None, arcs_data=None, polygons_data=None
) -> GlobeWidget:
    return GlobeWidget(
        config=GlobeConfig(
            init=GlobeInitConfig(animate_in=False),
            layout=GlobeLayoutConfig(width=128, height=128),
            globe=GlobeLayerConfig(show_globe=False),
            points=PointsLayerConfig(points_data=points_data),
            arcs=ArcsLayerConfig(arcs_data=arcs_data),
            polygons=PolygonsLayerConfig(polygons_data=polygons_data),
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
