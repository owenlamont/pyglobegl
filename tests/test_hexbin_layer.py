from __future__ import annotations

from typing import TYPE_CHECKING

from IPython.display import display
from pydantic import AnyUrl, TypeAdapter
from pydantic_extra_types.color import Color
import pytest

from pyglobegl import (
    frontend_python,
    GlobeConfig,
    GlobeInitConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeViewConfig,
    GlobeWidget,
    HexBinLayerConfig,
    HexBinPointDatum,
    PointOfView,
)


if TYPE_CHECKING:
    from playwright.sync_api import Page

_URL_ADAPTER = TypeAdapter(AnyUrl)


@frontend_python
def _hex_top_color_fn(hexbin):
    weight = float(hexbin["sumWeight"])
    if weight > 18.0:
        return "#ff007f"
    if weight > 10.0:
        return "#ffcc00"
    return "#66ff33"


@frontend_python
def _hex_side_color_fn(hexbin):
    weight = float(hexbin["sumWeight"])
    if weight > 18.0:
        return "#1a0033"
    if weight > 10.0:
        return "#002266"
    return "#004488"


@frontend_python
def _hex_altitude_fn(hexbin):
    return float(hexbin["sumWeight"]) * 0.08


@frontend_python
def _hex_top_color_fn_alt(hexbin):
    weight = float(hexbin["sumWeight"])
    if weight > 18.0:
        return "#00e5ff"
    if weight > 10.0:
        return "#39ff14"
    return "#f5f5f5"


@frontend_python
def _hex_side_color_fn_alt(hexbin):
    weight = float(hexbin["sumWeight"])
    if weight > 18.0:
        return "#003b46"
    if weight > 10.0:
        return "#145214"
    return "#5c5c5c"


@frontend_python
def _hex_altitude_fn_alt(hexbin):
    return float(hexbin["sumWeight"]) * 0.05


def _make_config(hexbin: HexBinLayerConfig, globe_texture_url: str) -> GlobeConfig:
    return GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#000000"),
        globe=GlobeLayerConfig(
            globe_image_url=_URL_ADAPTER.validate_python(globe_texture_url),
            show_atmosphere=False,
            show_graticules=False,
        ),
        hex_bin=hexbin,
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.6), transition_ms=0
        ),
    )


def _await_globe_ready(page_session: Page) -> None:
    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )
    page_session.wait_for_timeout(250)


