from __future__ import annotations

from threading import Event
from typing import Any, TYPE_CHECKING

from geojson_pydantic import Polygon
from geojson_pydantic.types import Position2D, Position3D
from IPython.display import display
import pytest

from pyglobegl import (
    GlobeConfig,
    GlobeInitConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeViewConfig,
    GlobeWidget,
    PointOfView,
    PolygonDatum,
    PolygonsLayerConfig,
)


if TYPE_CHECKING:
    from playwright.sync_api import Page


def _polygon() -> Polygon:
    coordinates: list[list[Position2D | Position3D]] = [
        [
            Position2D(-60.0, -20.0),
            Position2D(-60.0, 20.0),
            Position2D(60.0, 20.0),
            Position2D(60.0, -20.0),
            Position2D(-60.0, -20.0),
        ]
    ]
    return Polygon(type="Polygon", coordinates=coordinates)


@pytest.mark.usefixtures("solara_test")
def test_on_polygon_click_callback(
    page_session: Page, globe_clicker, globe_earth_texture_url
) -> None:
    click_event = Event()
    payload: dict[str, Any] = {}

    def _on_click(polygon: dict[str, Any], coords: dict[str, float]) -> None:
        payload["polygon"] = polygon
        payload["coords"] = coords
        click_event.set()

    polygon = _polygon()

    config = GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#000000"),
        globe=GlobeLayerConfig(
            globe_image_url=globe_earth_texture_url,
            show_atmosphere=False,
            show_graticules=False,
        ),
        polygons=PolygonsLayerConfig(
            polygons_data=[
                PolygonDatum(
                    geometry=polygon,
                    cap_color="#ffcc00",
                    stroke_color="#ffffff",
                    altitude=0.05,
                )
            ]
        ),
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.6), transition_ms=0
        ),
    )
    widget = GlobeWidget(config=config)
    widget.on_polygon_click(_on_click)
    display(widget)

    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )
    page_session.wait_for_function(
        """
        () => {
          const canvas = document.querySelector("canvas");
          if (!canvas) {
            return false;
          }
          const dataUrl = canvas.toDataURL("image/png");
          return dataUrl.length > 2000;
        }
        """,
        timeout=20000,
    )
    globe_clicker(page_session, "left")

    assert click_event.wait(5), "Expected polygon click callback to fire."
    assert isinstance(payload.get("polygon"), dict)
    assert isinstance(payload.get("coords"), dict)


@pytest.mark.usefixtures("solara_test")
def test_on_polygon_right_click_callback(
    page_session: Page, globe_clicker, globe_earth_texture_url
) -> None:
    click_event = Event()
    payload: dict[str, Any] = {}

    def _on_click(polygon: dict[str, Any], coords: dict[str, float]) -> None:
        payload["polygon"] = polygon
        payload["coords"] = coords
        click_event.set()

    polygon = _polygon()

    config = GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#000000"),
        globe=GlobeLayerConfig(
            globe_image_url=globe_earth_texture_url,
            show_atmosphere=False,
            show_graticules=False,
        ),
        polygons=PolygonsLayerConfig(
            polygons_data=[
                PolygonDatum(
                    geometry=polygon,
                    cap_color="#00ffcc",
                    stroke_color="#ffffff",
                    altitude=0.05,
                )
            ]
        ),
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.6), transition_ms=0
        ),
    )
    widget = GlobeWidget(config=config)
    widget.on_polygon_right_click(_on_click)
    display(widget)

    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )
    page_session.wait_for_function(
        """
        () => {
          const canvas = document.querySelector("canvas");
          if (!canvas) {
            return false;
          }
          const dataUrl = canvas.toDataURL("image/png");
          return dataUrl.length > 2000;
        }
        """,
        timeout=20000,
    )
    globe_clicker(page_session, "right")

    assert click_event.wait(5), "Expected polygon right-click callback to fire."
    assert isinstance(payload.get("polygon"), dict)
    assert isinstance(payload.get("coords"), dict)


@pytest.mark.usefixtures("solara_test")
def test_on_polygon_hover_callback(
    page_session: Page, globe_hoverer, globe_earth_texture_url
) -> None:
    hover_event = Event()
    payload: dict[str, Any] = {}

    def _on_hover(polygon: dict[str, Any] | None, prev: dict[str, Any] | None) -> None:
        payload["polygon"] = polygon
        payload["prev"] = prev
        hover_event.set()

    polygon = _polygon()

    config = GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#000000"),
        globe=GlobeLayerConfig(
            globe_image_url=globe_earth_texture_url,
            show_atmosphere=False,
            show_graticules=False,
        ),
        polygons=PolygonsLayerConfig(
            polygons_data=[
                PolygonDatum(
                    geometry=polygon,
                    cap_color="#ff00ff",
                    stroke_color="#ffffff",
                    altitude=0.05,
                )
            ]
        ),
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.6), transition_ms=0
        ),
    )
    widget = GlobeWidget(config=config)
    widget.on_polygon_hover(_on_hover)
    display(widget)

    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )
    globe_hoverer(page_session)

    assert hover_event.wait(5), "Expected polygon hover callback to fire."
    assert payload.get("polygon") is None or isinstance(payload.get("polygon"), dict)
