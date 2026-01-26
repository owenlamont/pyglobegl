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
def test_globe_layer_graticules(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
) -> None:
    canvas_similarity_threshold = 0.99
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

    _assert_capture("test_globe_layer_graticules-graticules-off")
    widget.set_show_graticules(updated_show_graticules)
    page_session.wait_for_timeout(100)
    _assert_capture("test_globe_layer_graticules-graticules-on")


@pytest.mark.usefixtures("solara_test")
def test_globe_layer_show_globe(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    globe_earth_texture_url,
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

    def _assert_capture(label: str) -> None:
        captured_image = canvas_capture(page_session)
        reference_path = canvas_reference_path(label)
        if not reference_path.exists():
            reference_path.parent.mkdir(parents=True, exist_ok=True)
            captured_image.save(reference_path)
            raise AssertionError(
                "Reference image missing. Saved capture to "
                f"{reference_path}; verify and re-run."
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

    _assert_capture("test_globe_layer_show_globe-on")
    widget.set_show_globe(False)
    page_session.wait_for_timeout(200)
    _assert_capture("test_globe_layer_show_globe-off")
