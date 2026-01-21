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
    canvas_label,
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


@pytest.mark.usefixtures("solara_test")
@pytest.mark.parametrize(
    ("resolution", "radius"),
    [
        pytest.param(3, 5.0, id="resolution-3"),
        pytest.param(18, 5.0, id="resolution-18"),
    ],
)
def test_point_resolution(
    page_session: Page,
    canvas_capture,
    canvas_label,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_earth_texture_url,
    resolution: int,
    radius: float,
) -> None:
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
            point_resolution=resolution,
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


@pytest.mark.usefixtures("solara_test")
def test_point_label_tooltip(
    page_session: Page, globe_hoverer, globe_earth_texture_url
) -> None:
    points_data = [{"lat": 0, "lng": 0, "label": "Center point"}]
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

    initial_image = canvas_capture(page_session)
    canvas_save_capture(initial_image, "test_points_transition_duration-initial", True)
    initial_ref = canvas_reference_path("test_points_transition_duration-initial")
    if not initial_ref.exists():
        raise AssertionError(
            f"Reference image missing. Save the capture to {initial_ref} and re-run."
        )
    canvas_compare_images(initial_image, initial_ref)

    updated_config = config.model_copy(
        update={
            "points": config.points.model_copy(update={"points_data": updated_points})
        }
    )
    widget.config = updated_config.model_dump(
        by_alias=True, exclude_none=True, exclude_defaults=True
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

    updated_image = canvas_capture(page_session)
    canvas_save_capture(updated_image, "test_points_transition_duration-updated", True)
    updated_ref = canvas_reference_path("test_points_transition_duration-updated")
    if not updated_ref.exists():
        raise AssertionError(
            f"Reference image missing. Save the capture to {updated_ref} and re-run."
        )
    canvas_compare_images(updated_image, updated_ref)
