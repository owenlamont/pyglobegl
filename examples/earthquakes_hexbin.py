"""Earthquakes hexbin demo mirroring globe.gl's earthquakes example.

Launch commands:
    uv run solara run examples/earthquakes_hexbin.py
"""

from __future__ import annotations

from functools import lru_cache
import json
from urllib.request import urlopen

from pydantic import AnyUrl, TypeAdapter
import solara

from pyglobegl import (
    frontend_python,
    GlobeConfig,
    GlobeLayerConfig,
    GlobeViewConfig,
    GlobeWidget,
    HexBinLayerConfig,
    HexBinPointDatum,
    PointOfView,
)


_DATASET_URL = (
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_month.geojson"
)


@frontend_python
def earthquake_hex_altitude(hexbin: dict) -> float:
    """Return hex altitude from aggregate earthquake magnitude."""
    return float(hexbin["sumWeight"]) * 0.0025


@frontend_python
def earthquake_hex_color(hexbin: dict) -> str:
    """Return color interpolated from light blue to dark red."""
    # Keep interpolation self-contained for frontend MicroPython runtime.
    weight = float(hexbin["sumWeight"])
    if weight < 0:
        weight = 0.0
    if weight > 60:
        weight = 60.0
    t = weight / 60.0
    light_blue = (173, 216, 230)
    dark_red = (139, 0, 0)
    r = round(light_blue[0] + (dark_red[0] - light_blue[0]) * t)
    g = round(light_blue[1] + (dark_red[1] - light_blue[1]) * t)
    b = round(light_blue[2] + (dark_red[2] - light_blue[2]) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


@frontend_python
def earthquake_hex_label(hexbin: dict) -> str:
    """Return hover tooltip HTML listing earthquakes in this hexbin."""
    raw_points = hexbin.get("points")
    if not isinstance(raw_points, list):
        return "<b>0</b> earthquakes in the past month."

    points = [point for point in raw_points if isinstance(point, dict)]
    count = len(points)
    if count == 0:
        return "<b>0</b> earthquakes in the past month."

    # Keep hover callback cheap in frontend MicroPython to avoid UI stalls.
    sorted_points = sorted(
        points, key=lambda point: float(point.get("mag", 0.0)), reverse=True
    )[:12]
    titles = [str(point.get("title", "Unknown earthquake")) for point in sorted_points]
    if not titles:
        return f"<b>{count}</b> earthquakes in the past month."
    list_items = "</li><li>".join(titles)
    more_count = count - len(titles)
    more_suffix = f"</li><li>...and {more_count} more" if more_count > 0 else ""
    return (
        f"<b>{count}</b> earthquakes in the past month:"
        f"<ul><li>{list_items}{more_suffix}</li></ul>"
    )


def _load_earthquakes() -> list[HexBinPointDatum]:
    with urlopen(_DATASET_URL, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    features = payload.get("features", [])
    points: list[HexBinPointDatum] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        geometry = feature.get("geometry")
        properties = feature.get("properties")
        if not isinstance(geometry, dict) or not isinstance(properties, dict):
            continue
        coordinates = geometry.get("coordinates")
        if (
            not isinstance(coordinates, list)
            or len(coordinates) < 2
            or coordinates[0] is None
            or coordinates[1] is None
        ):
            continue
        magnitude = properties.get("mag")
        if not isinstance(magnitude, (int, float)):
            continue
        title = properties.get("title")
        points.append(
            HexBinPointDatum.model_validate(
                {
                    "lat": float(coordinates[1]),
                    "lng": float(coordinates[0]),
                    "weight": float(magnitude),
                    "mag": float(magnitude),
                    "title": (
                        str(title) if isinstance(title, str) else "Unknown earthquake"
                    ),
                }
            )
        )
    return points


@lru_cache(maxsize=1)
def _build_config() -> GlobeConfig:
    return GlobeConfig(
        globe=GlobeLayerConfig(
            globe_image_url=TypeAdapter(AnyUrl).validate_python(
                "https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-night.jpg"
            )
        ),
        view=GlobeViewConfig(point_of_view=PointOfView(lat=0, lng=0, altitude=2.2)),
        hex_bin=HexBinLayerConfig(
            hex_bin_points_data=_load_earthquakes(),
            hex_altitude=earthquake_hex_altitude,
            hex_top_color=earthquake_hex_color,
            hex_side_color=earthquake_hex_color,
            hex_label=earthquake_hex_label,
        ),
    )


@solara.component
def page():
    """Render the earthquakes hexbin demo.

    Returns:
        The root Solara element.
    """
    with solara.Column() as main:
        solara.display(GlobeWidget(config=_build_config()))
    return main
