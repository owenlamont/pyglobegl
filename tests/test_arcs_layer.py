from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

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
    page_session: Page, canvas_assert_capture, globe_earth_texture_url
) -> None:
    canvas_similarity_threshold = 0.985
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

    canvas_assert_capture(page_session, "initial", canvas_similarity_threshold)
    widget.set_arc_start_lat("sLat2")
    widget.set_arc_start_lng("sLng2")
    widget.set_arc_end_lat("eLat2")
    widget.set_arc_end_lng("eLng2")
    widget.set_arc_altitude("alt2")
    widget.set_arc_color("color2")
    widget.set_arcs_data(updated_arcs)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "updated", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_arcs_default_accessors(
    page_session: Page, canvas_assert_capture, globe_earth_texture_url
) -> None:
    canvas_similarity_threshold = 0.987
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

    canvas_assert_capture(page_session, "initial", canvas_similarity_threshold)
    widget.set_arcs_data(updated_arcs)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "updated", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_arc_dashes(
    page_session: Page, canvas_assert_capture, globe_earth_texture_url
) -> None:
    canvas_similarity_threshold = 0.985
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

    canvas_assert_capture(page_session, "solid", canvas_similarity_threshold)
    widget.set_arc_dash_length(updated_dash_length)
    widget.set_arc_dash_gap(updated_dash_gap)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "dashed", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_arc_runtime_update(
    page_session: Page, canvas_assert_capture, globe_earth_texture_url
) -> None:
    canvas_similarity_threshold = 0.96
    initial_colors = ["#ffcc00", "#00ffaa"]
    updated_colors = ["#ff0033", "#33ddff"]
    arc_id = uuid4()
    arcs_data = [
        ArcDatum(
            id=arc_id,
            start_lat=0,
            start_lng=-60,
            end_lat=0,
            end_lng=60,
            start_altitude=0.02,
            end_altitude=0.04,
            altitude=0.2,
            altitude_auto_scale=0.1,
            stroke=2.0,
            dash_length=1.0,
            dash_gap=0.0,
            dash_initial_gap=0.0,
            dash_animate_time=0.0,
            color=initial_colors,
            label="Initial arc",
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
            arc_start_lat="startLat",
            arc_start_lng="startLng",
            arc_end_lat="endLat",
            arc_end_lng="endLng",
            arc_start_altitude="startAltitude",
            arc_end_altitude="endAltitude",
            arc_color="color",
            arc_label="label",
            arc_stroke="stroke",
            arc_altitude="altitude",
            arc_altitude_auto_scale="altitudeAutoScale",
            arc_dash_length="dashLength",
            arc_dash_gap="dashGap",
            arc_dash_initial_gap="dashInitialGap",
            arc_dash_animate_time="dashAnimateTime",
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

    canvas_assert_capture(page_session, "initial", canvas_similarity_threshold)
    widget.update_arc(
        arc_id,
        start_lat=30,
        start_lng=-30,
        end_lat=-30,
        end_lng=30,
        start_altitude=0.4,
        end_altitude=0.6,
        altitude=0.8,
        altitude_auto_scale=0.9,
        stroke=6.0,
        dash_length=0.2,
        dash_gap=0.6,
        dash_initial_gap=0.4,
        dash_animate_time=0.0,
        color=updated_colors,
        label="Updated arc",
    )
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "updated", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_arc_stroke(
    page_session: Page, canvas_assert_capture, globe_earth_texture_url
) -> None:
    canvas_similarity_threshold = 0.975
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

    canvas_assert_capture(page_session, "thin", canvas_similarity_threshold)
    widget.set_arc_stroke(updated_stroke)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "thick", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_arc_start_end_altitude(
    page_session: Page, canvas_assert_capture, globe_earth_texture_url
) -> None:
    canvas_similarity_threshold = 0.984
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

    canvas_assert_capture(page_session, "initial", canvas_similarity_threshold)
    widget.set_arc_start_lat("startLat2")
    widget.set_arc_start_lng("startLng2")
    widget.set_arc_end_lat("endLat2")
    widget.set_arc_end_lng("endLng2")
    widget.set_arc_start_altitude("startAlt2")
    widget.set_arc_end_altitude("endAlt2")
    widget.set_arc_color("color2")
    widget.set_arcs_data(updated_arcs)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "updated", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_arc_curve_resolution(
    page_session: Page, canvas_assert_capture, globe_earth_texture_url
) -> None:
    canvas_similarity_threshold = 0.965
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

    canvas_assert_capture(page_session, "low", canvas_similarity_threshold)
    widget.set_arc_curve_resolution(updated_curve_resolution)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "high", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_arc_circular_resolution(
    page_session: Page, canvas_assert_capture, globe_earth_texture_url
) -> None:
    canvas_similarity_threshold = 0.99
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

    canvas_assert_capture(page_session, "low", canvas_similarity_threshold)
    widget.set_arc_circular_resolution(updated_circular_resolution)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "high", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_arc_dash_initial_gap(
    page_session: Page, canvas_assert_capture, globe_earth_texture_url
) -> None:
    canvas_similarity_threshold = 0.99
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

    canvas_assert_capture(page_session, "gap-0", canvas_similarity_threshold)
    widget.set_arc_dash_initial_gap(updated_gap)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "gap-0.6", canvas_similarity_threshold)


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
def test_arc_dash_animate_time_setter(
    page_session: Page, canvas_assert_capture, globe_earth_texture_url
) -> None:
    canvas_similarity_threshold = 0.99
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

    canvas_assert_capture(page_session, "off", canvas_similarity_threshold)
    widget.set_arc_dash_animate_time(2000)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "on", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_arcs_transition_duration(
    page_session: Page, canvas_assert_capture, globe_earth_texture_url
) -> None:
    canvas_similarity_threshold = 0.99
    initial_arcs = [
        {"startLat": 0, "startLng": -40, "endLat": 0, "endLng": 40, "color": "#ffcc00"}
    ]
    updated_arcs = [
        {
            "startLat": 20,
            "startLng": -20,
            "endLat": -10,
            "endLng": 30,
            "color": "#00ccff",
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
            arcs_data=initial_arcs,
            arc_start_lat="startLat",
            arc_start_lng="startLng",
            arc_end_lat="endLat",
            arc_end_lng="endLng",
            arc_color="color",
            arc_stroke=2.0,
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

    canvas_assert_capture(page_session, "initial", canvas_similarity_threshold)
    widget.set_arcs_transition_duration(0)
    widget.set_arcs_data(updated_arcs)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "updated", canvas_similarity_threshold)


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
    page_session: Page, canvas_assert_capture, globe_earth_texture_url
) -> None:
    canvas_similarity_threshold = 0.99
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

    canvas_assert_capture(page_session, "fixed-altitude", canvas_similarity_threshold)
    widget.set_arc_altitude(updated_altitude)
    widget.set_arc_altitude_auto_scale(updated_auto_scale)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "auto-scale", canvas_similarity_threshold)
