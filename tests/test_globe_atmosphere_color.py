from __future__ import annotations

from typing import TYPE_CHECKING

from IPython.display import display
import pytest

from pyglobegl import (
    GlobeConfig,
    GlobeInitConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeWidget,
)


if TYPE_CHECKING:
    from playwright.sync_api import Page


@pytest.mark.usefixtures("solara_test")
def test_globe_atmosphere_color(
    page_session: Page, canvas_assert_capture, globe_earth_texture_url
) -> None:
    canvas_similarity_threshold = 0.99
    initial_color = "#00ffff"
    updated_color = "#ff00ff"
    config = GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#000000"),
        globe=GlobeLayerConfig(
            globe_image_url=globe_earth_texture_url,
            show_atmosphere=True,
            atmosphere_color=initial_color,
            atmosphere_altitude=0.15,
            show_graticules=False,
        ),
    )
    widget = GlobeWidget(config=config)
    display(widget)

    page_session.wait_for_function(
        "document.querySelector('canvas, .jupyter-widgets') !== null", timeout=20000
    )
    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )

    canvas_assert_capture(page_session, "cyan", canvas_similarity_threshold)
    widget.set_atmosphere_color(updated_color)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "magenta", canvas_similarity_threshold)
