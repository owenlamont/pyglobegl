from __future__ import annotations

from typing import TYPE_CHECKING

from IPython.display import display
import pytest

from pyglobegl import GlobeConfig, GlobeInitConfig, GlobeLayoutConfig, GlobeWidget


if TYPE_CHECKING:
    from playwright.sync_api import Page


@pytest.mark.usefixtures("solara_test")
def test_solara_canvas_capture_baseline(
    page_session: Page,
    canvas_capture,
    canvas_label,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
) -> None:
    canvas_similarity_threshold = 0.99
    config = GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#00ff00"),
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
    reference_path = canvas_reference_path(test_label)
    if not reference_path.exists():
        raise AssertionError(
            f"Reference image missing. Save the capture to {reference_path} and re-run."
        )
    try:
        score = canvas_compare_images(captured_image, reference_path)
        passed = score >= canvas_similarity_threshold
    except Exception:
        canvas_save_capture(captured_image, test_label, False)
        raise
    canvas_save_capture(captured_image, test_label, passed)
    assert passed, (
        "Captured image similarity below threshold. "
        f"Score: {score:.4f} (threshold {canvas_similarity_threshold:.4f})."
    )
