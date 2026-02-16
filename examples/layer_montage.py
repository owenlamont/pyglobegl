"""Layer montage demo.

Rotates the globe 360° for each layer, pauses, then switches to the next layer.

Launch commands:
    uv run solara run examples/layer_montage.py

Video tip (example):
    Record in Playwright, then add fades with ffmpeg.
"""

from __future__ import annotations

from collections.abc import Callable, Generator, Mapping
import csv
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import json
import math
import random
import threading
import time
from typing import Any
from urllib.request import urlopen

from geojson_pydantic import MultiPolygon, Polygon
from pydantic import AnyUrl, TypeAdapter
from sgp4.api import jday, Satrec
import solara

from pyglobegl import (
    ArcDatum,
    frontend_python,
    GlobeConfig,
    GlobeInitConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeMaterialSpec,
    GlobeViewConfig,
    GlobeWidget,
    HeatmapDatum,
    HeatmapPointDatum,
    HexBinPointDatum,
    HexPolygonDatum,
    LabelDatum,
    ParticleDatum,
    ParticlePointDatum,
    PathDatum,
    PointDatum,
    PointOfView,
    PolygonDatum,
    RingDatum,
    TileDatum,
    TilesLayerConfig,
)


ROTATE_SECONDS = 4.0
PAUSE_SECONDS = 2.0
_FRAME_INTERVAL_SECONDS = 0.05
_SATELLITE_STEP_SECONDS = 10
_SATELLITE_UPDATE_INTERVAL = 0.1

_START_LNG = 135.0
_START_ALTITUDE = 2.64

_URL_ADAPTER = TypeAdapter(AnyUrl)

_POPULATION_URL = (
    "https://unpkg.com/globe.gl@2.44.1/example/datasets/world_population.csv"
)

_COUNTRIES_URL = (
    "https://raw.githubusercontent.com/vasturiano/globe.gl/"
    "master/example/datasets/ne_110m_admin_0_countries.geojson"
)

_HEXED_COUNTRIES_URL = (
    "https://unpkg.com/globe.gl@2.21.1/example/datasets/"
    "ne_110m_admin_0_countries.geojson"
)

_PLACES_URL = (
    "https://unpkg.com/globe.gl@2.18.2/example/datasets/"
    "ne_110m_populated_places_simple.geojson"
)

_TLE_URL = "https://unpkg.com/globe.gl@2.44.1/example/datasets/space-track-leo.txt"

_EARTH_RADIUS_KM = 6371
_MAX_SATELLITES = 300


@dataclass(frozen=True)
class Stage:
    name: str
    layout: GlobeLayoutConfig | None
    globe: GlobeLayerConfig | None
    base_view: PointOfView
    apply: Callable[[GlobeWidget], None]
    pre_rotate_wait_seconds: float = 0.0


@dataclass(frozen=True)
class StageUpdate:
    stage_index: int
    pov: PointOfView | None
    apply_stage: bool
    particles_data: list[ParticleDatum] | None = None


def _make_points(seed: int = 7, count: int = 240) -> list[PointDatum]:
    rng = random.Random(seed)  # noqa: S311
    colors = ["red", "white", "blue", "green"]
    return [
        PointDatum(
            lat=(rng.random() - 0.5) * 180,
            lng=(rng.random() - 0.5) * 360,
            altitude=rng.random() / 2.5,
            color=rng.choice(colors),
        )
        for _ in range(count)
    ]


def _make_arcs(seed: int = 11, count: int = 120) -> list[ArcDatum]:
    rng = random.Random(seed)  # noqa: S311
    colors = ["#ff6b6b", "#ffd93d", "#4dabf7", "#69db7c"]
    return [
        ArcDatum(
            start_lat=(rng.random() - 0.5) * 180,
            start_lng=(rng.random() - 0.5) * 360,
            end_lat=(rng.random() - 0.5) * 180,
            end_lng=(rng.random() - 0.5) * 360,
            altitude=rng.random() * 0.4 + 0.1,
            color=rng.choice(colors),
            label=f"Arc {index + 1}",
            stroke=0.6,
        )
        for index in range(count)
    ]


