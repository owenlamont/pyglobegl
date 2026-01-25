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
    PointsLayerConfig,
)


if TYPE_CHECKING:
    from playwright.sync_api import Page


@pytest.mark.usefixtures("solara_test")
def test_points_accessors(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_earth_texture_url,
) -> None:
    points_data = [
        {"latitude": 0, "longitude": 0, "alt": 0.25, "radius": 1.2, "color": "#ff0000"},
        {
            "latitude": 15,
            "longitude": -45,
            "alt": 0.1,
            "radius": 0.8,
            "color": "#00ff00",
        },
        {
            "latitude": -20,
            "longitude": 60,
            "alt": 0.18,
            "radius": 1.0,
            "color": "#00ffff",
        },
    ]
    updated_points = [
        {"lat2": 10, "lng2": 10, "alt2": 0.05, "radius2": 0.7, "color2": "#00ff00"},
        {"lat2": -25, "lng2": 40, "alt2": 0.22, "radius2": 1.3, "color2": "#ff00ff"},
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
        points=PointsLayerConfig(
            points_data=points_data,
            point_lat="latitude",
            point_lng="longitude",
            point_altitude="alt",
            point_radius="radius",
            point_color="color",
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

    _assert_capture("test_points_accessors")
    widget.set_point_lat("lat2")
    widget.set_point_lng("lng2")
    widget.set_point_altitude("alt2")
    widget.set_point_radius("radius2")
    widget.set_point_color("color2")
    widget.set_points_data(updated_points)
    page_session.wait_for_timeout(100)
    _assert_capture("test_points_accessors-updated")


@pytest.mark.usefixtures("solara_test")
def test_point_resolution(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_earth_texture_url,
) -> None:
    initial_resolution = 3
    updated_resolution = 18
    radius = 5.0
    points_data = [
        {"lat": 0, "lng": 0, "altitude": 0.25, "radius": radius, "color": "#ffcc00"}
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
        points=PointsLayerConfig(
            points_data=points_data,
            point_altitude="altitude",
            point_radius="radius",
            point_color="color",
            point_resolution=initial_resolution,
        ),
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.6), transition_ms=0
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

    _assert_capture("test_point_resolution-resolution-3")
    widget.set_point_resolution(updated_resolution)
    page_session.wait_for_timeout(100)
    _assert_capture("test_point_resolution-resolution-18")


@pytest.mark.usefixtures("solara_test")
def test_point_label_tooltip(
    page_session: Page, globe_hoverer, globe_earth_texture_url
) -> None:
    points_data = [{"lat": 0, "lng": 0, "label": "Center point"}]
    updated_points = [{"lat": 0, "lng": 0, "label2": "Updated point"}]
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
        points=PointsLayerConfig(
            points_data=points_data,
            point_label="label",
            point_altitude=0.2,
            point_radius=1.2,
            point_color="#00ff00",
        ),
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.6), transition_ms=0
        ),
    )
    widget = GlobeWidget(config=config)
    display(widget)

    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )
    globe_hoverer(page_session)
    page_session.wait_for_function(
        """
        () => {
          const tooltip = document.querySelector(".float-tooltip-kap");
          if (!tooltip) {
            return false;
          }
          const style = window.getComputedStyle(tooltip);
          if (style.display === "none") {
            return false;
          }
          return (tooltip.textContent || "").includes("Center point");
        }
        """,
        timeout=20000,
    )

    widget.set_point_label("label2")
    widget.set_points_data(updated_points)
    page_session.wait_for_timeout(100)
    globe_hoverer(page_session)
    page_session.wait_for_function(
        """
        () => {
          const tooltip = document.querySelector(".float-tooltip-kap");
          if (!tooltip) {
            return false;
          }
          const style = window.getComputedStyle(tooltip);
          if (style.display === "none") {
            return false;
          }
          return (tooltip.textContent || "").includes("Updated point");
        }
        """,
        timeout=20000,
    )


@pytest.mark.usefixtures("solara_test")
def test_points_transition_duration(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_earth_texture_url,
) -> None:
    initial_points = [
        {"lat": 0, "lng": 0, "altitude": 0.2, "radius": 1.2, "color": "#ff0000"}
    ]
    updated_points = [
        {"lat": 20, "lng": 40, "altitude": 0.2, "radius": 1.2, "color": "#ff0000"}
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
        points=PointsLayerConfig(
            points_data=initial_points,
            point_altitude="altitude",
            point_radius="radius",
            point_color="color",
            points_transition_duration=0,
        ),
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.6), transition_ms=0
        ),
    )
    widget = GlobeWidget(config=config)
    display(widget)

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

    _assert_capture("test_points_transition_duration-initial")
    widget.set_points_transition_duration(0)
    widget.set_points_data(updated_points)
    page_session.wait_for_timeout(100)
    _assert_capture("test_points_transition_duration-updated")
