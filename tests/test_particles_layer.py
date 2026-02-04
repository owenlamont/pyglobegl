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
    ParticleDatum,
    ParticlePointDatum,
    ParticlesLayerConfig,
    PointOfView,
)


if TYPE_CHECKING:
    from playwright.sync_api import Page

_URL_ADAPTER = TypeAdapter(AnyUrl)


def _make_config(
    particles: ParticlesLayerConfig, globe_texture_url: str
) -> GlobeConfig:
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
        particles=particles,
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
def test_particles_accessors(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.97
    particles = [
        ParticleDatum(
            particles=[
                ParticlePointDatum(lat=0, lng=0, altitude=0.18),
                ParticlePointDatum(lat=12, lng=10, altitude=0.18),
                ParticlePointDatum(lat=-12, lng=-10, altitude=0.18),
                ParticlePointDatum(lat=20, lng=-14, altitude=0.2),
                ParticlePointDatum(lat=-20, lng=14, altitude=0.2),
            ],
            size=18.0,
            size_attenuation=False,
            color="#ff3333",
        )
    ]
    updated = [
        ParticleDatum(
            particles=[
                ParticlePointDatum(lat=28, lng=-18, altitude=0.22),
                ParticlePointDatum(lat=26, lng=20, altitude=0.22),
                ParticlePointDatum(lat=-20, lng=26, altitude=0.22),
                ParticlePointDatum(lat=-26, lng=-24, altitude=0.22),
            ],
            size=20.0,
            size_attenuation=False,
            color="#00ccff",
        )
    ]

    config = _make_config(
        ParticlesLayerConfig(particles_data=particles), globe_flat_texture_data_url
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(page_session, "initial", canvas_similarity_threshold)

    widget.set_particles_data(updated)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "updated", canvas_similarity_threshold)
