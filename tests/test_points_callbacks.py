from __future__ import annotations

from threading import Event
from typing import Any, TYPE_CHECKING

from IPython.display import display
import pytest

from pyglobegl import (
    GlobeConfig,
    GlobeInitConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeViewConfig,
    GlobeWidget,
    PointDatum,
    PointOfView,
    PointsLayerConfig,
)


if TYPE_CHECKING:
    from playwright.sync_api import Page


@pytest.mark.usefixtures("solara_test")
def test_on_point_click_callback(
    page_session: Page, globe_clicker, globe_earth_texture_url
) -> None:
    click_event = Event()
    payload: dict[str, Any] = {}

    def _on_click(point: dict[str, Any], coords: dict[str, float]) -> None:
        payload["point"] = point
        payload["coords"] = coords
        click_event.set()

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
        points=PointsLayerConfig(
            points_data=[
                PointDatum(
                    lat=0,
                    lng=0,
                    label="Center",
                    altitude=0.2,
                    radius=1.2,
                    color="#ffff00",
                )
            ]
        ),
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.6), transition_ms=0
        ),
    )
    widget = GlobeWidget(config=config)
    widget.on_point_click(_on_click)
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

    assert click_event.wait(5), "Expected point click callback to fire."
    assert isinstance(payload.get("point"), dict)
    assert isinstance(payload.get("coords"), dict)


@pytest.mark.usefixtures("solara_test")
def test_on_point_right_click_callback(
    page_session: Page, globe_clicker, globe_earth_texture_url
) -> None:
    click_event = Event()
    payload: dict[str, Any] = {}

    def _on_click(point: dict[str, Any], coords: dict[str, float]) -> None:
        payload["point"] = point
        payload["coords"] = coords
        click_event.set()

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
        points=PointsLayerConfig(
            points_data=[
                PointDatum(
                    lat=0,
                    lng=0,
                    label="Center",
                    altitude=0.2,
                    radius=1.2,
                    color="#00ffff",
                )
            ]
        ),
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.6), transition_ms=0
        ),
    )
    widget = GlobeWidget(config=config)
    widget.on_point_right_click(_on_click)
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

    assert click_event.wait(5), "Expected point right-click callback to fire."
    assert isinstance(payload.get("point"), dict)
    assert isinstance(payload.get("coords"), dict)


@pytest.mark.usefixtures("solara_test")
def test_on_point_hover_callback(
    page_session: Page, globe_hoverer, globe_earth_texture_url
) -> None:
    hover_event = Event()
    payload: dict[str, Any] = {}

    def _on_hover(point: dict[str, Any] | None, prev: dict[str, Any] | None) -> None:
        payload["point"] = point
        payload["prev"] = prev
        hover_event.set()

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
        points=PointsLayerConfig(
            points_data=[
                PointDatum(
                    lat=0,
                    lng=0,
                    label="Center",
                    altitude=0.2,
                    radius=1.2,
                    color="#ff00ff",
                )
            ]
        ),
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.6), transition_ms=0
        ),
    )
    widget = GlobeWidget(config=config)
    widget.on_point_hover(_on_hover)
    display(widget)

    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )
    globe_hoverer(page_session)

    assert hover_event.wait(5), "Expected point hover callback to fire."
    assert payload.get("point") is None or isinstance(payload.get("point"), dict)


@pytest.mark.usefixtures("solara_test")
def test_points_merge_disables_click(
    page_session: Page, globe_clicker, globe_earth_texture_url
) -> None:
    click_event = Event()

    def _on_click(_: dict[str, Any], __: dict[str, float]) -> None:
        click_event.set()

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
        points=PointsLayerConfig(
            points_data=[
                PointDatum(
                    lat=0,
                    lng=0,
                    label="Center",
                    altitude=0.2,
                    radius=1.2,
                    color="#ffffff",
                )
            ],
            points_merge=True,
        ),
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.6), transition_ms=0
        ),
    )
    widget = GlobeWidget(config=config)
    widget.on_point_click(_on_click)
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

    assert not click_event.wait(1.5), "Point click should not fire when merged."
