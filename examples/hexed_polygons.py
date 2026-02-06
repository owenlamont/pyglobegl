"""Hexed polygons layer demo (globe.gl hexed-polygons).

Launch commands:
    uv run solara run examples/hexed_polygons.py
"""

from __future__ import annotations

from functools import lru_cache
import json
import random
from urllib.request import urlopen

from geojson_pydantic import MultiPolygon, Polygon
from pydantic import AnyUrl, TypeAdapter
import solara

from pyglobegl import (
    GlobeConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeViewConfig,
    GlobeWidget,
    HexedPolygonsLayerConfig,
    HexPolygonDatum,
    PointOfView,
)


_COUNTRIES_URL = (
    "https://unpkg.com/globe.gl@2.21.1/example/datasets/"
    "ne_110m_admin_0_countries.geojson"
)


@lru_cache(maxsize=1)
def _load_countries(seed: int = 42) -> list[HexPolygonDatum]:
    with urlopen(_COUNTRIES_URL) as response:
        data = json.load(response)

    rng = random.Random(seed)  # noqa: S311
    hexed: list[HexPolygonDatum] = []
    for feat in data.get("features", []):
        geometry = feat.get("geometry")
        if not isinstance(geometry, dict):
            continue
        if geometry.get("type") == "Polygon":
            polygon_geometry = Polygon.model_validate(geometry)
        elif geometry.get("type") == "MultiPolygon":
            polygon_geometry = MultiPolygon.model_validate(geometry)
        else:
            continue
        props = feat.get("properties", {})
        iso_a2 = props.get("ISO_A2", "--")
        pop_est = props.get("POP_EST", "unknown")
        label = (
            f"<b>{props.get('ADMIN', 'Unknown')} ({iso_a2})</b> <br />"
            f"Population: <i>{pop_est}</i>"
        )
        color = f"#{rng.randrange(0, 0xFFFFFF):06x}"
        hexed.append(
            HexPolygonDatum(
                geometry=polygon_geometry,
                color=color,
                resolution=3,
                margin=0.3,
                label=label,
            )
        )

    if not hexed:
        raise ValueError("No country features loaded from GeoJSON.")

    return hexed


config = GlobeConfig(
    layout=GlobeLayoutConfig(background_color="#000000"),
    globe=GlobeLayerConfig(
        globe_image_url=TypeAdapter(AnyUrl).validate_python(
            "https://unpkg.com/three-globe/example/img/earth-dark.jpg"
        )
    ),
    hexed_polygons=HexedPolygonsLayerConfig(hex_polygons_data=_load_countries()),
    view=GlobeViewConfig(point_of_view=PointOfView(lat=0, lng=0, altitude=2.2)),
)


@solara.component
def page():
    """Render the hexed polygons layer demo.

    Returns:
        The root Solara element.
    """
    solara.Style("body { margin: 0; background: #000; }")
    with solara.Column(
        style={"padding": "0", "margin": "0", "width": "100vw", "height": "100vh"}
    ) as main:
        solara.display(GlobeWidget(config=config))
    return main
