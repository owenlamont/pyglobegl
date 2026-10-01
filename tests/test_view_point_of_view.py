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
)


if TYPE_CHECKING:
    from playwright.sync_api import Page


@pytest.mark.parametrize(
    ("pov", "expected_altitude"),
    [
        pytest.param(
            PointOfView(lat=0, lng=-90, altitude=1.2), 1.2, id="pov-lat0-lng-90-alt1.2"
        ),
        pytest.param(
            PointOfView(lat=0, lng=-90, altitude=1.4), 1.4, id="pov-lat0-lng-90-alt1.4"
        ),
        pytest.param(
            PointOfView(lat=45, lng=90, altitude=1.4), 1.4, id="pov-lat45-lng90-alt1.4"
        ),
    ],
)
@pytest.mark.usefixtures("solara_test")
def test_view_point_of_view(
    page_session: Page,
    canvas_label,
    canvas_match_reference,
    globe_earth_texture_url,
    pov,
    expected_altitude,
) -> None:
    config = GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#ff00ff"),
        view=GlobeViewConfig(point_of_view=pov),
        globe=GlobeLayerConfig(
            globe_image_url=globe_earth_texture_url,
            show_atmosphere=False,
            show_graticules=False,
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
        (
            "expected => window.__pyglobegl_pov && "
            "Math.abs(window.__pyglobegl_pov.altitude - expected) < 0.001"
        ),
        arg=expected_altitude,
        timeout=20000,
    )

    canvas_match_reference(page_session, canvas_label, 0.99)