def _make_paths(
    seed: int = 23,
    count: int = 10,
    max_points: int = 10000,
    max_step_deg: float = 1.0,
    max_step_alt: float = 0.006,
    max_altitude: float = 0.04,
) -> list[PathDatum]:
    rng = random.Random(seed)  # noqa: S311
    paths: list[PathDatum] = []
    for _ in range(count):
        lat = (rng.random() - 0.5) * 90
        lng = (rng.random() - 0.5) * 360
        altitude = 0.0
        path: list[tuple[float, float] | tuple[float, float, float]] = [(lat, lng)]
        for _ in range(rng.randint(0, max_points)):
            lat += (rng.random() * 2 - 1) * max_step_deg
            lng += (rng.random() * 2 - 1) * max_step_deg
            altitude = altitude + (rng.random() * 2 - 1) * max_step_alt
            altitude = max(0.0, min(max_altitude, altitude))
            path.append((lat, lng, altitude))
        paths.append(
            PathDatum(
                path=path,
                color=["rgba(0,0,255,0.6)", "rgba(255,0,0,0.6)"],
                dash_length=0.01,
                dash_gap=0.004,
                dash_animate_time=100000,
            )
        )
    return paths


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


def _feature_properties(feature: Mapping[str, Any]) -> Mapping[str, Any]:
    props = feature.get("properties")
    return props if isinstance(props, Mapping) else {}


def _country_value(props: Mapping[str, Any]) -> float:
    pop = float(props.get("POP_EST") or 0.0)
    gdp = float(props.get("GDP_MD_EST") or 0.0)
    return gdp / max(1e5, pop)


def _build_polygon(
    feature: Mapping[str, Any], value: float, max_value: float
) -> PolygonDatum | None:
    geometry = feature.get("geometry")
    if not isinstance(geometry, dict):
        return None
    if geometry.get("type") == "Polygon":
        polygon_geometry = Polygon.model_validate(geometry)
    elif geometry.get("type") == "MultiPolygon":
        polygon_geometry = MultiPolygon.model_validate(geometry)
    else:
        return None

    props = _feature_properties(feature)
    t = math.sqrt(value) / math.sqrt(max_value) if max_value else 0.0
    color = _interpolate_scale(_YLORRD_STOPS, t)
    label = (
        f"<b>{props.get('ADMIN', 'Unknown')} ({props.get('ISO_A2', '--')}):</b>"
        " <br />"
        f"GDP: <i>{props.get('GDP_MD_EST', 'N/A')}</i> M$<br/>"
        f"Population: <i>{props.get('POP_EST', 'N/A')}</i>"
    )
    return PolygonDatum.model_validate(
        {
            "geometry": polygon_geometry,
            "cap_color": color,
            "side_color": "rgba(0, 100, 0, 0.15)",
            "stroke_color": "#111111",
            "altitude": 0.06,
            "label": label,
        }
    )


@lru_cache(maxsize=1)
def _load_polygons() -> list[PolygonDatum]:
    with urlopen(_COUNTRIES_URL) as response:
        data = json.load(response)

    raw_features = data.get("features", [])
    features = [
        feat
        for feat in raw_features
        if isinstance(feat, Mapping) and _feature_properties(feat).get("ISO_A2") != "AQ"
    ]
    if not features:
        raise ValueError("No country features loaded from GeoJSON.")

    values = [_country_value(_feature_properties(feat)) for feat in features]
    max_val = max(values) if values else 1.0

    polygons = [
        polygon
        for feat, val in zip(features, values, strict=False)
        if (polygon := _build_polygon(feat, val, max_val)) is not None
    ]
    if not polygons:
        raise ValueError("No country polygon geometries were usable.")
    return polygons


@lru_cache(maxsize=1)
def _load_population_heatmap() -> HeatmapDatum:
    with urlopen(_POPULATION_URL) as response:
        csv_text = response.read().decode("utf-8")

    reader = csv.DictReader(csv_text.splitlines())
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


@lru_cache(maxsize=1)
def _load_population_hexbin_points() -> list[HexBinPointDatum]:
    heatmap = _load_population_heatmap()
    return [
        HexBinPointDatum(lat=point.lat, lng=point.lng, weight=point.weight)
        for point in heatmap.points
    ]


@frontend_python
def _population_hex_altitude(hexbin: dict) -> float:
    """Return altitude scaled from aggregate hex population."""
    return hexbin["sumWeight"] * 6e-8


@frontend_python
def _population_hex_color(hexbin: dict) -> str:
    """Return a YlOrRd color interpolated by sqrt-scaled aggregate population."""
    # Keep this self-contained so frontend MicroPython has all required symbols.
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


