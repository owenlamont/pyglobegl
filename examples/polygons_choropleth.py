"""Choropleth polygons demo.

Launch commands:
    uv run solara run examples/polygons_choropleth.py
"""

from __future__ import annotations

from functools import lru_cache
import json
from typing import Any
from urllib.request import urlopen

from pydantic import AnyUrl, TypeAdapter
import solara

from pyglobegl import (
    GlobeConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeWidget,
    PolygonsLayerConfig,
)


_COUNTRIES_URL = (
    "https://raw.githubusercontent.com/vasturiano/globe.gl/"
    "master/example/datasets/ne_110m_admin_0_countries.geojson"
)


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def _interpolate_color(
    start: tuple[int, int, int], end: tuple[int, int, int], t: float
) -> str:
    t = max(0.0, min(1.0, t))
    return _rgb_to_hex(
        (
            round(start[0] + (end[0] - start[0]) * t),
            round(start[1] + (end[1] - start[1]) * t),
            round(start[2] + (end[2] - start[2]) * t),
        )
    )


@lru_cache(maxsize=1)
def _load_countries() -> list[dict[str, Any]]:
    with urlopen(_COUNTRIES_URL) as response:
        data = json.load(response)

    features = [
        feat
        for feat in data.get("features", [])
        if feat.get("properties", {}).get("ISO_A2") != "AQ"
    ]
    if not features:
        raise ValueError("No country features loaded from GeoJSON.")

    def _value(feat: dict[str, Any]) -> float:
        props = feat.get("properties", {})
        gdp = float(props.get("GDP_MD_EST") or 0.0)
        pop = float(props.get("POP_EST") or 0.0)
        return gdp / max(1e5, pop)

    values = [_value(feat) for feat in features]
    max_val = max(values) if values else 1.0

    start = (255, 255, 102)
    end = (128, 0, 0)
    for feat, val in zip(features, values, strict=False):
        t = val / max_val if max_val else 0.0
        props = feat.setdefault("properties", {})
        feat["color"] = _interpolate_color(start, end, t)
        feat["stroke_color"] = "#111111"
        feat["side_color"] = "rgba(0, 100, 0, 0.15)"
        feat["label"] = (
            f"<b>{props.get('ADMIN', 'Unknown')}</b> "
            f"({props.get('ISO_A2', '--')}):<br/>"
            f"GDP: <i>{props.get('GDP_MD_EST', 'N/A')}</i> M$<br/>"
            f"Population: <i>{props.get('POP_EST', 'N/A')}</i>"
        )

    return features


config = GlobeConfig(
    layout=GlobeLayoutConfig(
        background_color="#000000",
        background_image_url=TypeAdapter(AnyUrl).validate_python(
            "https://cdn.jsdelivr.net/npm/three-globe/example/img/night-sky.png"
        ),
    ),
    globe=GlobeLayerConfig(
        globe_image_url=TypeAdapter(AnyUrl).validate_python(
            "https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-night.jpg"
        ),
        show_atmosphere=False,
        show_graticules=False,
    ),
    polygons=PolygonsLayerConfig(
        polygons_data=_load_countries(),
        polygon_geojson_geometry="geometry",
        polygon_cap_color="color",
        polygon_side_color="side_color",
        polygon_stroke_color="stroke_color",
        polygon_label="label",
        polygon_altitude=0.06,
        polygons_transition_duration=300,
    ),
)


@solara.component
def page():
    """Render the polygons choropleth demo.

    Returns:
        The root Solara element.
    """
    with solara.Column() as main:
        solara.display(GlobeWidget(config=config))
    return main
