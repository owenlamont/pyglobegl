from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from IPython.display import display
from pydantic import AnyUrl, TypeAdapter
import pytest

from pyglobegl import (
    GlobeConfig,
    GlobeInitConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeViewConfig,
    GlobeWidget,
    PathDatum,
    PathsLayerConfig,
    PointOfView,
)


if TYPE_CHECKING:
    from playwright.sync_api import Page


_URL_ADAPTER = TypeAdapter(AnyUrl)


def _make_config(
    globe_texture_url: str,
    paths: PathsLayerConfig,
    *,
    lat: float = 0,
    lng: float = 0,
    altitude: float = 1.6,
    width: int = 256,
    height: int = 256,
) -> GlobeConfig:
    globe_url = _URL_ADAPTER.validate_python(globe_texture_url)
    return GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(
            width=width, height=height, background_color="#000000"
        ),
        globe=GlobeLayerConfig(
            globe_image_url=globe_url, show_atmosphere=False, show_graticules=False
        ),
        paths=paths,
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=lat, lng=lng, altitude=altitude),
            transition_ms=0,
        ),
    )


def _await_globe_ready(page_session: Page) -> None:
    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )
    page_session.wait_for_timeout(250)


@pytest.mark.usefixtures("solara_test")
def test_paths_accessors(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.97
    paths_data = [
        PathDatum(
            path=[(-20, -20), (0, 0), (20, -20)], color="#ff66cc", dash_length=1.0
        ),
        PathDatum(path=[(-20, 20), (0, 0), (20, 20)], color="#66ccff", dash_length=1.0),
    ]
    updated_paths = [PathDatum(path=[(-10, -10), (10, 10)], color="#ffcc00")]

    config = _make_config(
        globe_flat_texture_data_url,
        PathsLayerConfig(paths_data=paths_data, paths_transition_duration=0),
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(page_session, "initial", canvas_similarity_threshold)

    widget.set_paths_data(updated_paths)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "updated", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_path_label_tooltip(
    page_session: Page, globe_hoverer, globe_flat_texture_data_url
) -> None:
    paths_data = [
        PathDatum(path=[(-10, 0), (10, 0)], label="Initial path", color="#ffcc00")
    ]
    updated_paths = [
        PathDatum(path=[(-10, 0), (10, 0)], label="Updated path", color="#ffcc00")
    ]

    config = _make_config(
        globe_flat_texture_data_url,
        PathsLayerConfig(paths_data=paths_data, paths_transition_duration=0),
        altitude=1.7,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    globe_hoverer(page_session)
    page_session.wait_for_function(
        """
        () => {
          const tooltip = document.querySelector(".float-tooltip-kap");
          if (!tooltip) {
            return false;
          }
          const style = window.getComputedStyle(tooltip);
          if (style.display === "none") {
            return false;
          }
          return (tooltip.textContent || "").includes("Initial path");
        }
        """,
        timeout=20000,
    )

    widget.set_paths_data(updated_paths)
    page_session.wait_for_timeout(100)
    globe_hoverer(page_session)
    page_session.wait_for_function(
        """
        () => {
          const tooltip = document.querySelector(".float-tooltip-kap");
          if (!tooltip) {
            return false;
          }
          const style = window.getComputedStyle(tooltip);
          if (style.display === "none") {
            return false;
          }
          return (tooltip.textContent || "").includes("Updated path");
        }
        """,
        timeout=20000,
    )


@pytest.mark.usefixtures("solara_test")
def test_paths_transition_duration(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.98
    # Initial: A vertical line from South Pole to North Pole at prime meridian
    initial_paths = [
        PathDatum(
            path=[(0, -90), (0, 90)],
            color="#ff00ff",  # Magenta
        )
    ]
    # Updated: A vertical line from South Pole to North Pole at 45 degrees East
    updated_paths = [
        PathDatum(
            path=[(0, -90), (0, 90)],
            color="#00ffff",  # Cyan
        )
    ]
    updated_paths[0] = PathDatum(
        path=[(45, -90), (45, 90)],
        color="#00ffff",  # Cyan
    )

    config = _make_config(
        globe_flat_texture_data_url,
        PathsLayerConfig(
            paths_data=initial_paths, paths_transition_duration=1200, path_stroke=None
        ),
        lat=0,
        lng=20,  # Center view between 0 and 45 degrees longitude
        altitude=2.0,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(page_session, "initial", canvas_similarity_threshold)

    widget.set_paths_transition_duration(0)
    widget.set_paths_data(updated_paths)
    page_session.wait_for_timeout(500)
    canvas_assert_capture(page_session, "updated", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_path_stroke(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.99
    path_id = uuid4()
    paths_data = [
        PathDatum(id=path_id, path=[(-20, 0), (0, 20), (20, 0)], color="#ffcc00")
    ]
    config = _make_config(
        globe_flat_texture_data_url,
        PathsLayerConfig(
            paths_data=paths_data, paths_transition_duration=0, path_stroke=None
        ),
        altitude=1.7,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(page_session, "thin", canvas_similarity_threshold)

    widget._set_layer_prop("paths", widget._paths_props, "pathStroke", 2.0)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "thick", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_path_dash(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.99
    path_id = uuid4()
    paths_data = [
        PathDatum(
            id=path_id,
            path=[(-20, 0), (0, 20), (20, 0)],
            color="#ffcc00",
            dash_length=1.0,
            dash_gap=0.0,
        )
    ]
    config = _make_config(
        globe_flat_texture_data_url,
        PathsLayerConfig(paths_data=paths_data, paths_transition_duration=0),
        altitude=1.7,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(page_session, "solid", canvas_similarity_threshold)

    widget.update_path(path_id, dash_length=0.1, dash_gap=0.05)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "dashed", canvas_similarity_threshold)
