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
def test_globe_atmosphere_altitude(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    globe_earth_texture_url,
) -> None:
    canvas_similarity_threshold = 0.99
    initial_altitude = 0.05
    updated_altitude = 0.25
    config = GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#000000"),
        globe=GlobeLayerConfig(
            globe_image_url=globe_earth_texture_url,
            show_atmosphere=True,
            atmosphere_color="#00ffff",
            atmosphere_altitude=initial_altitude,
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

    def _assert_capture(label: str) -> None:
        captured_image = canvas_capture(page_session)
        reference_path = canvas_reference_path(label)
        if not reference_path.exists():
            raise AssertionError(
                "Reference image missing. Save the capture to "
                f"{reference_path} and re-run."
            )
        try:
            score = canvas_compare_images(captured_image, reference_path)
            passed = score >= canvas_similarity_threshold
        except Exception:
            canvas_save_capture(captured_image, label, False)
            raise
        canvas_save_capture(captured_image, label, passed)
        assert passed, (
            "Captured image similarity below threshold. "
            f"Score: {score:.4f} (threshold {canvas_similarity_threshold:.4f})."
        )

    _assert_capture("test_globe_atmosphere_altitude-altitude-low")
    widget.set_atmosphere_altitude(updated_altitude)
    page_session.wait_for_timeout(100)
    _assert_capture("test_globe_atmosphere_altitude-altitude-high")
