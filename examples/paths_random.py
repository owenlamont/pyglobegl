"""Random paths layer demo (globe.gl random-paths inspired).

Launch commands:
    uv run solara run examples/paths_random.py
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
import random
import threading
from uuid import uuid4

from pydantic import AnyUrl, TypeAdapter
import solara

from pyglobegl import (
    GlobeConfig,
    GlobeInitConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeViewConfig,
    GlobeWidget,
    PathDatum,
    PathDatumPatch,
    PathsLayerConfig,
    PointOfView,
)
from pyglobegl.config import UUID4


_URL_ADAPTER = TypeAdapter(AnyUrl)


def _generate_path_points(
    rng: random.Random, *, max_points: int, max_step_deg: float, max_step_alt: float
) -> tuple[list[tuple[float, float]], list[float]]:
    lat = (rng.random() - 0.5) * 90
    lng = (rng.random() - 0.5) * 360
    alt = 0.0
    points = [(lat, lng)]
    altitudes = [alt]

    for _ in range(rng.randint(0, max_points)):
        lat += (rng.random() * 2 - 1) * max_step_deg
        lng += (rng.random() * 2 - 1) * max_step_deg
        alt += (rng.random() * 2 - 1) * max_step_alt
        alt = max(0.0, alt)
        points.append((lat, lng))
        altitudes.append(alt)

    return points, altitudes


def _make_paths(
    rng: random.Random,
    *,
    count: int,
    max_points: int,
    max_step_deg: float,
    max_step_alt: float,
) -> list[tuple[list[tuple[float, float]], list[float]]]:
    return [
        _generate_path_points(
            rng,
            max_points=max_points,
            max_step_deg=max_step_deg,
            max_step_alt=max_step_alt,
        )
        for _ in range(count)
    ]


def _paths_without_altitude(
    paths: Sequence[tuple[list[tuple[float, float]], list[float]]], ids: Sequence[UUID4]
) -> list[PathDatum]:
    path_data: list[PathDatum] = []
    for index, (points, _) in enumerate(paths):
        path_data.append(
            PathDatum(
                id=ids[index],
                path=list(points),
                color=["rgba(0,0,255,0.6)", "rgba(255,0,0,0.6)"],
                dash_length=0.01,
                dash_gap=0.004,
                dash_animate_time=100000,
            )
        )
    return path_data


def _paths_with_altitude(
    paths: Sequence[tuple[list[tuple[float, float]], list[float]]], ids: Sequence[UUID4]
) -> list[PathDatum]:
    path_data: list[PathDatum] = []
    for index, (points, altitudes) in enumerate(paths):
        path: list[tuple[float, float] | tuple[float, float, float]] = [
            (lat, lng, alt) for (lat, lng), alt in zip(points, altitudes, strict=True)
        ]
        path_data.append(
            PathDatum(
                id=ids[index],
                path=path,
                color=["rgba(0,0,255,0.6)", "rgba(255,0,0,0.6)"],
                dash_length=0.01,
                dash_gap=0.004,
                dash_animate_time=100000,
            )
        )
    return path_data


def _make_config(paths: Sequence[PathDatum]) -> GlobeConfig:
    return GlobeConfig(
        init=GlobeInitConfig(animate_in=False),
        layout=GlobeLayoutConfig(width=900, height=600, background_color="#000000"),
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
        paths=PathsLayerConfig(paths_data=list(paths), path_transition_duration=0),
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=2.0), transition_ms=0
        ),
    )


@solara.component
def page():
    """Render the random paths demo.

    Returns:
        The root Solara element.
    """
    rng = random.Random(7)  # noqa: S311
    base_paths = solara.use_memo(
        lambda: _make_paths(
            rng, count=10, max_points=10000, max_step_deg=1.0, max_step_alt=0.015
        ),
        [],
    )
    path_ids = solara.use_memo(
        lambda: [uuid4() for _ in range(len(base_paths))], [base_paths]
    )
    initial_paths = solara.use_memo(
        lambda: _paths_without_altitude(base_paths, path_ids), [base_paths, path_ids]
    )
    updated_paths = solara.use_memo(
        lambda: _paths_with_altitude(base_paths, path_ids), [base_paths, path_ids]
    )
    updated_patches = solara.use_memo(
        lambda: [
            PathDatumPatch(id=path_ids[index], path=path.path)
            for index, path in enumerate(updated_paths)
        ],
        [updated_paths, path_ids],
    )
    widget = solara.use_memo(
        lambda: GlobeWidget(config=_make_config(initial_paths)), []
    )

    def _schedule_update() -> Callable[[], None] | None:
        def _apply_update_from_timer() -> None:
            widget.set_path_transition_duration(4000)
            widget.patch_paths_data(updated_patches)

        timer = threading.Timer(6.0, _apply_update_from_timer)
        timer.start()

        def _cleanup() -> None:
            timer.cancel()

        return _cleanup

    solara.use_effect(_schedule_update, [])

    with solara.Column() as main:
        solara.display(widget)
    return main
