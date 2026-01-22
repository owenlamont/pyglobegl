"""Basic arcs layer demo.

Launch commands:
    uv run solara run examples/arcs_basic.py
"""

from __future__ import annotations

import random
from typing import Any

from pydantic import AnyUrl, TypeAdapter
import solara

from pyglobegl import ArcsLayerConfig, GlobeConfig, GlobeLayerConfig, GlobeWidget


def _make_arcs(count: int = 120) -> list[dict[str, Any]]:
    colors = ["#ff6b6b", "#ffd93d", "#4dabf7", "#69db7c"]
    arcs: list[dict[str, Any]] = []
    for _ in range(count):
        start_lat = (random.random() - 0.5) * 180  # noqa: S311
        start_lng = (random.random() - 0.5) * 360  # noqa: S311
        end_lat = (random.random() - 0.5) * 180  # noqa: S311
        end_lng = (random.random() - 0.5) * 360  # noqa: S311
        arcs.append(
            {
                "startLat": start_lat,
                "startLng": start_lng,
                "endLat": end_lat,
                "endLng": end_lng,
                "alt": random.random() * 0.4 + 0.1,  # noqa: S311
                "color": random.choice(colors),  # noqa: S311
            }
        )
    return arcs


config = GlobeConfig(
    globe=GlobeLayerConfig(
        globe_image_url=TypeAdapter(AnyUrl).validate_python(
            "https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-night.jpg"
        )
    ),
    arcs=ArcsLayerConfig(
        arcs_data=_make_arcs(),
        arc_start_lat="startLat",
        arc_start_lng="startLng",
        arc_end_lat="endLat",
        arc_end_lng="endLng",
        arc_altitude="alt",
        arc_color="color",
        arc_stroke=0.6,
    ),
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
