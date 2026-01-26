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
def test_bump_image_url(
    page_session: Page,
    canvas_assert_capture,
    globe_bump_test_data_url,
    globe_flat_texture_data_url,
) -> None:
    canvas_similarity_threshold = 0.99
    updated_bump_image_url = None
    config = GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#ff00ff"),
        globe=GlobeLayerConfig(
            show_atmosphere=False,
            show_graticules=False,
            globe_image_url=globe_flat_texture_data_url,
            bump_image_url=globe_bump_test_data_url,
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

    canvas_assert_capture(page_session, "initial", canvas_similarity_threshold)
    widget.set_bump_image_url(updated_bump_image_url)
    page_session.wait_for_timeout(200)
    canvas_assert_capture(page_session, "updated", canvas_similarity_threshold)
