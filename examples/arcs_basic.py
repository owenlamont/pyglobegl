"""Basic arcs layer demo.

Launch commands:
    uv run solara run examples/arcs_basic.py
"""

from __future__ import annotations

import random

from pydantic import AnyUrl, TypeAdapter
import solara

from pyglobegl import (
    ArcDatum,
    ArcsLayerConfig,
    GlobeConfig,
    GlobeLayerConfig,
    GlobeWidget,
)


def _make_arcs(count: int = 120) -> list[ArcDatum]:
    colors = ["#ff6b6b", "#ffd93d", "#4dabf7", "#69db7c"]
    arcs: list[ArcDatum] = []
    for index in range(count):
        start_lat = (random.random() - 0.5) * 180  # noqa: S311
        start_lng = (random.random() - 0.5) * 360  # noqa: S311
        end_lat = (random.random() - 0.5) * 180  # noqa: S311
        end_lng = (random.random() - 0.5) * 360  # noqa: S311
        arcs.append(
            ArcDatum(
                start_lat=start_lat,
                start_lng=start_lng,
                end_lat=end_lat,
                end_lng=end_lng,
                altitude=random.random() * 0.4 + 0.1,  # noqa: S311
                color=random.choice(colors),  # noqa: S311
                label=f"Arc {index + 1}",
                stroke=0.6,
            )
        )
    return arcs


config = GlobeConfig(
    globe=GlobeLayerConfig(
        globe_image_url=TypeAdapter(AnyUrl).validate_python(
            "https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-night.jpg"
        )
    ),
    arcs=ArcsLayerConfig(arcs_data=_make_arcs()),
)


@solara.component
def page():
    """Render the arcs layer demo.

    Returns:
        The root Solara element.
    """
    with solara.Column() as main:
        solara.display(GlobeWidget(config=config))
    return main
