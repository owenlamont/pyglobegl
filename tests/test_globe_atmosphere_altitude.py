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


@pytest.mark.parametrize(
    "altitude",
    [pytest.param(0.05, id="altitude-low"), pytest.param(0.25, id="altitude-high")],
)
@pytest.mark.usefixtures("solara_test")
def test_globe_atmosphere_altitude(
    page_session: Page,
    canvas_capture,
    canvas_label,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    globe_earth_texture_url,
    altitude,
) -> None:
    config = GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#000000"),
        globe=GlobeLayerConfig(
            globe_image_url=globe_earth_texture_url,
            show_atmosphere=True,
            atmosphere_color="#00ffff",
            atmosphere_altitude=altitude,
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

    captured_image = canvas_capture(page_session)
    test_label = canvas_label
    canvas_save_capture(captured_image, test_label)

    reference_path = canvas_reference_path(test_label)
    if not reference_path.exists():
        raise AssertionError(
            f"Reference image missing. Save the capture to {reference_path} and re-run."
        )
    try:
        canvas_compare_images(captured_image, reference_path)
    except AssertionError:
        canvas_save_capture(captured_image, f"{test_label}-mismatch")
        raise
