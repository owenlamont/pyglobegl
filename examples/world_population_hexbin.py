"""World population hexbin demo using frontend MicroPython accessors.

Launch commands:
    uv run solara run examples/world_population_hexbin.py
"""

from __future__ import annotations

import csv
from functools import lru_cache
from io import StringIO
from urllib.request import urlopen

from pydantic import AnyUrl, TypeAdapter
import solara

from pyglobegl import (
    frontend_python,
    GlobeConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeViewConfig,
    GlobeWidget,
    HexBinLayerConfig,
    HexBinPointDatum,
    PointOfView,
)


_DATASET_URL = (
    "https://raw.githubusercontent.com/vasturiano/globe.gl/master/example/"
    "datasets/world_population.csv"
)


@frontend_python
def population_hex_altitude(hexbin: dict) -> float:
    """Return altitude scaled from aggregate hex population."""
    return hexbin["sumWeight"] * 6e-8


@frontend_python
def population_hex_color(hexbin: dict) -> str:
    """Return a YlOrRd color interpolated by sqrt-scaled aggregate population."""
    # Self-contained body so frontend MicroPython has all required symbols.
    palette = (
        (255, 255, 204),
        (255, 237, 160),
        (254, 217, 118),
        (254, 178, 76),
        (253, 141, 60),
        (252, 78, 42),
        (227, 26, 28),
        (189, 0, 38),
        (128, 0, 38),
    )
    weight = float(hexbin["sumWeight"])
    if weight < 0:
        weight = 0.0
    normalized = (weight / 1e7) ** 0.5
    if normalized > 1:
        normalized = 1.0
    scaled = normalized * (len(palette) - 1)
    lower = int(scaled)
    upper = min(len(palette) - 1, lower + 1)
    blend = scaled - lower
    low = palette[lower]
    high = palette[upper]
    r = round(low[0] + (high[0] - low[0]) * blend)
    g = round(low[1] + (high[1] - low[1]) * blend)
    b = round(low[2] + (high[2] - low[2]) * blend)
    return f"#{r:02x}{g:02x}{b:02x}"


def _load_population_points() -> list[HexBinPointDatum]:
    with urlopen(_DATASET_URL, timeout=30) as response:
        csv_text = response.read().decode("utf-8")

    reader = csv.DictReader(StringIO(csv_text))
    return [
        HexBinPointDatum(
            lat=float(row["lat"]), lng=float(row["lng"]), weight=float(row["pop"])
        )
        for row in reader
    ]


@lru_cache(maxsize=1)
def _build_config() -> GlobeConfig:
    return GlobeConfig(
        globe=GlobeLayerConfig(
            globe_image_url=TypeAdapter(AnyUrl).validate_python(
                "https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-night.jpg"
            ),
            bump_image_url=TypeAdapter(AnyUrl).validate_python(
                "https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-topology.png"
            ),
        ),
        layout=GlobeLayoutConfig(
            background_image_url=TypeAdapter(AnyUrl).validate_python(
                "https://cdn.jsdelivr.net/npm/three-globe/example/img/night-sky.png"
            )
        ),
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=2.1),
            controls_auto_rotate=True,
            controls_auto_rotate_speed=0.6,
        ),
        hex_bin=HexBinLayerConfig(
            hex_bin_points_data=_load_population_points(),
            hex_bin_resolution=4,
            hex_altitude=population_hex_altitude,
            hex_top_color=population_hex_color,
            hex_side_color=population_hex_color,
            hex_bin_merge=True,
            hex_transition_duration=0,
        ),
    )


@solara.component
def page():
    """Render the world population hexbin demo.

    Returns:
        The root Solara element.
    """
    with solara.Column() as main:
        solara.display(GlobeWidget(config=_build_config()))
    return main
