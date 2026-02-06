"""World cities labels demo (globe.gl world-cities).

Launch commands:
    uv run solara run examples/world_cities.py
"""

from __future__ import annotations

from functools import lru_cache
import json
import math
from urllib.request import urlopen

from pydantic import AnyUrl, TypeAdapter
import solara

from pyglobegl import (
    GlobeConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeViewConfig,
    GlobeWidget,
    LabelDatum,
    LabelsLayerConfig,
    PointOfView,
)


_PLACES_URL = (
    "https://unpkg.com/globe.gl@2.18.2/example/datasets/"
    "ne_110m_populated_places_simple.geojson"
)


@lru_cache(maxsize=1)
def _load_labels() -> list[LabelDatum]:
    with urlopen(_PLACES_URL) as response:
        data = json.load(response)

    labels: list[LabelDatum] = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        lat = props.get("latitude")
        lng = props.get("longitude")
        name = props.get("name")
        pop_max = props.get("pop_max")
        if lat is None or lng is None or name is None or pop_max is None:
            continue
        scale = math.sqrt(float(pop_max)) * 4e-4
        labels.append(
            LabelDatum(
                lat=float(lat),
                lng=float(lng),
                text=str(name),
                size=scale,
                dot_radius=scale,
                color="rgba(255, 165, 0, 0.75)",
            )
        )

    if not labels:
        raise ValueError("World cities dataset returned no usable rows.")

    return labels


config = GlobeConfig(
    layout=GlobeLayoutConfig(
        background_image_url=TypeAdapter(AnyUrl).validate_python(
            "https://unpkg.com/three-globe/example/img/night-sky.png"
        ),
        background_color="#000000",
    ),
    globe=GlobeLayerConfig(
        globe_image_url=TypeAdapter(AnyUrl).validate_python(
            "https://unpkg.com/three-globe/example/img/earth-night.jpg"
        )
    ),
    labels=LabelsLayerConfig(labels_data=_load_labels(), label_resolution=2),
    view=GlobeViewConfig(point_of_view=PointOfView(lat=0, lng=0, altitude=2.2)),
)


@solara.component
def page():
    """Render the world cities labels demo.

    Returns:
        The root Solara element.
    """
    solara.Style("body { margin: 0; background: #000; }")
    with solara.Column(
        style={"padding": "0", "margin": "0", "width": "100vw", "height": "100vh"}
    ) as main:
        solara.display(GlobeWidget(config=config))
    return main
