from __future__ import annotations

from typing import TYPE_CHECKING

from IPython.display import display
import pytest

from pyglobegl import (
    ArcsLayerConfig,
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
def test_arcs_accessors(
    page_session: Page,
    canvas_capture,
    canvas_label,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_earth_texture_url,
) -> None:
    arcs_data = [
        {
            "startLat": 0,
            "startLng": -30,
            "endLat": 15,
            "endLng": 35,
            "alt": 0.25,
            "color": "#ff0033",
        },
        {
            "startLat": -10,
            "startLng": 30,
            "endLat": 25,
            "endLng": -10,
            "alt": 0.15,
            "color": "#00ffaa",
        },
    ]

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
        arcs=ArcsLayerConfig(
            arcs_data=arcs_data,
            arc_start_lat="startLat",
            arc_start_lng="startLng",
            arc_end_lat="endLat",
            arc_end_lng="endLng",
            arc_altitude="alt",
            arc_color="color",
            arc_stroke=0.7,
            arcs_transition_duration=0,
        ),
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.7), transition_ms=0
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
    reference_path = canvas_reference_path(test_label)
    if not reference_path.exists():
        canvas_save_capture(captured_image, test_label, False)
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


@pytest.mark.usefixtures("solara_test")
@pytest.mark.parametrize(
    ("dash_length", "dash_gap"),
    [pytest.param(1.0, 0.0, id="solid"), pytest.param(0.2, 0.15, id="dashed")],
)
def test_arc_dashes(
    page_session: Page,
    canvas_capture,
    canvas_label,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_earth_texture_url,
    dash_length: float,
    dash_gap: float,
) -> None:
    arcs_data = [
        {
            "startLat": 0,
            "startLng": -35,
            "endLat": 0,
            "endLng": 35,
            "alt": 0.2,
            "color": "#ffcc00",
        }
    ]

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
        arcs=ArcsLayerConfig(
            arcs_data=arcs_data,
            arc_start_lat="startLat",
            arc_start_lng="startLng",
            arc_end_lat="endLat",
            arc_end_lng="endLng",
            arc_altitude="alt",
            arc_color="color",
            arc_stroke=0.8,
            arc_dash_length=dash_length,
            arc_dash_gap=dash_gap,
            arc_dash_animate_time=0,
            arcs_transition_duration=0,
        ),
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.7), transition_ms=0
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
    reference_path = canvas_reference_path(test_label)
    if not reference_path.exists():
        canvas_save_capture(captured_image, test_label, False)
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


@pytest.mark.usefixtures("solara_test")
@pytest.mark.parametrize(
    ("altitude", "auto_scale"),
    [
        pytest.param(0.45, None, id="fixed-altitude"),
        pytest.param(None, 0.8, id="auto-scale"),
    ],
)
def test_arc_altitude_modes(
    page_session: Page,
    canvas_capture,
    canvas_label,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_earth_texture_url,
    altitude: float | None,
    auto_scale: float | None,
) -> None:
    arcs_data = [
        {
            "startLat": 10,
            "startLng": -40,
            "endLat": -10,
            "endLng": 40,
            "color": "#33ddff",
        }
    ]

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
        arcs=ArcsLayerConfig(
            arcs_data=arcs_data,
            arc_start_lat="startLat",
            arc_start_lng="startLng",
            arc_end_lat="endLat",
            arc_end_lng="endLng",
            arc_color="color",
            arc_stroke=0.9,
            arc_altitude=altitude,
            arc_altitude_auto_scale=auto_scale,
            arcs_transition_duration=0,
        ),
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.8), transition_ms=0
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
    reference_path = canvas_reference_path(test_label)
    if not reference_path.exists():
        canvas_save_capture(captured_image, test_label, False)
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
