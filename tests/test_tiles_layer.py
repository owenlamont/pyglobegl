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
    GlobeMaterialSpec,
    GlobeViewConfig,
    GlobeWidget,
    PointOfView,
    TileDatum,
    TilesLayerConfig,
)


if TYPE_CHECKING:
    from playwright.sync_api import Page

_URL_ADAPTER = TypeAdapter(AnyUrl)


def _make_config(tiles: TilesLayerConfig, globe_texture_url: str) -> GlobeConfig:
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
        tiles=tiles,
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.8), transition_ms=0
        ),
    )


def _await_globe_ready(page_session: Page) -> None:
    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )
    page_session.wait_for_timeout(250)


@pytest.mark.usefixtures("solara_test")
def test_tiles_accessors(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.97
    tiles = [
        TileDatum(
            lat=0,
            lng=0,
            width=60,
            height=30,
            altitude=0.02,
            use_globe_projection=True,
            curvature_resolution=2,
            material=GlobeMaterialSpec(
                type="MeshLambertMaterial",
                params={"color": "#ffcc00", "opacity": 0.6, "transparent": True},
            ),
        )
    ]
    updated = [
        TileDatum(
            lat=10,
            lng=10,
            width=40,
            height=20,
            altitude=0.05,
            use_globe_projection=False,
            curvature_resolution=8,
            material=GlobeMaterialSpec(
                type="MeshLambertMaterial",
                params={"color": "#00ccff", "opacity": 0.85, "transparent": True},
            ),
        )
    ]

    config = _make_config(
        TilesLayerConfig(tiles_data=tiles, tiles_transition_duration=0),
        globe_flat_texture_data_url,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(page_session, "initial", canvas_similarity_threshold)

    widget.set_tiles_data(updated)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "updated", canvas_similarity_threshold)
