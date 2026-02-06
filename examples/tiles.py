"""Tiles layer demo (globe.gl tiles).

Launch commands:
    uv run solara run examples/tiles.py
"""

from __future__ import annotations

import random

import solara

from pyglobegl import (
    GlobeConfig,
    GlobeLayoutConfig,
    GlobeMaterialSpec,
    GlobeViewConfig,
    GlobeWidget,
    PointOfView,
    TileDatum,
    TilesLayerConfig,
)


_TILE_MARGIN = 0.35
_GRID_SIZE = (60, 20)
_COLORS = [
    "red",
    "green",
    "yellow",
    "blue",
    "orange",
    "pink",
    "brown",
    "purple",
    "magenta",
]


def _make_tiles(seed: int = 13) -> list[TileDatum]:
    rng = random.Random(seed)  # noqa: S311
    tile_width = 360 / _GRID_SIZE[0]
    tile_height = 180 / _GRID_SIZE[1]
    width = tile_width - _TILE_MARGIN
    height = tile_height - _TILE_MARGIN

    tiles: list[TileDatum] = []
    for lng_idx in range(_GRID_SIZE[0]):
        for lat_idx in range(_GRID_SIZE[1]):
            color = rng.choice(_COLORS)
            material = GlobeMaterialSpec(
                type="MeshLambertMaterial",
                params={"color": color, "opacity": 0.6, "transparent": True},
            )
            tiles.append(
                TileDatum(
                    lng=-180 + lng_idx * tile_width,
                    lat=-90 + (lat_idx + 0.5) * tile_height,
                    width=width,
                    height=height,
                    material=material,
                )
            )
    return tiles


config = GlobeConfig(
    layout=GlobeLayoutConfig(background_color="#000000"),
    tiles=TilesLayerConfig(tiles_data=_make_tiles()),
    view=GlobeViewConfig(point_of_view=PointOfView(lat=0, lng=0, altitude=2.2)),
)


@solara.component
def page():
    """Render the tiles layer demo.

    Returns:
        The root Solara element.
    """
    solara.Style("body { margin: 0; background: #000; }")
    with solara.Column(
        style={"padding": "0", "margin": "0", "width": "100vw", "height": "100vh"}
    ) as main:
        solara.display(GlobeWidget(config=config))
    return main
