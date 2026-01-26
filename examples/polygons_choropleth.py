"""Choropleth polygons demo.

Launch commands:
    uv run solara run examples/polygons_choropleth.py
"""

from __future__ import annotations

from functools import lru_cache
import json
import math
from typing import Any
from urllib.request import urlopen
from uuid import uuid4

from geojson_pydantic import MultiPolygon, Polygon
from pydantic import AnyUrl, TypeAdapter
import solara

from pyglobegl import (
    GlobeConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeWidget,
    PolygonDatum,
    PolygonsLayerConfig,
)


_COUNTRIES_URL = (
    "https://raw.githubusercontent.com/vasturiano/globe.gl/"
    "master/example/datasets/ne_110m_admin_0_countries.geojson"
)


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


_YLORRD_STOPS: list[tuple[int, int, int]] = [
    (255, 255, 204),
    (255, 237, 160),
    (254, 217, 118),
    (254, 178, 76),
    (253, 141, 60),
    (252, 78, 42),
    (227, 26, 28),
    (189, 0, 38),
    (128, 0, 38),
]


def _interpolate_color(
    start: tuple[int, int, int], end: tuple[int, int, int], t: float
) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        round(start[0] + (end[0] - start[0]) * t),
        round(start[1] + (end[1] - start[1]) * t),
        round(start[2] + (end[2] - start[2]) * t),
    )


def _interpolate_scale(stops: list[tuple[int, int, int]], t: float) -> str:
    t = max(0.0, min(1.0, t))
    if len(stops) == 1:
        return _rgb_to_hex(stops[0])
    scaled = t * (len(stops) - 1)
    index = math.floor(scaled)
    if index >= len(stops) - 1:
        return _rgb_to_hex(stops[-1])
    local_t = scaled - index
    return _rgb_to_hex(_interpolate_color(stops[index], stops[index + 1], local_t))


@lru_cache(maxsize=1)
def _load_countries() -> list[PolygonDatum]:
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
        pop = float(props.get("POP_EST") or 0.0)
        gdp = float(props.get("GDP_MD_EST") or 0.0)
        return gdp / max(1e5, pop)

    values = [_value(feat) for feat in features]
    max_val = max(values) if values else 1.0

    polygons: list[PolygonDatum] = []
    for feat, val in zip(features, values, strict=False):
        t = math.sqrt(val) / math.sqrt(max_val) if max_val else 0.0
        props = feat.setdefault("properties", {})
        color = _interpolate_scale(_YLORRD_STOPS, t)
        geometry = feat.get("geometry")
        if not isinstance(geometry, dict):
            raise ValueError("Feature geometry must be a GeoJSON object.")
        if geometry.get("type") == "Polygon":
            polygon_geometry = Polygon.model_validate(geometry)
        elif geometry.get("type") == "MultiPolygon":
            polygon_geometry = MultiPolygon.model_validate(geometry)
        else:
            raise ValueError("Country geometry must be Polygon or MultiPolygon.")
        label = (
            f"<b>{props.get('ADMIN', 'Unknown')} ({props.get('ISO_A2', '--')}):</b>"
            " <br />"
            f"GDP: <i>{props.get('GDP_MD_EST', 'N/A')}</i> M$<br/>"
            f"Population: <i>{props.get('POP_EST', 'N/A')}</i>"
        )
        polygons.append(
            PolygonDatum.model_validate(
                {
                    "id": uuid4(),
                    "geometry": polygon_geometry,
                    "cap_color": color,
                    "side_color": "rgba(0, 100, 0, 0.15)",
                    "stroke_color": "#111111",
                    "altitude": 0.06,
                    "label": label,
                    "hover_color": "steelblue",
                    "hover_altitude": 0.12,
                }
            )
        )

    return polygons


_COUNTRIES = _load_countries()
_COUNTRY_INDEX = {
    str(country.id): {
        "cap_color": country.cap_color,
        "altitude": country.altitude,
        "hover_color": country.hover_color,
        "hover_altitude": country.hover_altitude,
    }
    for country in _COUNTRIES
}

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
        polygons_data=_COUNTRIES, polygons_transition_duration=300
    ),
)


@solara.component
def page():
    """Render the polygons choropleth demo.

    Returns:
        The root Solara element.
    """
    widget = solara.use_memo(lambda: GlobeWidget(config=config), [])

    def _handle_hover(
        polygon: dict[str, Any] | None, prev_polygon: dict[str, Any] | None
    ) -> None:
        if prev_polygon is not None:
            prev_id = prev_polygon.get("id")
            if isinstance(prev_id, str) and prev_id in _COUNTRY_INDEX:
                base = _COUNTRY_INDEX[prev_id]
                widget.update_polygon(
                    prev_id, cap_color=base["cap_color"], altitude=base["altitude"]
                )
        if polygon is not None:
            polygon_id = polygon.get("id")
            if isinstance(polygon_id, str) and polygon_id in _COUNTRY_INDEX:
                base = _COUNTRY_INDEX[polygon_id]
                widget.update_polygon(
                    polygon_id,
                    cap_color=base["hover_color"],
                    altitude=base["hover_altitude"],
                )

    def _register_callbacks() -> None:
        widget.on_polygon_hover(_handle_hover)

    solara.use_effect(_register_callbacks, [])
    with solara.Column() as main:
        solara.display(widget)
    return main
