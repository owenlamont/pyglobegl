from __future__ import annotations

from typing import TYPE_CHECKING

from IPython.display import display
import numpy as np
from pydantic import AnyUrl, TypeAdapter
import pytest

from pyglobegl import (
    frontend_python,
    GlobeConfig,
    GlobeInitConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeViewConfig,
    GlobeWidget,
    PointOfView,
    RingDatum,
    RingsLayerConfig,
)


if TYPE_CHECKING:
    from collections.abc import Callable

    from PIL import Image
    from playwright.sync_api import Page

_URL_ADAPTER = TypeAdapter(AnyUrl)


def _sample_ring_colours(
    page: Page,
    capture: Callable[[Page, int], Image.Image],
    *,
    frames: int = 8,
    interval_ms: int = 150,
) -> dict[str, int]:
    """Aggregate gradient-colour pixel counts across several animation frames.

    Rings animate every frame, so instead of comparing one still frame this
    samples the canvas over time and counts pixels that are warm (red end of the
    gradient, ``t`` near 0), cool (blue end, ``t`` near 1), or yellow (the
    per-datum ``#ffffaa`` default). A small centre patch is scored separately so
    the runtime swap (which flips the innermost ring's colour) is verifiable.

    Returns:
        Pixel-count totals keyed ``warm`` / ``cool`` / ``yellow`` /
        ``centre_warm`` / ``centre_cool`` summed over the sampled frames.
    """
    totals = {"warm": 0, "cool": 0, "yellow": 0, "centre_warm": 0, "centre_cool": 0}
    for index in range(frames):
        arr = np.asarray(capture(page, 1)).astype(int)
        red, green, blue = arr[..., 0], arr[..., 1], arr[..., 2]
        warm = (red - blue > 40) & (green < 120)
        cool = blue - red > 40
        yellow = (red > 180) & (green > 180) & (blue < 200)
        totals["warm"] += int(np.count_nonzero(warm))
        totals["cool"] += int(np.count_nonzero(cool))
        totals["yellow"] += int(np.count_nonzero(yellow))
        height, width = red.shape
        cy, cx = height // 2, width // 2
        patch = (slice(cy - 16, cy + 16), slice(cx - 16, cx + 16))
        totals["centre_warm"] += int(np.count_nonzero(warm[patch]))
        totals["centre_cool"] += int(np.count_nonzero(cool[patch]))
        if index < frames - 1:
            page.wait_for_timeout(interval_ms)
    return totals


def _make_config(rings: RingsLayerConfig, globe_texture_url: str) -> GlobeConfig:
    return GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#000000"),
        globe=GlobeLayerConfig(
            globe_image_url=_URL_ADAPTER.validate_python(globe_texture_url),
            show_atmosphere=False,
            show_graticules=False,
        ),
        rings=rings,
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.8), transition_ms=0
        ),
    )


def _await_globe_ready(page_session: Page) -> None:
    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )
    page_session.wait_for_timeout(500)