def _apply_population_hexbin(
    widget: GlobeWidget, points: list[HexBinPointDatum]
) -> None:
    widget.set_hex_bin_resolution(4)
    widget.set_hex_altitude(_population_hex_altitude)
    widget.set_hex_top_color(_population_hex_color)
    widget.set_hex_side_color(_population_hex_color)
    widget.set_hex_bin_merge(True)
    widget.set_hex_transition_duration(0)
    widget.set_hex_bin_points_data(points)


@lru_cache(maxsize=1)
def _load_hexed_polygons(seed: int = 42) -> list[HexPolygonDatum]:
    with urlopen(_HEXED_COUNTRIES_URL) as response:
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
        if not isinstance(props, dict):
            props = {}
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


def _make_tiles(seed: int = 13) -> list[TileDatum]:
    rng = random.Random(seed)  # noqa: S311
    grid_size = (60, 20)
    tile_margin = 0.35
    tile_width = 360 / grid_size[0]
    tile_height = 180 / grid_size[1]
    width = tile_width - tile_margin
    height = tile_height - tile_margin

    colors = [
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

    tiles: list[TileDatum] = []
    for lng_idx in range(grid_size[0]):
        for lat_idx in range(grid_size[1]):
            color = rng.choice(colors)
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


@lru_cache(maxsize=1)
def _load_world_cities() -> list[LabelDatum]:
    with urlopen(_PLACES_URL) as response:
        data = json.load(response)

    labels: list[LabelDatum] = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        if not isinstance(props, dict):
            continue
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


def _parse_tle(raw: str) -> list[tuple[str, str, str]]:
    entries: list[tuple[str, str, str]] = []
    name: str | None = None
    lines: list[str] = []
    for line in raw.replace("\r", "").splitlines():
        if not line.strip():
            continue
        if line[0] not in {"1", "2"}:
            if name and len(lines) >= 2:
                entries.append((name, lines[0], lines[1]))
            name = line.strip().removeprefix("0 ").strip()
            lines = []
        else:
            lines.append(line.strip())
    if name and len(lines) >= 2:
        entries.append((name, lines[0], lines[1]))
    return entries


def _gstime(julian_date: float) -> float:
    t = (julian_date - 2451545.0) / 36525.0
    seconds = (
        67310.54841
        + (876600 * 3600 + 8640184.812866) * t
        + 0.093104 * t * t
        - 6.2e-6 * t * t * t
    )
    seconds = seconds % 86400.0
    if seconds < 0:
        seconds += 86400.0
    return seconds * (2 * math.pi / 86400.0)


def _eci_to_geodetic(
    x_km: float, y_km: float, z_km: float, gmst: float
) -> tuple[float, float, float]:
    cos_gmst = math.cos(gmst)
    sin_gmst = math.sin(gmst)
    x = x_km * cos_gmst + y_km * sin_gmst
    y = -x_km * sin_gmst + y_km * cos_gmst
    z = z_km

    lon = math.degrees(math.atan2(y, x))
    hyp = math.hypot(x, y)
    lat = math.degrees(math.atan2(z, hyp))
    alt_km = math.sqrt(x * x + y * y + z * z) - _EARTH_RADIUS_KM
    return lat, lon, alt_km


@lru_cache(maxsize=1)
def _load_satellites() -> list[tuple[str, Satrec]]:
    with urlopen(_TLE_URL) as response:
        raw = response.read().decode("utf-8")

    tle_entries = _parse_tle(raw)
    if not tle_entries:
        raise ValueError("No TLE entries parsed from the satellites dataset.")

    satellites: list[tuple[str, Satrec]] = []
    for name, line1, line2 in tle_entries:
        satellites.append((name, Satrec.twoline2rv(line1, line2)))
    if len(satellites) <= _MAX_SATELLITES:
        return satellites
    return satellites[:_MAX_SATELLITES]


@lru_cache(maxsize=1)
def _propagate_satellite_particles(when: datetime) -> list[ParticlePointDatum]:
    jd, fr = jday(
        when.year,
        when.month,
        when.day,
        when.hour,
        when.minute,
        when.second + when.microsecond / 1e6,
    )
    gmst = _gstime(jd + fr)

    points: list[ParticlePointDatum] = []
    for name, satrec in _load_satellites():
        error_code, position, _velocity = satrec.sgp4(jd, fr)
        if error_code != 0 or position is None:
            continue
        lat, lng, alt_km = _eci_to_geodetic(position[0], position[1], position[2], gmst)
        altitude = alt_km / _EARTH_RADIUS_KM
        if (
            not math.isfinite(lat)
            or not math.isfinite(lng)
            or not math.isfinite(altitude)
        ):
            continue
        points.append(
            ParticlePointDatum(lat=lat, lng=lng, altitude=altitude, label=name)
        )

    if not points:
        raise ValueError("Satellite propagation produced no valid positions.")

    return points


def _make_rings(seed: int = 11, count: int = 40) -> list[RingDatum]:
    rng = random.Random(seed)  # noqa: S311
    colors = ["rgba(255,100,50,1)", "rgba(255,100,50,0)"]
    return [
        RingDatum(
            lat=(rng.random() - 0.5) * 180,
            lng=(rng.random() - 0.5) * 360,
            color=colors,
            max_radius=rng.random() * 8 + 4,
            propagation_speed=rng.random() * 20 + 10,
            repeat_period=1200,
        )
        for _ in range(count)
    ]


def _apply_layout_and_globe(widget: GlobeWidget, stage: Stage) -> None:
    update: dict[str, object] = {}
    if stage.layout is not None:
        update["layout"] = stage.layout.model_dump(
            by_alias=True, exclude_none=True, mode="json"
        )
    if stage.globe is not None:
        update["globe"] = stage.globe.model_dump(
            by_alias=True, exclude_none=True, mode="json"
        )
    if update:
        widget.config = update


def _set_view(widget: GlobeWidget, pov: PointOfView) -> None:
    view = GlobeViewConfig(point_of_view=pov, transition_ms=0)
    widget.config = {"view": view.model_dump(by_alias=True, mode="json")}


def _clear_layers(widget: GlobeWidget) -> None:
    widget.set_points_data([])
    widget.set_arcs_data([])
    widget.set_paths_data([])
    widget.set_polygons_data([])
    widget.set_heatmaps_data([])
    widget.set_hex_bin_points_data([])
    widget.set_hex_polygons_data([])
    widget.set_tiles_data([])
    widget.set_particles_data([])
    widget.set_rings_data([])
    widget.set_labels_data([])


def _build_stages() -> list[Stage]:
    points = _make_points()
    arcs = _make_arcs()
    paths = _make_paths()
    polygons = _load_polygons()
    heatmap = _load_population_heatmap()
    hexed = _load_hexed_polygons()
    tiles = _make_tiles()
    particles = _propagate_satellite_particles(datetime.now(tz=timezone.utc))
    rings = _make_rings()
    labels = _load_world_cities()

    return [
        Stage(
            name="points",
            layout=GlobeLayoutConfig(background_color="#000000"),
            globe=GlobeLayerConfig(
                globe_image_url=_URL_ADAPTER.validate_python(
                    "https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-night.jpg"
                ),
                show_atmosphere=False,
            ),
            base_view=PointOfView(lat=0, lng=_START_LNG, altitude=_START_ALTITUDE),
            apply=lambda widget: widget.set_points_data(points),
        ),
        Stage(
            name="arcs",
            layout=GlobeLayoutConfig(background_color="#000000"),
            globe=GlobeLayerConfig(
                globe_image_url=_URL_ADAPTER.validate_python(
                    "https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-night.jpg"
                ),
                show_atmosphere=False,
            ),
            base_view=PointOfView(lat=0, lng=_START_LNG, altitude=_START_ALTITUDE),
            apply=lambda widget: widget.set_arcs_data(arcs),
        ),
        Stage(
            name="world_population_hexbin",
            layout=GlobeLayoutConfig(
                background_color="#000000",
                background_image_url=_URL_ADAPTER.validate_python(
                    "https://cdn.jsdelivr.net/npm/three-globe/example/img/night-sky.png"
                ),
            ),
            globe=GlobeLayerConfig(
                globe_image_url=_URL_ADAPTER.validate_python(
                    "https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-night.jpg"
                ),
                bump_image_url=_URL_ADAPTER.validate_python(
                    "https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-topology.png"
                ),
            ),
            base_view=PointOfView(lat=0, lng=_START_LNG, altitude=_START_ALTITUDE),
            apply=lambda widget: _apply_population_hexbin(
                widget, _load_population_hexbin_points()
            ),
            pre_rotate_wait_seconds=PAUSE_SECONDS,
        ),
        Stage(
            name="heatmaps",
            layout=GlobeLayoutConfig(background_color="#000000"),
            globe=GlobeLayerConfig(
                globe_image_url=_URL_ADAPTER.validate_python(
                    "https://unpkg.com/three-globe/example/img/earth-night.jpg"
                )
            ),
            base_view=PointOfView(lat=0, lng=_START_LNG, altitude=_START_ALTITUDE),
            apply=lambda widget: widget.set_heatmaps_data([heatmap]),
        ),
        Stage(
            name="polygons",
            layout=GlobeLayoutConfig(
                background_color="#000000",
                background_image_url=_URL_ADAPTER.validate_python(
                    "https://cdn.jsdelivr.net/npm/three-globe/example/img/night-sky.png"
                ),
            ),
            globe=GlobeLayerConfig(
                globe_image_url=_URL_ADAPTER.validate_python(
                    "https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-night.jpg"
                ),
                show_atmosphere=False,
                show_graticules=False,
            ),
            base_view=PointOfView(lat=0, lng=_START_LNG, altitude=_START_ALTITUDE),
            apply=lambda widget: widget.set_polygons_data(polygons),
        ),
        Stage(
            name="hexed_polygons",
            layout=GlobeLayoutConfig(background_color="#000000"),
            globe=GlobeLayerConfig(
                globe_image_url=_URL_ADAPTER.validate_python(
                    "https://unpkg.com/three-globe/example/img/earth-dark.jpg"
                )
            ),
            base_view=PointOfView(lat=0, lng=_START_LNG, altitude=_START_ALTITUDE),
            apply=lambda widget: widget.set_hex_polygons_data(hexed),
        ),
        Stage(
            name="paths",
            layout=GlobeLayoutConfig(background_color="#000000"),
            globe=GlobeLayerConfig(
                globe_image_url=_URL_ADAPTER.validate_python(
                    "https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-dark.jpg"
                ),
                bump_image_url=_URL_ADAPTER.validate_python(
                    "https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-topology.png"
                ),
                show_atmosphere=False,
                show_graticules=False,
            ),
            base_view=PointOfView(lat=0, lng=_START_LNG, altitude=_START_ALTITUDE),
            apply=lambda widget: widget.set_paths_data(paths),
        ),
        Stage(
            name="tiles",
            layout=GlobeLayoutConfig(background_color="#000000"),
            globe=GlobeLayerConfig(show_globe=False, show_atmosphere=False),
            base_view=PointOfView(lat=0, lng=_START_LNG, altitude=_START_ALTITUDE),
            apply=lambda widget: widget.set_tiles_data(tiles),
        ),
        Stage(
            name="particles",
            layout=GlobeLayoutConfig(background_color="#000000"),
            globe=GlobeLayerConfig(
                globe_image_url=_URL_ADAPTER.validate_python(
                    "https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg"
                )
            ),
            base_view=PointOfView(lat=0, lng=_START_LNG, altitude=_START_ALTITUDE),
            apply=lambda widget: widget.set_particles_data(
                [ParticleDatum(particles=particles, color="palegreen", size=6)]
            ),
        ),
        Stage(
            name="rings",
            layout=GlobeLayoutConfig(background_color="#000000"),
            globe=GlobeLayerConfig(
                globe_image_url=_URL_ADAPTER.validate_python(
                    "https://unpkg.com/three-globe/example/img/earth-dark.jpg"
                ),
                bump_image_url=_URL_ADAPTER.validate_python(
                    "https://unpkg.com/three-globe/example/img/earth-topology.png"
                ),
            ),
            base_view=PointOfView(lat=0, lng=_START_LNG, altitude=_START_ALTITUDE),
            apply=lambda widget: widget.set_rings_data(rings),
        ),
        Stage(
            name="labels",
            layout=GlobeLayoutConfig(
                background_image_url=_URL_ADAPTER.validate_python(
                    "https://unpkg.com/three-globe/example/img/night-sky.png"
                ),
                background_color="#000000",
            ),
            globe=GlobeLayerConfig(
                globe_image_url=_URL_ADAPTER.validate_python(
                    "https://unpkg.com/three-globe/example/img/earth-night.jpg"
                )
            ),
            base_view=PointOfView(lat=0, lng=_START_LNG, altitude=_START_ALTITUDE),
            apply=lambda widget: widget.set_labels_data(labels),
        ),
    ]


def _apply_stage(widget: GlobeWidget, stage: Stage) -> None:
    _clear_layers(widget)
    _apply_layout_and_globe(widget, stage)
    stage.apply(widget)
    _set_view(widget, stage.base_view)


def _wrap_longitude(lng: float) -> float:
    return (lng + 180.0) % 360.0 - 180.0


def _run_montage(
    stages: list[Stage], ready: bool, stop_event: threading.Event
) -> Generator[StageUpdate, None, None]:
    if not ready:
        return
    stage_index = 0
    current_time = datetime.now(tz=timezone.utc)
    yield StageUpdate(stage_index=stage_index, pov=None, apply_stage=True)
    while not stop_event.is_set():
        stage = stages[stage_index]
        start = time.monotonic()
        next_particle_update = start
        while True:
            elapsed = time.monotonic() - start
            if elapsed >= ROTATE_SECONDS:
                break
            progress = elapsed / ROTATE_SECONDS
            lng = _wrap_longitude(stage.base_view.lng + progress * 360)
            pov = PointOfView(
                lat=stage.base_view.lat, lng=lng, altitude=stage.base_view.altitude
            )
            particles_data: list[ParticleDatum] | None = None
            if stage.name == "particles" and time.monotonic() >= next_particle_update:
                current_time = current_time + timedelta(seconds=_SATELLITE_STEP_SECONDS)
                particles = _propagate_satellite_particles(current_time)
                particles_data = [
                    ParticleDatum(particles=particles, color="palegreen", size=6)
                ]
                next_particle_update = time.monotonic() + _SATELLITE_UPDATE_INTERVAL
            yield StageUpdate(
                stage_index=stage_index,
                pov=pov,
                apply_stage=False,
                particles_data=particles_data,
            )
            stop_event.wait(_FRAME_INTERVAL_SECONDS)
        yield StageUpdate(
            stage_index=stage_index, pov=stage.base_view, apply_stage=False
        )
        stage_index = (stage_index + 1) % len(stages)
        yield StageUpdate(stage_index=stage_index, pov=None, apply_stage=True)
        next_stage = stages[stage_index]
        if next_stage.pre_rotate_wait_seconds > 0:
            stop_event.wait(next_stage.pre_rotate_wait_seconds)
        stop_event.wait(PAUSE_SECONDS)


def _apply_update(
    widget: GlobeWidget, stages: list[Stage], update: StageUpdate | None
) -> None:
    if update is None:
        return
    if update.apply_stage:
        _apply_stage(widget, stages[update.stage_index])
        return
    if update.particles_data is not None:
        widget.set_particles_data(update.particles_data)
    if update.pov is not None:
        _set_view(widget, update.pov)


@solara.component
def page():
    """Render the layer montage demo.

    Returns:
        The root Solara element.
    """
    stages = solara.use_memo(_build_stages, [])
    initial_layout = stages[0].layout or GlobeLayoutConfig(background_color="#000000")
    initial_globe = stages[0].globe or GlobeLayerConfig()
    initial_config = GlobeConfig(
        init=GlobeInitConfig(animate_in=False),
        layout=initial_layout,
        globe=initial_globe,
        view=GlobeViewConfig(point_of_view=stages[0].base_view, transition_ms=0),
        tiles=TilesLayerConfig(),
    )
    widget = solara.use_memo(lambda: GlobeWidget(config=initial_config), [])
    initial_ready: bool = False
    ready, set_ready = solara.use_state(initial_ready)

    def _register_ready() -> None:
        def _mark_ready() -> None:
            set_ready(True)  # type: ignore[arg-type]

        widget.on_globe_ready(_mark_ready)

    solara.use_effect(_register_ready, [])

    def _start_thread(
        stop_event: threading.Event,
    ) -> Generator[StageUpdate, None, None]:
        return _run_montage(stages, ready, stop_event)

    updates = solara.use_thread(_start_thread, dependencies=[ready, stages])

    def _apply_updates() -> None:
        update = updates.value
        if not isinstance(update, StageUpdate):
            return
        _apply_update(widget, stages, update)

    solara.use_effect(_apply_updates, [updates.value])

    solara.Style("body { margin: 0; background: #000; }")
    with solara.Column(
        style={"padding": "0", "margin": "0", "width": "100vw", "height": "100vh"}
    ) as main:
        solara.display(widget)
    return main
