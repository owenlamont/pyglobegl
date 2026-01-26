import marimo


__generated_with = "0.19.6"
app = marimo.App(width="medium")


@app.function
def fetch_country_features() -> list[dict[str, object]]:
    """Fetch and filter country features from the GeoJSON source.

    Returns:
        List of feature dictionaries.

    Raises:
        ValueError: If no features are loaded.
    """
    import json
    from urllib.request import urlopen

    countries_url = (
        "https://raw.githubusercontent.com/vasturiano/globe.gl/"
        "master/example/datasets/ne_110m_admin_0_countries.geojson"
    )

    with urlopen(countries_url) as response:
        data = json.load(response)

    features = [
        feat
        for feat in data.get("features", [])
        if feat.get("properties", {}).get("ISO_A2") != "AQ"
    ]
    if not features:
        raise ValueError("No country features loaded from GeoJSON.")
    return features


@app.function
def compute_values(features: list[dict[str, object]]) -> tuple[list[float], float]:
    """Compute per-feature values and maximum.

    Returns:
        Tuple of values list and max value.
    """

    def to_float(value: object | None) -> float:
        if isinstance(value, (int, float, str)):
            return float(value)
        return 0.0

    def compute_value(props: dict[object, object]) -> float:
        pop = to_float(props.get("POP_EST"))
        gdp = to_float(props.get("GDP_MD_EST"))
        return gdp / max(1e5, pop)

    values = []
    for feat in features:
        props = feat.get("properties")
        if isinstance(props, dict):
            props = {str(key): value for key, value in props.items()}
        else:
            props = {}
        values.append(compute_value(props))
    max_val = max(values) if values else 1.0
    return values, max_val


@app.function
def build_polygons(
    features: list[dict[str, object]], values: list[float], max_val: float
):
    """Build polygon datums for globe.gl.

    Returns:
        List of polygon datums.

    Raises:
        ValueError: If the geometry is missing or invalid.
    """
    import math
    from uuid import uuid4

    from geojson_pydantic import MultiPolygon, Polygon

    from pyglobegl import PolygonDatum

    ylorrrd_stops = ["#ffffb2", "#fed976", "#feb24c", "#fd8d3c", "#f03b20", "#bd0026"]

    def interpolate_scale(stops: list[str], t: float) -> str:
        t = max(0.0, min(1.0, t))
        if len(stops) == 1:
            return stops[0]
        step = 1.0 / (len(stops) - 1)
        idx = min(int(t / step), len(stops) - 2)
        local_t = (t - idx * step) / step
        start = stops[idx]
        end = stops[idx + 1]

        def hex_to_rgb(value: str) -> tuple[int, int, int]:
            value = value.lstrip("#")
            return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)

        def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
            return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

        start_rgb = hex_to_rgb(start)
        end_rgb = hex_to_rgb(end)
        blended = (
            int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * local_t),
            int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * local_t),
            int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * local_t),
        )
        return rgb_to_hex(blended)

    def parse_geometry(geometry: dict[str, object]):
        geometry_type = geometry.get("type")
        if geometry_type == "Polygon":
            return Polygon.model_validate(geometry)
        if geometry_type == "MultiPolygon":
            return MultiPolygon.model_validate(geometry)
        raise ValueError("Country geometry must be Polygon or MultiPolygon.")

    def build_label(props: dict[str, object]) -> str:
        admin = props.get("ADMIN", "Unknown")
        iso = props.get("ISO_A2", "--")
        gdp = props.get("GDP_MD_EST", "N/A")
        population = props.get("POP_EST", "N/A")
        return (
            f"<b>{admin} ({iso}):</b> <br />"
            f"GDP: <i>{gdp}</i> M$<br/>"
            f"Population: <i>{population}</i>"
        )

    polygons: list[PolygonDatum] = []
    for feat, val in zip(features, values, strict=False):
        t = math.sqrt(val) / math.sqrt(max_val) if max_val else 0.0
        props = feat.setdefault("properties", {})
        color = interpolate_scale(ylorrrd_stops, t)
        geometry = feat.get("geometry")
        if not isinstance(geometry, dict):
            raise ValueError("Feature geometry must be a GeoJSON object.")
        polygon_geometry = parse_geometry(geometry)
        polygons.append(
            PolygonDatum.model_validate(
                {
                    "id": uuid4(),
                    "geometry": polygon_geometry,
                    "cap_color": color,
                    "side_color": "rgba(0, 100, 0, 0.15)",
                    "stroke_color": "#111111",
                    "altitude": 0.06,
                    "label": build_label(props),
                    "hover_color": "steelblue",
                    "hover_altitude": 0.12,
                }
            )
        )
    return polygons


@app.function
def load_countries():
    """Load and prepare polygon data for the choropleth.

    Returns:
        List of polygon datums.
    """
    from functools import lru_cache

    @lru_cache(maxsize=1)
    def _load():
        features = fetch_country_features()
        values, max_val = compute_values(features)
        return build_polygons(features, values, max_val)

    return _load()


@app.cell
def _():
    countries = load_countries()
    country_index = {
        str(country.id): {
            "cap_color": country.cap_color,
            "altitude": country.altitude,
            "hover_color": country.hover_color,
            "hover_altitude": country.hover_altitude,
        }
        for country in countries
    }
    return countries, country_index


@app.cell
def _(countries):
    from pydantic import AnyUrl, TypeAdapter

    from pyglobegl import (
        GlobeConfig,
        GlobeLayerConfig,
        GlobeLayoutConfig,
        PolygonsLayerConfig,
    )

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
            polygons_data=countries, polygons_transition_duration=300
        ),
    )
    return (config,)


@app.cell
def _(config, country_index):
    from typing import Any

    from pyglobegl import GlobeWidget

    widget = GlobeWidget(config=config)

    def handle_hover(
        polygon: dict[str, Any] | None, prev_polygon: dict[str, Any] | None
    ) -> None:
        if prev_polygon is not None:
            prev_id = prev_polygon.get("id")
            if isinstance(prev_id, str) and prev_id in country_index:
                base = country_index[prev_id]
                widget.update_polygon(
                    prev_id, cap_color=base["cap_color"], altitude=base["altitude"]
                )
        if polygon is not None:
            polygon_id = polygon.get("id")
            if isinstance(polygon_id, str) and polygon_id in country_index:
                base = country_index[polygon_id]
                widget.update_polygon(
                    polygon_id,
                    cap_color=base["hover_color"],
                    altitude=base["hover_altitude"],
                )

    widget.on_polygon_hover(handle_hover)
    widget  # noqa: B018
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
