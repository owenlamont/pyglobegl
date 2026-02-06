"""Population heatmap layer demo (globe.gl population-heatmap).

Launch commands:
    uv run solara run examples/population_heatmap.py
"""

from __future__ import annotations

import csv
from functools import lru_cache
from io import StringIO
from urllib.request import urlopen

from pydantic import AnyUrl, TypeAdapter
import solara

from pyglobegl import (
    GlobeConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeViewConfig,
    GlobeWidget,
    HeatmapDatum,
    HeatmapPointDatum,
    HeatmapsLayerConfig,
    PointOfView,
)


_POPULATION_URL = (
    "https://unpkg.com/globe.gl@2.44.1/example/datasets/world_population.csv"
)


@lru_cache(maxsize=1)
def _load_population_heatmap() -> HeatmapDatum:
    with urlopen(_POPULATION_URL) as response:
        csv_text = response.read().decode("utf-8")

    reader = csv.DictReader(StringIO(csv_text))
    points: list[HeatmapPointDatum] = []
    for row in reader:
        lat = row.get("lat")
        lng = row.get("lng")
        pop = row.get("pop")
        if lat is None or lng is None or pop is None:
            continue
        points.append(
            HeatmapPointDatum(lat=float(lat), lng=float(lng), weight=float(pop))
        )

    if not points:
        raise ValueError("Population dataset returned no usable rows.")

    return HeatmapDatum(points=points, bandwidth=0.9, color_saturation=2.8)


config = GlobeConfig(
    layout=GlobeLayoutConfig(background_color="#000000"),
    globe=GlobeLayerConfig(
        globe_image_url=TypeAdapter(AnyUrl).validate_python(
            "https://unpkg.com/three-globe/example/img/earth-night.jpg"
        )
    ),
    heatmaps=HeatmapsLayerConfig(
        heatmaps_data=[_load_population_heatmap()], heatmaps_transition_duration=0
    ),
    view=GlobeViewConfig(point_of_view=PointOfView(lat=0, lng=0, altitude=2.2)),
)


@solara.component
def page():
    """Render the population heatmap demo.

    Returns:
        The root Solara element.
    """
    solara.Style("body { margin: 0; background: #000; }")
    with solara.Column(
        style={"padding": "0", "margin": "0", "width": "100vw", "height": "100vh"}
    ) as main:
        solara.display(GlobeWidget(config=config))
    return main
