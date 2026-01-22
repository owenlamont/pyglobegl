from __future__ import annotations

from threading import Event
from typing import Any, TYPE_CHECKING

from IPython.display import display
import pytest

from pyglobegl import (
    ArcsLayerConfig,
    GlobeConfig,
    GlobeInitConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeViewConfig,
    GlobeWidget,
    PointOfView,
)


if TYPE_CHECKING:
    from playwright.sync_api import Page


@pytest.mark.usefixtures("solara_test")
def test_on_arc_click_callback(
    page_session: Page, globe_clicker, globe_earth_texture_url
) -> None:
    click_event = Event()
    payload: dict[str, Any] = {}

    def _on_click(arc: dict[str, Any], coords: dict[str, float]) -> None:
        payload["arc"] = arc
        payload["coords"] = coords
        click_event.set()

    arcs_data = [
        {"startLat": 0, "startLng": -20, "endLat": 0, "endLng": 20, "color": "#ffcc00"}
    ]

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
        arcs=ArcsLayerConfig(
            arcs_data=arcs_data,
            arc_start_lat="startLat",
            arc_start_lng="startLng",
            arc_end_lat="endLat",
            arc_end_lng="endLng",
            arc_color="color",
            arc_altitude=0.2,
            arc_stroke=1.2,
            arcs_transition_duration=0,
        ),
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.7), transition_ms=0
        ),
    )
    widget = GlobeWidget(config=config)
    widget.on_arc_click(_on_click)
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

    assert click_event.wait(5), "Expected arc click callback to fire."
    assert isinstance(payload.get("arc"), dict)
    assert isinstance(payload.get("coords"), dict)


@pytest.mark.usefixtures("solara_test")
def test_on_arc_right_click_callback(
    page_session: Page, globe_clicker, globe_earth_texture_url
) -> None:
    click_event = Event()
    payload: dict[str, Any] = {}

    def _on_click(arc: dict[str, Any], coords: dict[str, float]) -> None:
        payload["arc"] = arc
        payload["coords"] = coords
        click_event.set()

    arcs_data = [
        {"startLat": 0, "startLng": -20, "endLat": 0, "endLng": 20, "color": "#00ffcc"}
    ]

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
        arcs=ArcsLayerConfig(
            arcs_data=arcs_data,
            arc_start_lat="startLat",
            arc_start_lng="startLng",
            arc_end_lat="endLat",
            arc_end_lng="endLng",
            arc_color="color",
            arc_altitude=0.2,
            arc_stroke=1.2,
            arcs_transition_duration=0,
        ),
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.7), transition_ms=0
        ),
    )
    widget = GlobeWidget(config=config)
    widget.on_arc_right_click(_on_click)
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

    assert click_event.wait(5), "Expected arc right-click callback to fire."
    assert isinstance(payload.get("arc"), dict)
    assert isinstance(payload.get("coords"), dict)


@pytest.mark.usefixtures("solara_test")
def test_on_arc_hover_callback(
    page_session: Page, globe_hoverer, globe_earth_texture_url
) -> None:
    hover_event = Event()
    payload: dict[str, Any] = {}

    def _on_hover(arc: dict[str, Any] | None, prev: dict[str, Any] | None) -> None:
        payload["arc"] = arc
        payload["prev"] = prev
        hover_event.set()

    arcs_data = [
        {"startLat": 0, "startLng": -20, "endLat": 0, "endLng": 20, "color": "#ff00cc"}
    ]

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
        arcs=ArcsLayerConfig(
            arcs_data=arcs_data,
            arc_start_lat="startLat",
            arc_start_lng="startLng",
            arc_end_lat="endLat",
            arc_end_lng="endLng",
            arc_color="color",
            arc_altitude=0.2,
            arc_stroke=1.2,
            arcs_transition_duration=0,
        ),
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.7), transition_ms=0
        ),
    )
    widget = GlobeWidget(config=config)
    widget.on_arc_hover(_on_hover)
    display(widget)

    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )
    globe_hoverer(page_session)

    assert hover_event.wait(5), "Expected arc hover callback to fire."
    assert payload.get("arc") is None or isinstance(payload.get("arc"), dict)
