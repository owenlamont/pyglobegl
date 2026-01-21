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


@pytest.mark.parametrize(
    ("pov", "expected_altitude"),
    [
        pytest.param(
            PointOfView(lat=0, lng=-90, altitude=1.2), 1.2, id="pov-lat0-lng-90-alt1.2"
        ),
        pytest.param(
            PointOfView(lat=0, lng=-90, altitude=1.4), 1.4, id="pov-lat0-lng-90-alt1.4"
        ),
        pytest.param(
            PointOfView(lat=45, lng=90, altitude=1.4), 1.4, id="pov-lat45-lng90-alt1.4"
        ),
    ],
)
@pytest.mark.usefixtures("solara_test")
def test_view_point_of_view(
    page_session: Page,
    canvas_capture,
    canvas_label,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_earth_texture_url,
    pov,
    expected_altitude,
) -> None:
    config = GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#ff00ff"),
        view=GlobeViewConfig(point_of_view=pov),
        globe=GlobeLayerConfig(
            globe_image_url=globe_earth_texture_url,
            show_atmosphere=False,
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
    page_session.wait_for_function(
        (
            "expected => window.__pyglobegl_pov && "
            "Math.abs(window.__pyglobegl_pov.altitude - expected) < 0.001"
        ),
        arg=expected_altitude,
        timeout=20000,
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
