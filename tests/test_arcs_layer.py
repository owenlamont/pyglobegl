from __future__ import annotations

from typing import TYPE_CHECKING

from IPython.display import display
import numpy as np
import pytest
from skimage.metrics import structural_similarity

from pyglobegl import (
    ArcDatum,
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
    updated_arcs = [
        {
            "sLat2": 20,
            "sLng2": -10,
            "eLat2": -15,
            "eLng2": 35,
            "alt2": 0.12,
            "color2": "#00ccff",
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
    page_session.wait_for_function(
        """
        () => {
          const canvas = document.querySelector("canvas");
          if (!canvas) {
            return false;
          }
          const dataUrl = canvas.toDataURL("image/png");
          return dataUrl && dataUrl.length > 2000;
        }
        """,
        timeout=20000,
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

    _assert_capture("test_arcs_accessors")
    widget.set_arc_start_lat("sLat2")
    widget.set_arc_start_lng("sLng2")
    widget.set_arc_end_lat("eLat2")
    widget.set_arc_end_lng("eLng2")
    widget.set_arc_altitude("alt2")
    widget.set_arc_color("color2")
    widget.set_arcs_data(updated_arcs)
    page_session.wait_for_timeout(100)
    _assert_capture("test_arcs_accessors-updated")


@pytest.mark.usefixtures("solara_test")
def test_arcs_default_accessors(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_earth_texture_url,
) -> None:
    arcs_data = [
        ArcDatum(
            start_lat=0,
            start_lng=-30,
            end_lat=15,
            end_lng=35,
            altitude=0.25,
            color="#ffcc00",
        ),
        ArcDatum(
            start_lat=-10,
            start_lng=30,
            end_lat=25,
            end_lng=-10,
            altitude=0.15,
            color="#00ffaa",
        ),
    ]
    updated_arcs = [
        ArcDatum(
            start_lat=20,
            start_lng=-50,
            end_lat=-5,
            end_lng=30,
            altitude=0.2,
            color="#ff66cc",
        )
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
            arc_altitude="altitude",
            arc_color="color",
            arc_stroke=1.2,
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

    _assert_capture("test_arcs_default_accessors")
    widget.set_arcs_data(updated_arcs)
    page_session.wait_for_timeout(100)
    _assert_capture("test_arcs_default_accessors-updated")


@pytest.mark.usefixtures("solara_test")
def test_arc_dashes(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_earth_texture_url,
) -> None:
    initial_dash_length = 1.0
    initial_dash_gap = 0.0
    updated_dash_length = 0.2
    updated_dash_gap = 0.15
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
            arc_dash_length=initial_dash_length,
            arc_dash_gap=initial_dash_gap,
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

    def _assert_capture(label: str) -> None:
        captured_image = canvas_capture(page_session)
        reference_path = canvas_reference_path(label)
        if not reference_path.exists():
            canvas_save_capture(captured_image, label, False)
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

    _assert_capture("test_arc_dashes-solid")
    widget.set_arc_dash_length(updated_dash_length)
    widget.set_arc_dash_gap(updated_dash_gap)
    page_session.wait_for_timeout(100)
    _assert_capture("test_arc_dashes-dashed")


@pytest.mark.usefixtures("solara_test")
def test_arc_color_gradient(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_earth_texture_url,
) -> None:
    initial_colors = ["#ffcc00", "#00ffaa"]
    updated_colors = ["#ff0033", "#33ddff"]
    arcs_data = [
        {
            "id": "arc-gradient",
            "startLat": 5,
            "startLng": -50,
            "endLat": -5,
            "endLng": 50,
            "color": initial_colors,
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
            arc_stroke=1.2,
            arc_altitude=0.25,
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

    def _assert_capture(label: str) -> None:
        captured_image = canvas_capture(page_session)
        reference_path = canvas_reference_path(label)
        if not reference_path.exists():
            canvas_save_capture(captured_image, label, False)
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

    _assert_capture("test_arc_color_gradient-gradient")
    widget.update_arc("arc-gradient", color=updated_colors)
    page_session.wait_for_timeout(100)
    _assert_capture("test_arc_color_gradient-gradient-alt")


@pytest.mark.usefixtures("solara_test")
def test_arc_stroke(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_earth_texture_url,
) -> None:
    initial_stroke = 0.4
    updated_stroke = 2.5
    arcs_data = [
        {"startLat": 0, "startLng": -35, "endLat": 0, "endLng": 35, "color": "#ffcc00"}
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
            arc_stroke=initial_stroke,
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

    def _assert_capture(label: str) -> None:
        captured_image = canvas_capture(page_session)
        reference_path = canvas_reference_path(label)
        if not reference_path.exists():
            canvas_save_capture(captured_image, label, False)
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

    _assert_capture("test_arc_stroke-thin")
    widget.set_arc_stroke(updated_stroke)
    page_session.wait_for_timeout(100)
    _assert_capture("test_arc_stroke-thick")


@pytest.mark.usefixtures("solara_test")
def test_arc_start_end_altitude(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_earth_texture_url,
) -> None:
    arcs_data = [
        {
            "startLat": 0,
            "startLng": -40,
            "endLat": 10,
            "endLng": 40,
            "startAlt": 0.0,
            "endAlt": 0.6,
            "color": "#33ddff",
        }
    ]
    updated_arcs = [
        {
            "startLat2": -15,
            "startLng2": -20,
            "endLat2": 20,
            "endLng2": 30,
            "startAlt2": 0.4,
            "endAlt2": 0.1,
            "color2": "#ffcc00",
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
            arc_start_altitude="startAlt",
            arc_end_altitude="endAlt",
            arc_color="color",
            arc_stroke=1.1,
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

    _assert_capture("test_arc_start_end_altitude")
    widget.set_arc_start_lat("startLat2")
    widget.set_arc_start_lng("startLng2")
    widget.set_arc_end_lat("endLat2")
    widget.set_arc_end_lng("endLng2")
    widget.set_arc_start_altitude("startAlt2")
    widget.set_arc_end_altitude("endAlt2")
    widget.set_arc_color("color2")
    widget.set_arcs_data(updated_arcs)
    page_session.wait_for_timeout(100)
    _assert_capture("test_arc_start_end_altitude-updated")


@pytest.mark.usefixtures("solara_test")
def test_arc_curve_resolution(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_earth_texture_url,
) -> None:
    initial_curve_resolution = 2
    updated_curve_resolution = 120
    arcs_data = [
        {
            "startLat": -5,
            "startLng": -50,
            "endLat": 15,
            "endLng": 50,
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
            arc_color="color",
            arc_altitude=0.4,
            arc_curve_resolution=initial_curve_resolution,
            arc_stroke=1.2,
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

    def _assert_capture(label: str) -> None:
        captured_image = canvas_capture(page_session)
        reference_path = canvas_reference_path(label)
        if not reference_path.exists():
            canvas_save_capture(captured_image, label, False)
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

    _assert_capture("test_arc_curve_resolution-low")
    widget.set_arc_curve_resolution(updated_curve_resolution)
    page_session.wait_for_timeout(100)
    _assert_capture("test_arc_curve_resolution-high")


@pytest.mark.usefixtures("solara_test")
def test_arc_circular_resolution(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_earth_texture_url,
) -> None:
    initial_circular_resolution = 2
    updated_circular_resolution = 16
    arcs_data = [
        {
            "startLat": 10,
            "startLng": -60,
            "endLat": -5,
            "endLng": 60,
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
            arc_color="color",
            arc_altitude=0.35,
            arc_circular_resolution=initial_circular_resolution,
            arc_stroke=2.4,
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

    def _assert_capture(label: str) -> None:
        captured_image = canvas_capture(page_session)
        reference_path = canvas_reference_path(label)
        if not reference_path.exists():
            canvas_save_capture(captured_image, label, False)
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

    _assert_capture("test_arc_circular_resolution-low")
    widget.set_arc_circular_resolution(updated_circular_resolution)
    page_session.wait_for_timeout(100)
    _assert_capture("test_arc_circular_resolution-high")


@pytest.mark.usefixtures("solara_test")
def test_arc_dash_initial_gap(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_earth_texture_url,
) -> None:
    initial_gap = 0.0
    updated_gap = 0.6
    arcs_data = [
        {"startLat": 0, "startLng": -35, "endLat": 0, "endLng": 35, "color": "#ffcc00"}
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
            arc_dash_length=0.2,
            arc_dash_gap=0.1,
            arc_dash_initial_gap=initial_gap,
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

    def _assert_capture(label: str) -> None:
        captured_image = canvas_capture(page_session)
        reference_path = canvas_reference_path(label)
        if not reference_path.exists():
            canvas_save_capture(captured_image, label, False)
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

    _assert_capture("test_arc_dash_initial_gap-gap-0")
    widget.set_arc_dash_initial_gap(updated_gap)
    page_session.wait_for_timeout(100)
    _assert_capture("test_arc_dash_initial_gap-gap-0.6")


@pytest.mark.usefixtures("solara_test")
def test_arc_dash_animation_changes(
    page_session: Page,
    canvas_capture,
    canvas_label,
    canvas_save_capture,
    globe_earth_texture_url,
) -> None:
    arcs_data = [
        {"startLat": 0, "startLng": -60, "endLat": 0, "endLng": 60, "color": "#ffcc00"}
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
            arc_stroke=2.6,
            arc_dash_length=0.1,
            arc_dash_gap=0.2,
            arc_dash_animate_time=1000,
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

    first = canvas_capture(page_session)
    first_array = np.asarray(first.convert("RGBA"))
    passed = False
    score = 1.0
    changed = 0.0
    second = first
    for _attempt in range(3):
        page_session.wait_for_timeout(500)
        second = canvas_capture(page_session)
        second_array = np.asarray(second.convert("RGBA"))
        score = structural_similarity(
            first_array, second_array, channel_axis=2, data_range=255
        )
        diff = np.abs(first_array.astype(int) - second_array.astype(int))
        changed = (diff.max(axis=2) > 5).mean()
        passed = changed > 0.002
        if passed:
            break
    canvas_save_capture(first, f"{canvas_label}-t0", passed)
    canvas_save_capture(second, f"{canvas_label}-t1", passed)
    assert passed, (
        "Expected animation frames to differ "
        f"(changed={changed:.4f}, ssim={score:.4f})."
    )


@pytest.mark.usefixtures("solara_test")
def test_arc_label_tooltip(page_session: Page, globe_earth_texture_url) -> None:
    arcs_data = [
        {
            "startLat": 0,
            "startLng": -20,
            "endLat": 0,
            "endLng": 20,
            "color": "#ff00cc",
            "label": "Initial arc",
        }
    ]
    updated_arcs = [
        {
            "startLat": 0,
            "startLng": -20,
            "endLat": 0,
            "endLng": 20,
            "color": "#ff00cc",
            "label2": "Updated arc",
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
            arc_label="label",
            arc_color="color",
            arc_altitude=0.2,
            arc_stroke=1.2,
            arcs_transition_duration=0,
        ),
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.7), transition_ms=0
        ),
    )
    widget = GlobeWidget(config=config)
    display(widget)

    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )
    canvas = page_session.locator("canvas")
    box = canvas.bounding_box()
    if box is None:
        raise AssertionError("Canvas bounding box not found.")

    def _assert_tooltip(expected: str) -> None:
        page_session.mouse.move(box["x"] - 50, box["y"] - 50)
        page_session.wait_for_timeout(100)
        tooltip_ready = False
        for _ in range(25):
            tooltip_ready = page_session.evaluate(
                """
                (text) => {
                  const target = document.querySelector(".scene-container");
                  if (!target) {
                    return false;
                  }
                  const rect = target.getBoundingClientRect();
                  const x = rect.left + rect.width / 2;
                  const y = rect.top + rect.height / 2;
                  const opts = {
                    clientX: x,
                    clientY: y,
                    pageX: x + window.scrollX,
                    pageY: y + window.scrollY,
                    bubbles: true,
                    cancelable: true,
                    view: window,
                    pointerType: "mouse",
                    pointerId: 1,
                    isPrimary: true,
                  };
                  target.dispatchEvent(new PointerEvent("pointermove", opts));
                  target.dispatchEvent(new MouseEvent("mousemove", opts));
                  const tooltip = document.querySelector(".float-tooltip-kap");
                  if (!tooltip) {
                    return false;
                  }
                  const style = window.getComputedStyle(tooltip);
                  if (style.display === "none") {
                    return false;
                  }
                  return (tooltip.textContent || "").includes(text);
                }
                """,
                expected,
            )
            if tooltip_ready:
                break
            page_session.wait_for_timeout(80)
        assert tooltip_ready, f"Expected tooltip text to include: {expected}"

    _assert_tooltip("Initial arc")

    widget.set_arc_label("label2")
    widget.set_arcs_data(updated_arcs)
    page_session.wait_for_timeout(200)
    _assert_tooltip("Updated arc")


@pytest.mark.usefixtures("solara_test")
def test_arc_altitude_modes(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_earth_texture_url,
) -> None:
    initial_altitude = 0.15
    initial_auto_scale = None
    updated_altitude = None
    updated_auto_scale = 2.5
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
            arc_altitude=initial_altitude,
            arc_altitude_auto_scale=initial_auto_scale,
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

    def _assert_capture(label: str) -> None:
        captured_image = canvas_capture(page_session)
        reference_path = canvas_reference_path(label)
        if not reference_path.exists():
            canvas_save_capture(captured_image, label, False)
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

    _assert_capture("test_arc_altitude_modes-fixed-altitude")
    widget.set_arc_altitude(updated_altitude)
    widget.set_arc_altitude_auto_scale(updated_auto_scale)
    page_session.wait_for_timeout(100)
    _assert_capture("test_arc_altitude_modes-auto-scale")
