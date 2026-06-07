from __future__ import annotations

from typing import TYPE_CHECKING

from IPython.display import display
from pydantic import AnyUrl
import pytest

from pyglobegl import (
    frontend_python,
    GlobeConfig,
    GlobeInitConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeViewConfig,
    GlobeWidget,
    PointDatum,
    PointOfView,
    PointsLayerConfig,
)


if TYPE_CHECKING:
    from playwright.sync_api import Page


# globe.gl wires every layer's *Label accessor into a single hover tooltip, so the
# frontend binds the label callback directly (datum -> string), unlike the
# (t) -> colour gradient accessors. These tests assert that binding for one
# representative layer (points), plus the per-datum "label" field default that the
# frontend pre-binds for all eight one-to-one-datum layers.
_LABEL_ACCESSORS = [
    "pointLabel",
    "arcLabel",
    "pathLabel",
    "polygonLabel",
    "hexPolygonLabel",
    "tileLabel",
    "particleLabel",
    "labelLabel",
]


@frontend_python
def _point_tooltip(datum):
    label = "?"
    if isinstance(datum, dict):
        label = str(datum.get("label", "?"))
    return f"PT {label}"


def _base_config(
    globe_earth_texture_url: AnyUrl, points: PointsLayerConfig | None = None
) -> GlobeConfig:
    return GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#000000"),
        globe=GlobeLayerConfig(
            globe_image_url=globe_earth_texture_url,
            show_atmosphere=False,
            show_graticules=False,
        ),
        points=points if points is not None else PointsLayerConfig(),
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.6), transition_ms=0
        ),
    )


def _wait_for_canvas(page_session: Page) -> None:
    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )
    page_session.wait_for_function(
        """
        () => {
          const canvas = document.querySelector("canvas");
          if (!canvas) {
            return false;
          }
          const dataUrl = canvas.toDataURL("image/png");
          return dataUrl.length > 2000;
        }
        """,
        timeout=20000,
    )


def _wait_for_point_label_text(
    page_session: Page, expected_text: str, timeout_ms: int = 20000
) -> None:
    page_session.wait_for_function(
        """
        (text) => {
          const globe = globalThis.__pyglobegl_globe;
          if (!globe || typeof globe.pointLabel !== "function") {
            return false;
          }
          const accessor = globe.pointLabel();
          if (typeof accessor !== "function") {
            return false;
          }
          const value = accessor({ label: "SAMPLE", name: "NAME" });
          return typeof value === "string" && value.includes(text);
        }
        """,
        arg=expected_text,
        timeout=timeout_ms,
    )


@pytest.mark.usefixtures("solara_test")
def test_point_label_callback_tooltip_binds(
    page_session: Page, globe_earth_texture_url
) -> None:
    widget = GlobeWidget(
        config=_base_config(
            globe_earth_texture_url,
            points=PointsLayerConfig(
                points_data=[PointDatum(lat=0, lng=0, label="HOME")],
                point_label=_point_tooltip,
                points_transition_duration=0,
            ),
        )
    )
    display(widget)

    _wait_for_canvas(page_session)
    # The callback receives the datum and returns the tooltip string directly.
    _wait_for_point_label_text(page_session, "PT SAMPLE")


@pytest.mark.usefixtures("solara_test")
def test_point_label_constant_string_binds(
    page_session: Page, globe_earth_texture_url
) -> None:
    widget = GlobeWidget(
        config=_base_config(
            globe_earth_texture_url,
            points=PointsLayerConfig(
                points_data=[PointDatum(lat=0, lng=0, label="HOME")],
                point_label="CONST TIP",
                points_transition_duration=0,
            ),
        )
    )
    display(widget)

    _wait_for_canvas(page_session)
    # A constant string binds as () => value: the same tooltip for every datum.
    _wait_for_point_label_text(page_session, "CONST TIP")


@pytest.mark.usefixtures("solara_test")
def test_label_accessors_default_to_label_field(
    page_session: Page, globe_earth_texture_url
) -> None:
    widget = GlobeWidget(config=_base_config(globe_earth_texture_url))
    display(widget)

    _wait_for_canvas(page_session)
    accessors = page_session.evaluate(
        """
        (names) => {
          const globe = globalThis.__pyglobegl_globe;
          return names.map((name) => globe[name]());
        }
        """,
        _LABEL_ACCESSORS,
    )
    # With no label set, the frontend pre-binds the per-datum "label" field
    # accessor for every layer (globe.gl's own default is the "name" field).
    assert accessors == ["label"] * len(_LABEL_ACCESSORS)
