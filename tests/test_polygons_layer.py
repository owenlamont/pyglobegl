from __future__ import annotations

import math
from typing import TYPE_CHECKING
from uuid import uuid4

from geojson_pydantic import Polygon
from geojson_pydantic.types import Position2D, Position3D
from IPython.display import display
from pydantic import AnyUrl, TypeAdapter
import pytest

from pyglobegl import (
    GlobeConfig,
    GlobeInitConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeMaterialSpec,
    GlobeViewConfig,
    GlobeWidget,
    PointOfView,
    PolygonDatum,
    PolygonsLayerConfig,
)


if TYPE_CHECKING:
    from playwright.sync_api import Page


def _pos(lng: float, lat: float) -> Position2D:
    return Position2D(float(lng), float(lat))


def _polygon_coords(
    west: float, south: float, east: float, north: float
) -> list[list[Position2D | Position3D]]:
    return [
        [
            _pos(west, south),
            _pos(west, north),
            _pos(east, north),
            _pos(east, south),
            _pos(west, south),
        ]
    ]


def _polygon(west: float, south: float, east: float, north: float) -> Polygon:
    if west > east or (east - west) > 180:
        raise ValueError("Polygon bounds must not cross the antimeridian.")
    return Polygon(
        type="Polygon", coordinates=_polygon_coords(west, south, east, north)
    )


def _circle_polygon(
    lng: float, lat: float, radius_deg: float, *, steps: int = 72
) -> Polygon:
    """Return a CCW GeoJSON polygon ring for use with three-globe caps."""
    coords: list[Position2D | Position3D] = []
    for i in range(steps):
        angle = 2 * math.pi * (i / steps)
        lat_offset = radius_deg * math.sin(angle)
        lng_offset = (
            radius_deg * math.cos(angle) / max(1e-6, math.cos(math.radians(lat)))
        )
        coords.append(_pos(lng + lng_offset, lat + lat_offset))
    coords.append(coords[0])
    area = 0.0
    for i in range(len(coords) - 1):
        x1 = coords[i][0]
        y1 = coords[i][1]
        x2 = coords[i + 1][0]
        y2 = coords[i + 1][1]
        area += (x1 * y2) - (x2 * y1)
    if area > 0:
        coords.reverse()
    return Polygon(type="Polygon", coordinates=[coords])


_URL_ADAPTER = TypeAdapter(AnyUrl)


def _make_config(
    globe_texture_url: str,
    polygons: PolygonsLayerConfig,
    *,
    lat: float = 0,
    lng: float = 0,
    altitude: float = 1.6,
    width: int = 256,
    height: int = 256,
) -> GlobeConfig:
    globe_url = _URL_ADAPTER.validate_python(globe_texture_url)
    return GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(
            width=width, height=height, background_color="#000000"
        ),
        globe=GlobeLayerConfig(
            globe_image_url=globe_url, show_atmosphere=False, show_graticules=False
        ),
        polygons=polygons,
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=lat, lng=lng, altitude=altitude),
            transition_ms=0,
        ),
    )


def _await_globe_ready(page_session: Page) -> None:
    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )
    page_session.wait_for_timeout(250)


def _assert_canvas_matches(
    page_session: Page,
    canvas_capture,
    canvas_label: str,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold: float,
) -> None:
    captured_image = canvas_capture(page_session)
    reference_path = canvas_reference_path(canvas_label)
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
        canvas_save_capture(captured_image, canvas_label, False)
        raise
    canvas_save_capture(captured_image, canvas_label, passed)
    assert passed, (
        "Captured image similarity below threshold. "
        f"Score: {score:.4f} (threshold {canvas_similarity_threshold:.4f})."
    )


