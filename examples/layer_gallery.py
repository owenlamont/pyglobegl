"""Layer gallery for documentation screenshots.

Renders one globe.gl layer at a time (selected from a dropdown) using the rich,
real-data builders from ``layer_montage`` assembled into an initial
``GlobeConfig`` (the synced path that renders on first paint), so each layer can
be screenshotted for the documentation.

Launch commands:
    uv run marimo run examples/layer_gallery.py --headless --port 2730 \
        --skip-update-check
"""

from __future__ import annotations

import marimo


__generated_with = "0.19.0"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    from datetime import datetime, timezone
    import math
    import sys
    from urllib.request import urlopen

    from pydantic import AnyUrl
    from sgp4.api import jday, Satrec

    sys.path.insert(0, "examples")  # run from the repo root
    import layer_montage as lm

    from pyglobegl import (
        ArcsLayerConfig,
        GlobeConfig,
        GlobeLayerConfig,
        GlobeLayoutConfig,
        GlobeViewConfig,
        GlobeWidget,
        HeatmapsLayerConfig,
        HexBinLayerConfig,
        HexedPolygonsLayerConfig,
        LabelsLayerConfig,
        ParticleDatum,
        ParticlePointDatum,
        ParticlesLayerConfig,
        PathsLayerConfig,
        PointOfView,
        PointsLayerConfig,
        PolygonsLayerConfig,
        RingDatum,
        RingsLayerConfig,
        TilesLayerConfig,
    )

    night = AnyUrl(
        "https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-night.jpg"
    )
    dark = AnyUrl("https://unpkg.com/three-globe/example/img/earth-dark.jpg")
    blue = AnyUrl("https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg")
    topo = AnyUrl(
        "https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-topology.png"
    )
    sky = AnyUrl("https://cdn.jsdelivr.net/npm/three-globe/example/img/night-sky.png")

    def cfg(globe, layer_kw, *, lat=12, lng=130, alt=2.5, bg=None, rotate=False):
        layout = GlobeLayoutConfig(width=800, height=600, background_color="#000000")
        if bg is not None:
            layout = GlobeLayoutConfig(
                width=800,
                height=600,
                background_color="#000000",
                background_image_url=bg,
            )
        return GlobeConfig(
            globe=globe,
            layout=layout,
            view=GlobeViewConfig(
                point_of_view=PointOfView(lat=lat, lng=lng, altitude=alt),
                controls_auto_rotate=rotate,
                controls_auto_rotate_speed=0.6,
            ),
            **layer_kw,
        )

    # Build rich data once (network-backed loaders are cached in lm).
    # Robust satellite propagation: skip malformed TLEs (the upstream feed has
    # a few records sgp4 rejects, which crashes lm._load_satellites).
    def satellite_points(when):
        jd, fr = jday(
            when.year,
            when.month,
            when.day,
            when.hour,
            when.minute,
            when.second + when.microsecond / 1e6,
        )
        gmst = lm._gstime(jd + fr)
        with urlopen(lm._TLE_URL) as response:  # ruff: ignore[suspicious-url-open-usage]
            raw = response.read().decode("utf-8")
        pts = []
        for name, line1, line2 in lm._parse_tle(raw):
            try:
                satrec = Satrec.twoline2rv(line1, line2)
                error_code, position, _vel = satrec.sgp4(jd, fr)
            except (ValueError, RuntimeError):
                continue
            if error_code != 0 or position is None:
                continue
            lat, lng, alt_km = lm._eci_to_geodetic(
                position[0], position[1], position[2], gmst
            )
            altitude = alt_km / lm._EARTH_RADIUS_KM
            if not math.isfinite(lat + lng + altitude):
                continue
            pts.append(
                ParticlePointDatum(lat=lat, lng=lng, altitude=altitude, label=name)
            )
        return pts[: lm._MAX_SATELLITES]

    now = datetime.now(tz=timezone.utc)
    sat_points = satellite_points(now)

    # Bright, slow rings so several concentric waves stay on-screen for a static
    # capture (the montage's faster, briefer ring pulses are hard to catch in a
    # still frame).
    import random

    ring_rng = random.Random(3)  # ruff: ignore[suspicious-non-cryptographic-random-usage]
    bright_rings = [
        RingDatum(
            lat=ring_rng.uniform(-55, 65),
            lng=ring_rng.uniform(-170, 170),
            color="#ffd23f",
            max_radius=ring_rng.uniform(5, 9),
            propagation_speed=3.0,
            repeat_period=800,
        )
        for _ in range(48)
    ]

    configs = {
        "globe": cfg(
            GlobeLayerConfig(
                globe_image_url=blue,
                show_atmosphere=True,
                atmosphere_color="lightskyblue",
            ),
            {},
        ),
        "points": cfg(
            GlobeLayerConfig(globe_image_url=night, show_atmosphere=False),
            {"points": PointsLayerConfig(points_data=lm._make_points())},
        ),
        "arcs": cfg(
            GlobeLayerConfig(globe_image_url=night, show_atmosphere=False),
            {"arcs": ArcsLayerConfig(arcs_data=lm._make_arcs())},
        ),
        "polygons": cfg(
            GlobeLayerConfig(
                globe_image_url=night, show_atmosphere=False, show_graticules=False
            ),
            {"polygons": PolygonsLayerConfig(polygons_data=lm._load_polygons())},
            bg=sky,
        ),
        "paths": cfg(
            GlobeLayerConfig(
                globe_image_url=dark,
                bump_image_url=topo,
                show_atmosphere=False,
                show_graticules=False,
            ),
            {
                "paths": PathsLayerConfig(
                    paths_data=lm._make_paths(), path_transition_duration=0
                )
            },
        ),
        "heatmaps": cfg(
            GlobeLayerConfig(globe_image_url=night),
            {
                "heatmaps": HeatmapsLayerConfig(
                    heatmaps_data=[lm._load_population_heatmap()]
                )
            },
        ),
        "hex-bin": cfg(
            GlobeLayerConfig(globe_image_url=night, bump_image_url=topo),
            {
                "hex_bin": HexBinLayerConfig(
                    hex_bin_points_data=lm._load_population_hexbin_points(),
                    hex_bin_resolution=4,
                    hex_altitude=lm._population_hex_altitude,
                    hex_top_color=lm._population_hex_color,
                    hex_side_color=lm._population_hex_color,
                    hex_bin_merge=True,
                    hex_transition_duration=0,
                )
            },
            bg=sky,
        ),
        "hexed-polygons": cfg(
            GlobeLayerConfig(globe_image_url=dark),
            {
                "hexed_polygons": HexedPolygonsLayerConfig(
                    hex_polygons_data=lm._load_hexed_polygons()
                )
            },
        ),
        "tiles": cfg(
            GlobeLayerConfig(show_globe=False, show_atmosphere=False),
            {"tiles": TilesLayerConfig(tiles_data=lm._make_tiles())},
        ),
        "particles": cfg(
            GlobeLayerConfig(globe_image_url=blue),
            {
                "particles": ParticlesLayerConfig(
                    particles_data=[
                        ParticleDatum(particles=sat_points, color="palegreen", size=6)
                    ]
                )
            },
        ),
        "rings": cfg(
            GlobeLayerConfig(globe_image_url=night, bump_image_url=topo),
            {"rings": RingsLayerConfig(rings_data=bright_rings)},
            rotate=True,
        ),
        "labels": cfg(
            GlobeLayerConfig(globe_image_url=night),
            {"labels": LabelsLayerConfig(labels_data=lm._load_world_cities())},
            bg=sky,
        ),
    }
    return GlobeWidget, configs


@app.cell
def _(configs, mo):
    selector = mo.ui.dropdown(
        options=list(configs.keys()), value="globe", label="Layer"
    )
    selector  # ruff: ignore[useless-expression]
    return (selector,)


@app.cell
def _(GlobeWidget, configs, mo, selector):  # ruff: ignore[invalid-argument-name]
    widget = mo.ui.anywidget(GlobeWidget(config=configs[selector.value]))
    widget  # ruff: ignore[useless-expression]
    return


if __name__ == "__main__":
    app.run()
