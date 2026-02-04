from __future__ import annotations

from typing import TYPE_CHECKING

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
    RingDatum,
    RingsLayerConfig,
)


if TYPE_CHECKING:
    from playwright.sync_api import Page

_URL_ADAPTER = TypeAdapter(AnyUrl)


def _make_config(rings: RingsLayerConfig, globe_texture_url: str) -> GlobeConfig:
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
        rings=rings,
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.8), transition_ms=0
        ),
    )


def _await_globe_ready(page_session: Page) -> None:
    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )
    page_session.wait_for_timeout(500)


@pytest.mark.usefixtures("solara_test")
def test_rings_accessors(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.96
    rings = [
        RingDatum(
            lat=0,
            lng=0,
            color="#ff0000",
            max_radius=10,
            propagation_speed=0,
            repeat_period=0,
        )
    ]
    updated = [
        RingDatum(
            lat=10,
            lng=10,
            color="#00ccff",
            max_radius=20,
            propagation_speed=0,
            repeat_period=0,
        )
    ]

    config = _make_config(
        RingsLayerConfig(rings_data=rings, ring_resolution=32),
        globe_flat_texture_data_url,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(page_session, "initial", canvas_similarity_threshold)

    widget.set_ring_resolution(96)
    widget.set_rings_data(updated)
    page_session.wait_for_timeout(500)
    canvas_assert_capture(page_session, "updated", canvas_similarity_threshold)