@pytest.mark.usefixtures("solara_test")
def test_polygons_accessors(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    globe_flat_texture_data_url,
) -> None:
    canvas_similarity_threshold = 0.975
    polygons_data = [
        PolygonDatum(
            geometry=_polygon(-25, -5, -5, 10),
            cap_color="#ff66cc",
            side_color="#ff66cc",
            stroke_color=None,
            altitude=0.05,
            cap_curvature_resolution=0.5,
        ),
        PolygonDatum(
            geometry=_polygon(5, -5, 25, 10),
            cap_color="#66ccff",
            side_color="#66ccff",
            stroke_color=None,
            altitude=0.05,
            cap_curvature_resolution=1.0,
        ),
    ]
    updated_polygons = [
        PolygonDatum(
            geometry=_polygon(-10, -10, 10, 0),
            cap_color="#ffcc00",
            side_color="#3366ff",
            stroke_color=None,
            altitude=0.08,
            cap_curvature_resolution=0.2,
        )
    ]

    config = _make_config(
        globe_flat_texture_data_url,
        PolygonsLayerConfig(
            polygons_data=polygons_data, polygons_transition_duration=0
        ),
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    _assert_canvas_matches(
        page_session,
        canvas_capture,
        "test_polygons_accessors",
        canvas_reference_path,
        canvas_compare_images,
        canvas_save_capture,
        canvas_similarity_threshold,
    )
    widget.set_polygons_data(updated_polygons)
    page_session.wait_for_timeout(100)
    _assert_canvas_matches(
        page_session,
        canvas_capture,
        "test_polygons_accessors-updated",
        canvas_reference_path,
        canvas_compare_images,
        canvas_save_capture,
        canvas_similarity_threshold,
    )


@pytest.mark.usefixtures("solara_test")
def test_polygon_label_tooltip(
    page_session: Page, globe_hoverer, globe_flat_texture_data_url
) -> None:
    polygons_data = [
        PolygonDatum(
            geometry=_polygon(-10, -5, 10, 5),
            label="Initial polygon",
            cap_color="#ffcc00",
            side_color="#ffcc00",
            altitude=0.06,
        )
    ]
    updated_polygons = [
        PolygonDatum(
            geometry=_polygon(-10, -5, 10, 5),
            label="Updated polygon",
            cap_color="#ffcc00",
            side_color="#ffcc00",
            altitude=0.06,
        )
    ]

    config = _make_config(
        globe_flat_texture_data_url,
        PolygonsLayerConfig(
            polygons_data=polygons_data, polygons_transition_duration=0
        ),
        altitude=1.7,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
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
          return (tooltip.textContent || "").includes("Initial polygon");
        }
        """,
        timeout=20000,
    )

    widget.set_polygons_data(updated_polygons)
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
          return (tooltip.textContent || "").includes("Updated polygon");
        }
        """,
        timeout=20000,
    )