@pytest.mark.usefixtures("solara_test")
def test_rings_accessors(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.96
    rings = [
        RingDatum(
            lat=0,
            lng=0,
            color="#ff0000",
            altitude=0.02,
            max_radius=12,
            propagation_speed=0,
            repeat_period=0,
        )
    ]
    updated = [
        RingDatum(
            lat=10,
            lng=10,
            color="#00ccff",
            altitude=0.06,
            max_radius=18,
            propagation_speed=4,
            repeat_period=1000,
        )
    ]

    config = _make_config(
        RingsLayerConfig(rings_data=rings, ring_resolution=32),
        globe_flat_texture_data_url,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(page_session, "initial", canvas_similarity_threshold)

    widget.set_ring_resolution(96)
    widget.set_rings_data(updated)
    page_session.wait_for_timeout(1300)
    canvas_assert_capture(page_session, "updated", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_ring_color_fn(
    page_session: Page, canvas_capture, globe_flat_texture_data_url
) -> None:
    # Rings animate every frame, so (per the animated-layer guidance in AGENTS.md)
    # this asserts gradient-colour PRESENCE sampled over several frames rather than
    # comparing one still frame. A very short repeat period keeps many concentric
    # rings on screen so both ends of the gradient are visible at any moment.
    @frontend_python
    def warm_to_cool(t: float) -> str:
        # t -> 0 (innermost ring) is red; t -> 1 (outer edge) is blue.
        red = int(255 * min(1.0, max(0.0, 1.0 - t)))
        blue = int(255 * min(1.0, max(0.0, t)))
        return f"rgba({red},40,{blue},{max(0.0, 1.0 - 0.6 * t)})"

    @frontend_python
    def cool_to_warm(t: float) -> str:
        # Reversed: t -> 0 is blue, t -> 1 is red.
        red = int(255 * min(1.0, max(0.0, t)))
        blue = int(255 * min(1.0, max(0.0, 1.0 - t)))
        return f"rgba({red},40,{blue},{max(0.0, 1.0 - 0.6 * t)})"

    rings = [
        RingDatum(
            lat=0,
            lng=0,
            altitude=0.02,
            max_radius=18,
            propagation_speed=6,
            repeat_period=100,
        )
    ]

    config = _make_config(
        RingsLayerConfig(
            rings_data=rings, ring_color_fn=warm_to_cool, ring_resolution=64
        ),
        globe_flat_texture_data_url,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    page_session.wait_for_timeout(800)

    # The gradient renders: both ends are present, and the centre (t -> 0) is warm.
    initial = _sample_ring_colours(page_session, canvas_capture)
    assert initial["warm"] > 0, initial
    assert initial["cool"] > 0, initial
    assert initial["centre_warm"] > initial["centre_cool"], initial

    # Runtime swap flips the gradient: the centre is now cool.
    widget.set_rings_color_fn(cool_to_warm)
    page_session.wait_for_timeout(800)
    swapped = _sample_ring_colours(page_session, canvas_capture)
    assert swapped["warm"] > 0, swapped
    assert swapped["cool"] > 0, swapped
    assert swapped["centre_cool"] > swapped["centre_warm"], swapped

    # Passing None restores the per-datum RingDatum.color accessor (default
    # #ffffaa), exercising the colorFnAccessorDefaults reset path: yellow rings
    # appear (older gradient rings keep propagating out until they expire).
    widget.set_rings_color_fn(None)
    page_session.wait_for_timeout(1200)
    reset = _sample_ring_colours(page_session, canvas_capture)
    assert reset["yellow"] > 0, reset


@pytest.mark.usefixtures("solara_test")
def test_ring_color_fn_static_initial(
    page_session: Page, canvas_capture, globe_flat_texture_data_url
) -> None:
    # A static ring (propagation_speed=0, repeat_period=0) is emitted exactly once,
    # at full max_radius, coloured interpolator(0). Because three-globe captures
    # ringColor at emission, a configured gradient must be bound *before* the ring
    # data is applied; otherwise the ring is emitted with its per-datum default of
    # yellow #ffffaa while MicroPython loads and never picks up the gradient. This is a
    # stable (non-animated) capture, so it directly exercises that initial-config
    # binding without the timing sensitivity of a propagating ring.
    @frontend_python
    def warm_to_cool(t: float) -> str:
        # interpolator(0) is opaque red; the per-datum default is yellow #ffffaa.
        red = int(255 * min(1.0, max(0.0, 1.0 - t)))
        blue = int(255 * min(1.0, max(0.0, t)))
        return f"rgba({red},40,{blue},1.0)"

    rings = [
        RingDatum(
            lat=0,
            lng=0,
            altitude=0.02,
            max_radius=14,
            propagation_speed=0,
            repeat_period=0,
        )
    ]

    config = _make_config(
        RingsLayerConfig(
            rings_data=rings, ring_color_fn=warm_to_cool, ring_resolution=64
        ),
        globe_flat_texture_data_url,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    # Allow MicroPython to load and the bind-then-emit sequence to complete.
    page_session.wait_for_timeout(2500)
    colours = _sample_ring_colours(page_session, canvas_capture, frames=4)

    # The ring shows the gradient's t=0 colour (warm/red), not the per-datum
    # yellow default -- i.e. the callback was bound before the ring was emitted.
    assert colours["warm"] > 0, colours
    assert colours["yellow"] == 0, colours
