from __future__ import annotations

from typing import TYPE_CHECKING

from geojson_pydantic import Polygon
from geojson_pydantic.types import Position2D
from IPython.display import display
from pydantic import AnyUrl, TypeAdapter
import pytest

from pyglobegl import (
    GlobeConfig,
    GlobeInitConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeViewConfig,
    GlobeWidget,
    HexedPolygonsLayerConfig,
    HexPolygonDatum,
    PointOfView,
)


if TYPE_CHECKING:
    from playwright.sync_api import Page

_URL_ADAPTER = TypeAdapter(AnyUrl)


def _make_polygon() -> Polygon:
    ring = [
        Position2D(-10.0, -10.0),
        Position2D(-10.0, 10.0),
        Position2D(10.0, 10.0),
        Position2D(10.0, -10.0),
        Position2D(-10.0, -10.0),
    ]
    return Polygon(type="Polygon", coordinates=[ring])


def _make_config(
    hexed: HexedPolygonsLayerConfig, globe_texture_url: str
) -> GlobeConfig:
    return GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#000000"),
        globe=GlobeLayerConfig(
            globe_image_url=_URL_ADAPTER.validate_python(globe_texture_url),
            show_atmosphere=False,
            show_graticules=False,
        ),
        hexed_polygons=hexed,
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.6), transition_ms=0
        ),
    )


def _await_globe_ready(page_session: Page) -> None:
    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )
    page_session.wait_for_timeout(250)


@pytest.mark.usefixtures("solara_test")
def test_hexed_polygons_accessors(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.97
    polygon = _make_polygon()
    hexed = [
        HexPolygonDatum(
            geometry=polygon,
            color="#ffcc00",
            altitude=0.02,
            resolution=2,
            margin=0.2,
            use_dots=False,
            curvature_resolution=6,
            dot_resolution=8,
        )
    ]
    updated = [
        HexPolygonDatum(
            geometry=polygon,
            color="#00ccff",
            altitude=0.05,
            resolution=4,
            margin=0.05,
            use_dots=True,
            curvature_resolution=3,
            dot_resolution=16,
        )
    ]

    config = _make_config(
        HexedPolygonsLayerConfig(
            hex_polygons_data=hexed, hex_polygons_transition_duration=0
        ),
        globe_flat_texture_data_url,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(page_session, "initial", canvas_similarity_threshold)

    widget.set_hex_polygons_data(updated)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "updated", canvas_similarity_threshold)