@pytest.mark.usefixtures("solara_test")
def test_hexbin_accessors(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.97
    points = [
        HexBinPointDatum(lat=8, lng=0, weight=10.0),
        HexBinPointDatum(lat=10, lng=2, weight=9.0),
        HexBinPointDatum(lat=2, lng=22, weight=7.0),
        HexBinPointDatum(lat=4, lng=24, weight=6.0),
        HexBinPointDatum(lat=-10, lng=-20, weight=4.5),
        HexBinPointDatum(lat=-8, lng=-18, weight=4.0),
    ]
    updated_points = [
        HexBinPointDatum(lat=14, lng=-6, weight=11.0),
        HexBinPointDatum(lat=16, lng=-4, weight=10.0),
        HexBinPointDatum(lat=-2, lng=30, weight=8.0),
        HexBinPointDatum(lat=0, lng=32, weight=7.0),
        HexBinPointDatum(lat=-16, lng=-28, weight=6.0),
        HexBinPointDatum(lat=-14, lng=-26, weight=5.5),
    ]

    config = _make_config(
        HexBinLayerConfig(
            hex_bin_points_data=points,
            hex_bin_resolution=1,
            hex_margin=0.03,
            hex_top_color="#ffe066",
            hex_side_color="#1b4d8f",
            hex_altitude=0.18,
            hex_transition_duration=0,
        ),
        globe_flat_texture_data_url,
    )
    config = config.model_copy(
        update={
            "view": GlobeViewConfig(
                point_of_view=PointOfView(lat=0, lng=0, altitude=2.0), transition_ms=0
            )
        }
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(page_session, "initial", canvas_similarity_threshold)

    widget.set_hex_bin_points_data(updated_points)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "updated", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_hexbin_config_updates(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.96
    points = [
        HexBinPointDatum(lat=10, lng=0, weight=12.0),
        HexBinPointDatum(lat=12, lng=2, weight=11.0),
        HexBinPointDatum(lat=0, lng=24, weight=8.0),
        HexBinPointDatum(lat=2, lng=26, weight=7.0),
        HexBinPointDatum(lat=-12, lng=-22, weight=5.0),
        HexBinPointDatum(lat=-10, lng=-20, weight=4.0),
    ]

    config = _make_config(
        HexBinLayerConfig(
            hex_bin_points_data=points,
            hex_bin_resolution=1,
            hex_margin=0.03,
            hex_top_color="#ffcc00",
            hex_side_color="#3a146b",
            hex_altitude=0.16,
            hex_transition_duration=0,
        ),
        globe_flat_texture_data_url,
    )
    config = config.model_copy(
        update={
            "view": GlobeViewConfig(
                point_of_view=PointOfView(lat=0, lng=0, altitude=2.0), transition_ms=0
            )
        }
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(page_session, "initial", canvas_similarity_threshold)

    widget.set_hex_bin_resolution(1)
    widget.set_hex_margin(0.02)
    widget.set_hex_top_color(Color("#00ff99"))
    widget.set_hex_side_color(Color("#0044ff"))
    widget.set_hex_altitude(0.18)
    widget.set_hex_bin_merge(True)
    assert widget.get_hex_margin() == pytest.approx(0.02)
    assert widget.get_hex_top_color() in {"#00ff99", "#0f9"}
    assert widget.get_hex_side_color() in {"#0044ff", "#04f"}
    assert widget.get_hex_altitude() == pytest.approx(0.18)
    assert widget.get_hex_bin_merge() is True
    page_session.wait_for_timeout(200)
    canvas_assert_capture(page_session, "updated", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_hexbin_frontend_python_accessors(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.96
    # Three front-facing, spatially separated clusters to exercise all branches:
    # - high (>18), medium (>10), and low (<=10) aggregate weights.
    points = [
        HexBinPointDatum(lat=8, lng=0, weight=11.0),
        HexBinPointDatum(lat=10, lng=2, weight=10.0),
        HexBinPointDatum(lat=2, lng=24, weight=6.0),
        HexBinPointDatum(lat=4, lng=26, weight=5.5),
        HexBinPointDatum(lat=-10, lng=-24, weight=2.0),
        HexBinPointDatum(lat=-8, lng=-22, weight=2.0),
    ]

    config = _make_config(
        HexBinLayerConfig(
            hex_bin_points_data=points,
            hex_bin_resolution=2,
            hex_margin=0.05,
            hex_top_color=_hex_top_color_fn,
            hex_side_color=_hex_side_color_fn,
            hex_altitude=_hex_altitude_fn,
            hex_transition_duration=0,
        ),
        globe_flat_texture_data_url,
    )
    config = config.model_copy(
        update={
            "view": GlobeViewConfig(
                point_of_view=PointOfView(lat=0, lng=0, altitude=2.1), transition_ms=0
            )
        }
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(
        page_session, "frontend-python-initial", canvas_similarity_threshold
    )

    widget.set_hex_top_color(_hex_top_color_fn_alt)
    widget.set_hex_side_color(_hex_side_color_fn_alt)
    widget.set_hex_altitude(_hex_altitude_fn_alt)
    assert widget.get_hex_top_color() is not None
    assert widget.get_hex_side_color() is not None
    assert widget.get_hex_altitude() is not None
    page_session.wait_for_timeout(120)
    canvas_assert_capture(
        page_session, "frontend-python-updated", canvas_similarity_threshold
    )


@pytest.mark.usefixtures("solara_test")
def test_hexbin_frontend_python_point_accessors(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.96
    points = [
        HexBinPointDatum(lat=14, lng=-12, weight=1.0),
        HexBinPointDatum(lat=13, lng=-8, weight=1.0),
        HexBinPointDatum(lat=10, lng=-4, weight=1.0),
        HexBinPointDatum(lat=7, lng=0, weight=1.0),
        HexBinPointDatum(lat=4, lng=4, weight=1.0),
        HexBinPointDatum(lat=1, lng=8, weight=1.0),
        HexBinPointDatum(lat=-2, lng=12, weight=1.0),
        HexBinPointDatum(lat=-5, lng=16, weight=1.0),
    ]

    config = _make_config(
        HexBinLayerConfig(
            hex_bin_points_data=points,
            hex_bin_resolution=1,
            hex_bin_point_weight=6.0,
            hex_margin=0.02,
            hex_top_color="#ff006e",
            hex_side_color="#ffd166",
            hex_altitude=0.24,
            hex_transition_duration=0,
        ),
        globe_flat_texture_data_url,
    )
    config = config.model_copy(
        update={
            "view": GlobeViewConfig(
                point_of_view=PointOfView(lat=6, lng=2, altitude=2.0), transition_ms=0
            )
        }
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(
        page_session, "point-accessors-initial", canvas_similarity_threshold
    )

    widget.set_hex_bin_point_weight(0.2)
    widget.set_hex_margin(0.34)
    widget.set_hex_top_color(Color("#00e5ff"))
    widget.set_hex_side_color(Color("#003049"))
    widget.set_hex_altitude(0.05)
    assert widget.get_hex_bin_point_weight() == pytest.approx(0.2)
    assert widget.get_hex_margin() == pytest.approx(0.34)
    page_session.wait_for_timeout(150)
    canvas_assert_capture(
        page_session, "point-accessors-updated", canvas_similarity_threshold
    )


@pytest.mark.usefixtures("solara_test")
def test_hexbin_top_curvature_resolution(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.96
    points = [
        HexBinPointDatum(lat=3.0, lng=-2.0, weight=14.0),
        HexBinPointDatum(lat=2.5, lng=-1.5, weight=14.0),
        HexBinPointDatum(lat=2.0, lng=-1.0, weight=14.0),
        HexBinPointDatum(lat=1.5, lng=-0.5, weight=14.0),
        HexBinPointDatum(lat=1.0, lng=0.0, weight=14.0),
        HexBinPointDatum(lat=0.5, lng=0.5, weight=14.0),
        HexBinPointDatum(lat=0.0, lng=1.0, weight=14.0),
        HexBinPointDatum(lat=-0.5, lng=1.5, weight=14.0),
    ]

    config = _make_config(
        HexBinLayerConfig(
            hex_bin_points_data=points,
            hex_bin_resolution=0,
            hex_margin=0.01,
            hex_top_color="#ff4d6d",
            hex_side_color="#2d1e2f",
            hex_altitude=0.24,
            hex_top_curvature_resolution=180.0,
            hex_transition_duration=0,
        ),
        globe_flat_texture_data_url,
    )
    config = config.model_copy(
        update={
            "view": GlobeViewConfig(
                point_of_view=PointOfView(lat=1, lng=62, altitude=2.4), transition_ms=0
            )
        }
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(
        page_session, "curvature-initial", canvas_similarity_threshold
    )

    widget.set_hex_top_curvature_resolution(0.25)
    assert widget.get_hex_top_curvature_resolution() == pytest.approx(0.25)
    page_session.wait_for_timeout(150)
    canvas_assert_capture(
        page_session, "curvature-updated", canvas_similarity_threshold
    )
