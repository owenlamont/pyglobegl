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
        PathsLayerConfig(paths_data=paths_data, path_transition_duration=0),
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
        PathsLayerConfig(paths_data=paths_data, path_transition_duration=0),
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
def test_path_transition_duration(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.98
    # Initial: Red line along the equator (centered).
    initial_paths = [PathDatum(path=[(0, -45), (0, 45)], color="#ff0000")]
    # Updated: Same line but different color for visibility.
    updated_paths = [PathDatum(path=[(0, -45), (0, 45)], color="#00ff00")]

    config = _make_config(
        globe_flat_texture_data_url,
        PathsLayerConfig(paths_data=initial_paths, path_transition_duration=1200),
        lat=0,
        lng=0,
        altitude=1.5,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    page_session.wait_for_timeout(1400)
    canvas_assert_capture(page_session, "initial", canvas_similarity_threshold)

    widget.set_path_transition_duration(0)
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
        PathsLayerConfig(paths_data=paths_data, path_transition_duration=0),
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
        PathsLayerConfig(paths_data=paths_data, path_transition_duration=0),
        altitude=1.7,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(page_session, "solid", canvas_similarity_threshold)

    widget.update_path(path_id, dash_length=0.1, dash_gap=0.05)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "dashed", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_path_color_gradient(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.97
    path_id = uuid4()
    paths_data = [
        PathDatum(
            id=path_id,
            path=[(-30, -10), (0, 10), (30, -10)],
            color=["#ff0000", "#00ff00", "#0000ff"],
        )
    ]
    updated_paths = [
        PathDatum(
            id=path_id,
            path=[(-30, -10), (0, 10), (30, -10)],
            color=["#ffff00", "#ff00ff", "#00ffff"],
        )
    ]

    config = _make_config(
        globe_flat_texture_data_url,
        PathsLayerConfig(paths_data=paths_data, path_transition_duration=0),
        altitude=1.6,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(page_session, "gradient-initial", canvas_similarity_threshold)

    widget.set_paths_data(updated_paths)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "gradient-updated", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_path_3d_coordinates(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.98
    path_id = uuid4()
    paths_data = [
        PathDatum(
            id=path_id,
            path=[(-20, -10, 0.0), (0, 20, 0.3), (20, -10, 0.0)],
            color="#ffcc00",
        )
    ]
    updated_paths = [
        PathDatum(
            id=path_id,
            path=[(-20, -10, 0.2), (0, 20, 0.6), (20, -10, 0.2)],
            color="#ffcc00",
        )
    ]

    config = _make_config(
        globe_flat_texture_data_url,
        PathsLayerConfig(paths_data=paths_data, path_transition_duration=0),
        altitude=1.8,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(page_session, "3d-initial", canvas_similarity_threshold)

    widget.set_paths_data(updated_paths)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "3d-updated", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_path_resolution(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.97
    paths_data = [PathDatum(path=[(-45, -20), (45, 20)], color="#00ffcc")]

    config = _make_config(
        globe_flat_texture_data_url,
        PathsLayerConfig(paths_data=paths_data, path_transition_duration=0),
        altitude=1.7,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    widget.set_path_resolution(1)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "resolution-low", canvas_similarity_threshold)

    widget.set_path_resolution(8)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "resolution-high", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_path_dash_initial_gap(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.98
    path_id = uuid4()
    paths_data = [
        PathDatum(
            id=path_id,
            path=[(-20, 0), (0, 20), (20, 0)],
            color="#ffcc00",
            dash_length=0.12,
            dash_gap=0.06,
            dash_initial_gap=0.0,
        )
    ]

    config = _make_config(
        globe_flat_texture_data_url,
        PathsLayerConfig(paths_data=paths_data, path_transition_duration=0),
        altitude=1.7,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(page_session, "gap-0", canvas_similarity_threshold)

    widget.update_path(path_id, dash_initial_gap=0.3)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "gap-0.3", canvas_similarity_threshold)


@pytest.mark.usefixtures("solara_test")
def test_path_multilinestring_source(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.98
    geopandas = pytest.importorskip("geopandas")
    from shapely.geometry import MultiLineString

    from pyglobegl.geopandas import paths_from_gdf

    gdf = geopandas.GeoDataFrame(
        {"geometry": [MultiLineString([[(-35, -15), (-5, 15)], [(5, -15), (35, 15)]])]},
        geometry="geometry",
        crs="EPSG:4326",
    )
    paths_data = paths_from_gdf(gdf)

    updated_gdf = geopandas.GeoDataFrame(
        {"geometry": [MultiLineString([[(-35, 15), (-5, -15)], [(5, 15), (35, -15)]])]},
        geometry="geometry",
        crs="EPSG:4326",
    )
    updated_paths = paths_from_gdf(updated_gdf)

    config = _make_config(
        globe_flat_texture_data_url,
        PathsLayerConfig(paths_data=paths_data, path_transition_duration=0),
        altitude=1.6,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(
        page_session, "multiline-initial", canvas_similarity_threshold
    )

    widget.set_paths_data(updated_paths)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(
        page_session, "multiline-updated", canvas_similarity_threshold
    )


@pytest.mark.usefixtures("solara_test")
def test_path_dash_animate_time(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.96
    path_id = uuid4()
    paths_data = [
        PathDatum(
            id=path_id,
            path=[(-25, 0), (0, 25), (25, 0)],
            color="#66ccff",
            dash_length=0.12,
            dash_gap=0.06,
            dash_initial_gap=0.0,
            dash_animate_time=0.0,
        )
    ]

    config = _make_config(
        globe_flat_texture_data_url,
        PathsLayerConfig(paths_data=paths_data, path_transition_duration=0),
        altitude=1.7,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(page_session, "animate-off", canvas_similarity_threshold)

    widget.update_path(path_id, dash_animate_time=400.0)
    page_session.wait_for_timeout(300)
    canvas_assert_capture(page_session, "animate-on", canvas_similarity_threshold)