@pytest.mark.usefixtures("solara_test")
def test_polygons_transition_duration(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    globe_flat_texture_data_url,
) -> None:
    canvas_similarity_threshold = 0.984
    initial_polygons = [
        PolygonDatum(
            geometry=_polygon(-30, -10, -10, 10),
            cap_color="#ffcc00",
            side_color="#ffcc00",
            stroke_color=None,
            altitude=0.08,
        )
    ]
    updated_polygons = [
        PolygonDatum(
            geometry=_polygon(10, -10, 30, 10),
            cap_color="#66ccff",
            side_color="#66ccff",
            stroke_color=None,
            altitude=0.08,
        )
    ]

    config = _make_config(
        globe_flat_texture_data_url,
        PolygonsLayerConfig(
            polygons_data=initial_polygons, polygons_transition_duration=1200
        ),
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    _assert_canvas_matches(
        page_session,
        canvas_capture,
        "test_polygons_transition_duration-initial",
        canvas_reference_path,
        canvas_compare_images,
        canvas_save_capture,
        canvas_similarity_threshold,
    )
    widget.set_polygons_transition_duration(0)
    widget.set_polygons_data(updated_polygons)
    page_session.wait_for_timeout(100)
    _assert_canvas_matches(
        page_session,
        canvas_capture,
        "test_polygons_transition_duration-updated",
        canvas_reference_path,
        canvas_compare_images,
        canvas_save_capture,
        canvas_similarity_threshold,
    )


@pytest.mark.usefixtures("solara_test")
def test_polygon_cap_material(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    globe_flat_texture_data_url,
) -> None:
    canvas_similarity_threshold = 0.99
    polygon_id = uuid4()
    polygons_data = [
        PolygonDatum(
            id=polygon_id,
            geometry=_circle_polygon(0, 0, 10, steps=36),
            cap_color="#ffcc00",
            side_color="#334455",
            altitude=0.12,
        )
    ]
    config = _make_config(
        globe_flat_texture_data_url,
        PolygonsLayerConfig(
            polygons_data=polygons_data, polygons_transition_duration=0
        ),
        altitude=1.7,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    _assert_canvas_matches(
        page_session,
        canvas_capture,
        "test_polygon_cap_material-initial",
        canvas_reference_path,
        canvas_compare_images,
        canvas_save_capture,
        canvas_similarity_threshold,
    )

    widget.set_polygon_cap_material(
        GlobeMaterialSpec(
            type="MeshBasicMaterial", params={"color": "#00ff00", "wireframe": True}
        )
    )
    page_session.wait_for_timeout(100)
    _assert_canvas_matches(
        page_session,
        canvas_capture,
        "test_polygon_cap_material-updated",
        canvas_reference_path,
        canvas_compare_images,
        canvas_save_capture,
        canvas_similarity_threshold,
    )


@pytest.mark.usefixtures("solara_test")
def test_polygon_side_material(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    globe_flat_texture_data_url,
) -> None:
    canvas_similarity_threshold = 0.99
    polygons_data = [
        PolygonDatum(
            geometry=_circle_polygon(0, 0, 8, steps=36),
            cap_color="#ffcc00",
            side_color="#223344",
            altitude=0.18,
        )
    ]
    config = _make_config(
        globe_flat_texture_data_url,
        PolygonsLayerConfig(
            polygons_data=polygons_data, polygons_transition_duration=0
        ),
        lat=0,
        lng=90,
        altitude=1.8,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    _assert_canvas_matches(
        page_session,
        canvas_capture,
        "test_polygon_side_material-initial",
        canvas_reference_path,
        canvas_compare_images,
        canvas_save_capture,
        canvas_similarity_threshold,
    )

    widget.set_polygon_side_material(
        GlobeMaterialSpec(
            type="MeshBasicMaterial", params={"color": "#00ccff", "wireframe": True}
        )
    )
    page_session.wait_for_timeout(100)
    _assert_canvas_matches(
        page_session,
        canvas_capture,
        "test_polygon_side_material-updated",
        canvas_reference_path,
        canvas_compare_images,
        canvas_save_capture,
        canvas_similarity_threshold,
    )


@pytest.mark.usefixtures("solara_test")
def test_polygon_cap_color(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    globe_flat_texture_data_url,
) -> None:
    canvas_similarity_threshold = 0.99
    initial_cap_color = "#ff66cc"
    updated_cap_color = "#66ccff"
    polygon_id = uuid4()
    polygon = _polygon(-20, -5, 20, 5)
    config = _make_config(
        globe_flat_texture_data_url,
        PolygonsLayerConfig(
            polygons_data=[
                PolygonDatum(
                    id=polygon_id,
                    geometry=polygon,
                    cap_color=initial_cap_color,
                    side_color=initial_cap_color,
                    stroke_color=None,
                    altitude=0.3,
                    cap_curvature_resolution=4.0,
                )
            ],
            polygons_transition_duration=0,
        ),
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    _assert_canvas_matches(
        page_session,
        canvas_capture,
        "test_polygon_cap_color-cap-ff66cc",
        canvas_reference_path,
        canvas_compare_images,
        canvas_save_capture,
        canvas_similarity_threshold,
    )
    widget.update_polygon(
        polygon_id, cap_color=updated_cap_color, side_color=updated_cap_color
    )
    page_session.wait_for_timeout(100)
    _assert_canvas_matches(
        page_session,
        canvas_capture,
        "test_polygon_cap_color-cap-66ccff",
        canvas_reference_path,
        canvas_compare_images,
        canvas_save_capture,
        canvas_similarity_threshold,
    )


@pytest.mark.usefixtures("solara_test")
def test_polygon_side_color(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    globe_flat_texture_data_url,
) -> None:
    canvas_similarity_threshold = 0.99
    initial_side_color = "#66ccff"
    updated_side_color = "#ffcc66"
    polygon_id = uuid4()
    polygon = _polygon(-15, 5, 15, 20)
    config = _make_config(
        globe_flat_texture_data_url,
        PolygonsLayerConfig(
            polygons_data=[
                PolygonDatum(
                    id=polygon_id,
                    geometry=polygon,
                    cap_color="#f0f0f0",
                    side_color=initial_side_color,
                    stroke_color=None,
                    altitude=0.4,
                    cap_curvature_resolution=4.0,
                )
            ],
            polygons_transition_duration=0,
        ),
        lat=40,
        altitude=1.5,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    _assert_canvas_matches(
        page_session,
        canvas_capture,
        "test_polygon_side_color-side-66ccff",
        canvas_reference_path,
        canvas_compare_images,
        canvas_save_capture,
        canvas_similarity_threshold,
    )
    widget.update_polygon(polygon_id, side_color=updated_side_color)
    page_session.wait_for_timeout(100)
    _assert_canvas_matches(
        page_session,
        canvas_capture,
        "test_polygon_side_color-side-ffcc66",
        canvas_reference_path,
        canvas_compare_images,
        canvas_save_capture,
        canvas_similarity_threshold,
    )


@pytest.mark.usefixtures("solara_test")
def test_polygon_stroke_color(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    globe_flat_texture_data_url,
) -> None:
    canvas_similarity_threshold = 0.99
    initial_stroke_color = "#ffffff"
    updated_stroke_color = "#00ffcc"
    polygon_id = uuid4()
    polygon = _polygon(-20, -5, 20, 5)
    config = _make_config(
        globe_flat_texture_data_url,
        PolygonsLayerConfig(
            polygons_data=[
                PolygonDatum(
                    id=polygon_id,
                    geometry=polygon,
                    cap_color="#ffcc66",
                    side_color="#ffcc66",
                    stroke_color=initial_stroke_color,
                    altitude=0.3,
                    cap_curvature_resolution=4.0,
                )
            ],
            polygons_transition_duration=0,
        ),
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    _assert_canvas_matches(
        page_session,
        canvas_capture,
        "test_polygon_stroke_color-stroke-ffffff",
        canvas_reference_path,
        canvas_compare_images,
        canvas_save_capture,
        canvas_similarity_threshold,
    )
    widget.update_polygon(polygon_id, stroke_color=updated_stroke_color)
    page_session.wait_for_timeout(100)
    _assert_canvas_matches(
        page_session,
        canvas_capture,
        "test_polygon_stroke_color-stroke-00ffcc",
        canvas_reference_path,
        canvas_compare_images,
        canvas_save_capture,
        canvas_similarity_threshold,
    )


@pytest.mark.usefixtures("solara_test")
def test_polygon_altitude(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    globe_flat_texture_data_url,
) -> None:
    canvas_similarity_threshold = 0.99
    initial_altitude = 0.02
    updated_altitude = 0.12
    polygon_id = uuid4()
    polygon = _polygon(-20, -5, 20, 5)
    config = _make_config(
        globe_flat_texture_data_url,
        PolygonsLayerConfig(
            polygons_data=[
                PolygonDatum(
                    id=polygon_id,
                    geometry=polygon,
                    cap_color="#66ccff",
                    side_color="#66ccff",
                    stroke_color=None,
                    altitude=initial_altitude,
                    cap_curvature_resolution=4.0,
                )
            ],
            polygons_transition_duration=0,
        ),
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    _assert_canvas_matches(
        page_session,
        canvas_capture,
        "test_polygon_altitude-altitude-0_02",
        canvas_reference_path,
        canvas_compare_images,
        canvas_save_capture,
        canvas_similarity_threshold,
    )
    widget.update_polygon(polygon_id, altitude=updated_altitude)
    page_session.wait_for_timeout(100)
    _assert_canvas_matches(
        page_session,
        canvas_capture,
        "test_polygon_altitude-altitude-0_12",
        canvas_reference_path,
        canvas_compare_images,
        canvas_save_capture,
        canvas_similarity_threshold,
    )


@pytest.mark.usefixtures("solara_test")
def test_polygon_cap_curvature_resolution(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.99
    initial_curvature = 2.0
    updated_curvature = 12.0
    polygon_id = uuid4()
    polygon = _circle_polygon(0, 0, 37.5, steps=96)
    config = _make_config(
        globe_flat_texture_data_url,
        PolygonsLayerConfig(
            polygons_data=[
                PolygonDatum(
                    id=polygon_id,
                    geometry=polygon,
                    cap_color="#f7d97b",
                    side_color="#1f3b52",
                    stroke_color=None,
                    altitude=0.06,
                    cap_curvature_resolution=initial_curvature,
                )
            ],
            polygons_transition_duration=0,
        ),
        lat=0,
        lng=75,
        altitude=2.2,
        width=512,
        height=512,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)

    canvas_assert_capture(page_session, "curvature-2", canvas_similarity_threshold)
    widget.update_polygon(polygon_id, cap_curvature_resolution=updated_curvature)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "curvature-12", canvas_similarity_threshold)
