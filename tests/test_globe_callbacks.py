from __future__ import annotations

from threading import Event
from typing import TYPE_CHECKING

from IPython.display import display
from pydantic import AnyUrl
import pytest

from pyglobegl import (
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
def test_on_globe_ready_callback(page_session: Page) -> None:
    ready_event = Event()

    config = GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#00ff00"),
    )
    widget = GlobeWidget(config=config)
    widget.on_globe_ready(lambda: ready_event.set())
    display(widget)

    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )
    assert ready_event.wait(5), "Expected globe ready callback to fire."


@pytest.mark.usefixtures("solara_test")
def test_on_globe_click_callback(
    page_session: Page, globe_clicker, globe_earth_texture_url: AnyUrl
) -> None:
    click_event = Event()
    payload: dict[str, float] = {}

    def _on_click(coords: dict[str, float]) -> None:
        payload.update(coords)
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
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.4), transition_ms=0
        ),
    )
    widget = GlobeWidget(config=config)
    widget.on_globe_click(_on_click)
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

    assert click_event.wait(5), "Expected globe click callback to fire."
    assert "lat" in payload
    assert "lng" in payload
    assert -90 <= payload["lat"] <= 90
    assert -180 <= payload["lng"] <= 180


@pytest.mark.usefixtures("solara_test")
def test_on_globe_right_click_callback(
    page_session: Page, globe_clicker, globe_earth_texture_url: AnyUrl
) -> None:
    click_event = Event()
    payload: dict[str, float] = {}

    def _on_click(coords: dict[str, float]) -> None:
        payload.update(coords)
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
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.4), transition_ms=0
        ),
    )
    widget = GlobeWidget(config=config)
    widget.on_globe_right_click(_on_click)
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

    assert click_event.wait(5), "Expected globe right-click callback to fire."
    assert "lat" in payload
    assert "lng" in payload
    assert -90 <= payload["lat"] <= 90
    assert -180 <= payload["lng"] <= 180
