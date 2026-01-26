"""Basic points layer demo.

Launch commands:
    uv run solara run examples/points_basic.py
"""

from __future__ import annotations

import random

from pydantic import AnyUrl, TypeAdapter
import solara

from pyglobegl import (
    GlobeConfig,
    GlobeLayerConfig,
    GlobeWidget,
    PointDatum,
    PointsLayerConfig,
)


def _make_points(count: int = 300) -> list[PointDatum]:
    colors = ["red", "white", "blue", "green"]
    return [
        PointDatum(
            lat=(random.random() - 0.5) * 180,  # noqa: S311
            lng=(random.random() - 0.5) * 360,  # noqa: S311
            altitude=random.random() / 3,  # noqa: S311
            color=random.choice(colors),  # noqa: S311
        )
        for _ in range(count)
    ]


config = GlobeConfig(
    globe=GlobeLayerConfig(
        globe_image_url=TypeAdapter(AnyUrl).validate_python(
            "https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-night.jpg"
        )
    ),
    points=PointsLayerConfig(points_data=_make_points()),
)


@solara.component
def page():
    """Render the points layer demo.

    Returns:
        The root Solara element.
    """
    with solara.Column() as main:
        solara.display(GlobeWidget(config=config))
    return main
