"""Rings layer demo (globe.gl random-rings).

Launch commands:
    uv run solara run examples/random_rings.py
"""

from __future__ import annotations

import random

from pydantic import AnyUrl, TypeAdapter
import solara

from pyglobegl import (
    GlobeConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeViewConfig,
    GlobeWidget,
    PointOfView,
    RingDatum,
    RingsLayerConfig,
)


def _make_rings(seed: int = 11, count: int = 10) -> list[RingDatum]:
    rng = random.Random(seed)  # noqa: S311
    colors = ["rgba(255,100,50,1)", "rgba(255,100,50,0)"]
    return [
        RingDatum(
            lat=(rng.random() - 0.5) * 180,
            lng=(rng.random() - 0.5) * 360,
            color=colors,
            max_radius=rng.random() * 20 + 3,
            propagation_speed=(rng.random() - 0.5) * 20 + 1,
            repeat_period=rng.random() * 2000 + 200,
        )
        for _ in range(count)
    ]


config = GlobeConfig(
    layout=GlobeLayoutConfig(background_color="#000000"),
    globe=GlobeLayerConfig(
        globe_image_url=TypeAdapter(AnyUrl).validate_python(
            "https://unpkg.com/three-globe/example/img/earth-dark.jpg"
        ),
        bump_image_url=TypeAdapter(AnyUrl).validate_python(
            "https://unpkg.com/three-globe/example/img/earth-topology.png"
        ),
    ),
    rings=RingsLayerConfig(rings_data=_make_rings()),
    view=GlobeViewConfig(point_of_view=PointOfView(lat=0, lng=0, altitude=2.2)),
)


@solara.component
def page():
    """Render the rings layer demo.

    Returns:
        The root Solara element.
    """
    solara.Style("body { margin: 0; background: #000; }")
    with solara.Column(
        style={"padding": "0", "margin": "0", "width": "100vw", "height": "100vh"}
    ) as main:
        solara.display(GlobeWidget(config=config))
    return main
