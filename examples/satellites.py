"""Particles layer demo (globe.gl satellites).

Launch commands:
    uv run solara run examples/satellites.py
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache
import math
import threading
from urllib.request import urlopen

from pydantic import AnyUrl, TypeAdapter
from sgp4.api import jday, Satrec
import solara

from pyglobegl import (
    GlobeConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeViewConfig,
    GlobeWidget,
    ParticleDatum,
    ParticlePointDatum,
    ParticlesLayerConfig,
    PointOfView,
)


_CANVAS_WIDTH = 1200
_CANVAS_HEIGHT = 800
_EARTH_RADIUS_KM = 6371
_TIME_STEP_SECONDS = 3
_RENDER_INTERVAL_SECONDS = 0.05
_TLE_URL = "https://unpkg.com/globe.gl@2.44.1/example/datasets/space-track-leo.txt"
_MAX_SATELLITES = 500


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
    """Compute Greenwich mean sidereal time (radians).

    Returns:
        The sidereal time in radians.
    """
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


def _propagate_points(when: datetime) -> list[ParticlePointDatum]:
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


def _initial_particles() -> list[ParticlePointDatum]:
    return _propagate_points(datetime.now(tz=timezone.utc))


config = GlobeConfig(
    layout=GlobeLayoutConfig(
        width=_CANVAS_WIDTH, height=_CANVAS_HEIGHT, background_color="#000000"
    ),
    globe=GlobeLayerConfig(
        globe_image_url=TypeAdapter(AnyUrl).validate_python(
            "https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg"
        )
    ),
    particles=ParticlesLayerConfig(
        particles_data=[
            ParticleDatum(particles=_initial_particles(), color="palegreen")
        ]
    ),
    view=GlobeViewConfig(point_of_view=PointOfView(lat=0, lng=0, altitude=3.5)),
)


@solara.component
def page():
    """Render the satellites particles demo.

    Returns:
        The root Solara element.
    """
    widget = solara.use_memo(lambda: GlobeWidget(config=config), [])

    def _stream_positions(stop_event: threading.Event):
        current_time = datetime.now(tz=timezone.utc)
        while not stop_event.is_set():
            current_time = current_time + timedelta(seconds=_TIME_STEP_SECONDS)
            points = _propagate_points(current_time)
            yield [ParticleDatum(particles=points, color="palegreen")]
            stop_event.wait(_RENDER_INTERVAL_SECONDS)

    updates = solara.use_thread(_stream_positions, dependencies=[])

    def _apply_updates():
        if updates.value is None:
            return
        widget.set_particles_data(updates.value)
        return

    solara.use_effect(_apply_updates, [updates.value])

    with solara.Column(
        style={"padding": "0", "margin": "0", "width": "100%", "height": "100%"}
    ) as main:
        solara.display(widget)
    return main
