from __future__ import annotations

from typing import TYPE_CHECKING

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
    return Polygon(
        type="Polygon", coordinates=_polygon_coords(west, south, east, north)
    )


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
        raise AssertionError(
            f"Reference image missing. Save the capture to {reference_path} and re-run."
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
    canvas_label,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_flat_texture_data_url,
) -> None:
    polygons_data = [
        {
            "geom": _polygon(-25, -5, -5, 10),
            "cap_color": "#ff66cc",
            "side_color": "#ff66cc",
            "stroke_color": None,
            "altitude": 0.05,
            "cap_resolution": 0.5,
        },
        {
            "geom": _polygon(5, -5, 25, 10),
            "cap_color": "#66ccff",
            "side_color": "#66ccff",
            "stroke_color": None,
            "altitude": 0.05,
            "cap_resolution": 1.0,
        },
    ]

    config = _make_config(
        globe_flat_texture_data_url,
        PolygonsLayerConfig(
            polygons_data=polygons_data,
            polygon_geojson_geometry="geom",
            polygon_cap_color="cap_color",
            polygon_side_color="side_color",
            polygon_stroke_color="stroke_color",
            polygon_altitude="altitude",
            polygon_cap_curvature_resolution="cap_resolution",
            polygons_transition_duration=0,
        ),
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    _assert_canvas_matches(
        page_session,
        canvas_capture,
        canvas_label,
        canvas_reference_path,
        canvas_compare_images,
        canvas_save_capture,
        canvas_similarity_threshold,
    )


@pytest.mark.usefixtures("solara_test")
@pytest.mark.parametrize(
    "cap_color",
    [
        pytest.param("#ff66cc", id="cap-ff66cc"),
        pytest.param("#66ccff", id="cap-66ccff"),
    ],
)
def test_polygon_cap_color(
    page_session: Page,
    cap_color: str,
    canvas_capture,
    canvas_label,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_flat_texture_data_url,
) -> None:
    polygon = _polygon(-20, -5, 20, 5)
    config = _make_config(
        globe_flat_texture_data_url,
        PolygonsLayerConfig(
            polygons_data=[
                PolygonDatum(
                    geometry=polygon,
                    cap_color=cap_color,
                    side_color=cap_color,
                    stroke_color=None,
                    altitude=0.3,
                )
            ],
            polygon_cap_color="cap_color",
            polygon_side_color="side_color",
            polygon_stroke_color="stroke_color",
            polygon_altitude="altitude",
            polygon_cap_curvature_resolution=4.0,
            polygons_transition_duration=0,
        ),
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    _assert_canvas_matches(
        page_session,
        canvas_capture,
        canvas_label,
        canvas_reference_path,
        canvas_compare_images,
        canvas_save_capture,
        canvas_similarity_threshold,
    )


@pytest.mark.usefixtures("solara_test")
@pytest.mark.parametrize(
    "side_color",
    [
        pytest.param("#66ccff", id="side-66ccff"),
        pytest.param("#ffcc66", id="side-ffcc66"),
    ],
)
def test_polygon_side_color(
    page_session: Page,
    side_color: str,
    canvas_capture,
    canvas_label,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_flat_texture_data_url,
) -> None:
    polygon = _polygon(-15, 5, 15, 20)
    config = _make_config(
        globe_flat_texture_data_url,
        PolygonsLayerConfig(
            polygons_data=[
                PolygonDatum(
                    geometry=polygon,
                    cap_color="#f0f0f0",
                    side_color=side_color,
                    stroke_color=None,
                    altitude=0.4,
                )
            ],
            polygon_cap_color="cap_color",
            polygon_side_color="side_color",
            polygon_stroke_color="stroke_color",
            polygon_altitude="altitude",
            polygon_cap_curvature_resolution=4.0,
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
        canvas_label,
        canvas_reference_path,
        canvas_compare_images,
        canvas_save_capture,
        canvas_similarity_threshold,
    )


@pytest.mark.usefixtures("solara_test")
@pytest.mark.parametrize(
    "stroke_color",
    [
        pytest.param("#ffffff", id="stroke-ffffff"),
        pytest.param("#00ffcc", id="stroke-00ffcc"),
    ],
)
def test_polygon_stroke_color(
    page_session: Page,
    stroke_color: str,
    canvas_capture,
    canvas_label,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_flat_texture_data_url,
) -> None:
    polygon = _polygon(-20, -5, 20, 5)
    config = _make_config(
        globe_flat_texture_data_url,
        PolygonsLayerConfig(
            polygons_data=[
                PolygonDatum(
                    geometry=polygon,
                    cap_color="#ffcc66",
                    side_color="#ffcc66",
                    stroke_color=stroke_color,
                    altitude=0.3,
                )
            ],
            polygon_cap_color="cap_color",
            polygon_side_color="side_color",
            polygon_stroke_color="stroke_color",
            polygon_altitude="altitude",
            polygon_cap_curvature_resolution=4.0,
            polygons_transition_duration=0,
        ),
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    _assert_canvas_matches(
        page_session,
        canvas_capture,
        canvas_label,
        canvas_reference_path,
        canvas_compare_images,
        canvas_save_capture,
        canvas_similarity_threshold,
    )


@pytest.mark.usefixtures("solara_test")
@pytest.mark.parametrize(
    "altitude",
    [pytest.param(0.02, id="altitude-0_02"), pytest.param(0.12, id="altitude-0_12")],
)
def test_polygon_altitude(
    page_session: Page,
    altitude: float,
    canvas_capture,
    canvas_label,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_flat_texture_data_url,
) -> None:
    polygon = _polygon(-20, -5, 20, 5)
    config = _make_config(
        globe_flat_texture_data_url,
        PolygonsLayerConfig(
            polygons_data=[
                PolygonDatum(
                    geometry=polygon,
                    cap_color="#66ccff",
                    side_color="#66ccff",
                    stroke_color=None,
                    altitude=altitude,
                )
            ],
            polygon_cap_color="cap_color",
            polygon_side_color="side_color",
            polygon_stroke_color="stroke_color",
            polygon_altitude="altitude",
            polygon_cap_curvature_resolution=4.0,
            polygons_transition_duration=0,
        ),
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    _assert_canvas_matches(
        page_session,
        canvas_capture,
        canvas_label,
        canvas_reference_path,
        canvas_compare_images,
        canvas_save_capture,
        canvas_similarity_threshold,
    )


@pytest.mark.usefixtures("solara_test")
@pytest.mark.parametrize(
    ("curvature", "label"),
    [
        pytest.param(1.0, "curvature-1", id="curvature-1"),
        pytest.param(20.0, "curvature-20", id="curvature-20"),
    ],
)
def test_polygon_cap_curvature_resolution(
    page_session: Page,
    curvature: float,
    label: str,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    canvas_similarity_threshold,
    globe_flat_texture_data_url,
) -> None:
    polygon = _polygon(-60, -15, 60, 15)
    config = _make_config(
        globe_flat_texture_data_url,
        PolygonsLayerConfig(
            polygons_data=[
                PolygonDatum(
                    geometry=polygon,
                    cap_color="#ffcc66",
                    side_color="#ffcc66",
                    stroke_color=None,
                    altitude=0.2,
                )
            ],
            polygon_cap_color="cap_color",
            polygon_side_color="side_color",
            polygon_stroke_color="stroke_color",
            polygon_altitude="altitude",
            polygon_cap_curvature_resolution=curvature,
            polygons_transition_duration=0,
        ),
        lat=0,
        altitude=1.1,
        width=512,
        height=512,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    captured = canvas_capture(page_session)
    reference_path = canvas_reference_path(
        f"test_polygon_cap_curvature_resolution-{label}"
    )
    if not reference_path.exists():
        canvas_save_capture(
            captured, f"test_polygon_cap_curvature_resolution-{label}", False
        )
        raise AssertionError(
            f"Reference image missing. Save the capture to {reference_path} and re-run."
        )
    score = canvas_compare_images(captured, reference_path)
    passed = score >= canvas_similarity_threshold
    canvas_save_capture(
        captured, f"test_polygon_cap_curvature_resolution-{label}", passed
    )
    assert passed, (
        "Captured image similarity below threshold. "
        f"Score: {score:.4f} (threshold {canvas_similarity_threshold:.4f})."
    )
