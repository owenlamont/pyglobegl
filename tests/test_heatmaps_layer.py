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
    HeatmapDatum,
    HeatmapPointDatum,
    HeatmapsLayerConfig,
    PointOfView,
)


if TYPE_CHECKING:
    from playwright.sync_api import Page

_URL_ADAPTER = TypeAdapter(AnyUrl)


def _make_config(heatmaps: HeatmapsLayerConfig, globe_texture_url: str) -> GlobeConfig:
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
        heatmaps=heatmaps,
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.8), transition_ms=0
        ),
    )


def _await_globe_ready(page_session: Page) -> None:
    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )
    page_session.wait_for_timeout(1500)


def _disable_webgpu(page_session: Page) -> None:
    page_session.evaluate(
        """
        () => {
          try {
            Object.defineProperty(navigator, 'gpu', {
              value: undefined,
              configurable: true
            });
          } catch (error) {
            try {
              navigator.gpu = undefined;
            } catch {
              // ignore
            }
          }
        }
        """
    )


@pytest.mark.usefixtures("solara_test")
def test_heatmaps_accessors(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.97
    heatmaps_data = [
        HeatmapDatum(
            points=[
                HeatmapPointDatum(lat=0, lng=0, weight=5.0),
                HeatmapPointDatum(lat=20, lng=10, weight=3.0),
                HeatmapPointDatum(lat=-25, lng=-15, weight=4.0),
            ],
            bandwidth=8.0,
            color_saturation=10.0,
            base_altitude=0.4,
            top_altitude=0.8,
        )
    ]
    updated_heatmaps = [
        HeatmapDatum(
            points=[
                HeatmapPointDatum(lat=30, lng=-20, weight=6.0),
                HeatmapPointDatum(lat=-15, lng=25, weight=5.5),
            ],
            bandwidth=12.0,
            color_saturation=6.0,
            base_altitude=0.25,
            top_altitude=0.9,
        )
    ]

    config = _make_config(
        HeatmapsLayerConfig(
            heatmaps_data=heatmaps_data, heatmaps_transition_duration=0
        ),
        globe_flat_texture_data_url,
    )
    _disable_webgpu(page_session)
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(page_session, "initial", canvas_similarity_threshold)

    widget.set_heatmaps_data(updated_heatmaps)
    page_session.wait_for_timeout(1500)
    canvas_assert_capture(page_session, "updated", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_heatmap_bandwidth_update(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.97
    heatmap = HeatmapDatum(
        points=[
            HeatmapPointDatum(lat=-5, lng=6, weight=6.0),
            HeatmapPointDatum(lat=10, lng=-12, weight=5.0),
        ],
        bandwidth=6.0,
        color_saturation=12.0,
        base_altitude=0.35,
        top_altitude=0.75,
    )

    config = _make_config(
        HeatmapsLayerConfig(heatmaps_data=[heatmap], heatmaps_transition_duration=0),
        globe_flat_texture_data_url,
    )
    _disable_webgpu(page_session)
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(page_session, "bandwidth-0.6", canvas_similarity_threshold)

    widget.update_heatmap(
        heatmap.id,
        bandwidth=12.0,
        color_saturation=4.0,
        base_altitude=0.2,
        top_altitude=0.5,
    )
    page_session.wait_for_timeout(1500)
    canvas_assert_capture(page_session, "bandwidth-2.4", canvas_similarity_threshold)
