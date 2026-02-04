from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

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
    LabelDatum,
    LabelsLayerConfig,
    PointOfView,
)


if TYPE_CHECKING:
    from playwright.sync_api import Page

_URL_ADAPTER = TypeAdapter(AnyUrl)
_FONT_PATH = (
    Path(__file__).resolve().parent
    / "assets"
    / "fonts"
    / "optimer_regular.typeface.json"
)


def _make_config(labels: LabelsLayerConfig, globe_texture_url: str) -> GlobeConfig:
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
        labels=labels,
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.8), transition_ms=0
        ),
    )


def _await_globe_ready(page_session: Page) -> None:
    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )
    page_session.wait_for_timeout(250)


@pytest.mark.usefixtures("solara_test")
def test_labels_accessors(
    page_session: Page, canvas_assert_capture, globe_flat_texture_data_url
) -> None:
    canvas_similarity_threshold = 0.96
    labels = [
        LabelDatum(
            lat=0,
            lng=0,
            altitude=0.02,
            text="Alpha",
            size=2.4,
            color="#ffcc00",
            include_dot=True,
            dot_radius=1.1,
            dot_orientation="bottom",
        ),
        LabelDatum(
            lat=-12,
            lng=18,
            altitude=0.03,
            text="Gamma",
            size=1.8,
            color="#ff66cc",
            include_dot=True,
            dot_radius=0.9,
            dot_orientation="right",
        ),
    ]
    updated = [
        LabelDatum(
            lat=15,
            lng=-8,
            altitude=0.05,
            text="Beta",
            size=2.8,
            color="#00ccff",
            rotation=25,
            include_dot=True,
            dot_radius=1.3,
            dot_orientation="top",
        ),
        LabelDatum(
            lat=-5,
            lng=-20,
            altitude=0.01,
            text="Delta",
            size=2.0,
            color="#66ff99",
            include_dot=True,
            dot_radius=1.0,
            dot_orientation="bottom",
        ),
    ]

    config = _make_config(
        LabelsLayerConfig(labels_data=labels, labels_transition_duration=0),
        globe_flat_texture_data_url,
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _await_globe_ready(page_session)
    canvas_assert_capture(page_session, "initial", canvas_similarity_threshold)

    widget.set_label_resolution(8)
    widget.set_label_type_face(json.loads(_FONT_PATH.read_text(encoding="utf-8")))
    widget.set_labels_data(updated)
    page_session.wait_for_timeout(100)
    canvas_assert_capture(page_session, "updated", canvas_similarity_threshold)
