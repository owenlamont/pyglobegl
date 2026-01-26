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
    page_session: Page, canvas_assert_capture, globe_earth_texture_url
) -> None:
    canvas_similarity_threshold = 0.99
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

    canvas_assert_capture(page_session, "initial", canvas_similarity_threshold)
    widget.set_point_lat("lat2")
    widget.set_point_lng("lng2")
    widget.set_point_altitude("alt2")
    widget.set_point_radius("radius2")
    widget.set_point_color("color2")
    widget.set_points_data(updated_points)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "updated", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_point_resolution(
    page_session: Page, canvas_assert_capture, globe_earth_texture_url
) -> None:
    canvas_similarity_threshold = 0.985
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

    canvas_assert_capture(page_session, "resolution-3", canvas_similarity_threshold)
    widget.set_point_resolution(updated_resolution)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "resolution-18", canvas_similarity_threshold)


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
    page_session: Page, canvas_assert_capture, globe_earth_texture_url
) -> None:
    canvas_similarity_threshold = 0.99
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

    canvas_assert_capture(page_session, "initial", canvas_similarity_threshold)
    widget.set_points_transition_duration(0)
    widget.set_points_data(updated_points)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "updated", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_points_merge(
    page_session: Page, canvas_assert_capture, globe_earth_texture_url
) -> None:
    canvas_similarity_threshold = 0.99
    points_data = [
        {"lat": 0, "lng": 0, "altitude": 0.2, "radius": 1.6, "color": "#ffcc00"},
        {"lat": 10, "lng": 20, "altitude": 0.25, "radius": 1.2, "color": "#00ccff"},
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
            points_merge=False,
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

    canvas_assert_capture(page_session, "off", canvas_similarity_threshold)
    widget.set_points_merge(True)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "on", canvas_similarity_threshold)
