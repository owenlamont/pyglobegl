from __future__ import annotations

from typing import TYPE_CHECKING

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
)


if TYPE_CHECKING:
    from playwright.sync_api import Page


@pytest.mark.usefixtures("solara_test")
def test_globe_layer_graticules(page_session: Page, canvas_assert_capture) -> None:
    canvas_similarity_threshold = 0.97
    initial_show_graticules = False
    updated_show_graticules = True
    config = GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#00ff00"),
        view=GlobeViewConfig(point_of_view=PointOfView(lat=0, lng=0, altitude=1.4)),
        globe=GlobeLayerConfig(show_graticules=initial_show_graticules),
    )
    widget = GlobeWidget(config=config)
    display(widget)

    page_session.wait_for_function(
        "document.querySelector('canvas, .jupyter-widgets') !== null", timeout=20000
    )
    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )
    page_session.wait_for_function(
        (
            "window.__pyglobegl_pov && "
            "Math.abs(window.__pyglobegl_pov.altitude - 1.4) < 0.001"
        ),
        timeout=20000,
    )

    canvas_assert_capture(page_session, "graticules-off", canvas_similarity_threshold)
    widget.set_show_graticules(updated_show_graticules)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "graticules-on", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_globe_layer_show_globe(
    page_session: Page, canvas_assert_capture, globe_earth_texture_url
) -> None:
    canvas_similarity_threshold = 0.99
    config = GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#000000"),
        globe=GlobeLayerConfig(
            globe_image_url=globe_earth_texture_url,
            show_globe=True,
            show_graticules=False,
            show_atmosphere=False,
        ),
        view=GlobeViewConfig(point_of_view=PointOfView(lat=0, lng=0, altitude=1.4)),
    )
    widget = GlobeWidget(config=config)
    display(widget)

    page_session.wait_for_function(
        "document.querySelector('canvas, .jupyter-widgets') !== null", timeout=20000
    )
    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )

    canvas_assert_capture(page_session, "on", canvas_similarity_threshold)
    widget.set_show_globe(False)
    page_session.wait_for_timeout(200)
    canvas_assert_capture(page_session, "off", canvas_similarity_threshold)
