from __future__ import annotations

from typing import TYPE_CHECKING

from IPython.display import display
import pytest

from pyglobegl import (
    GlobeConfig,
    GlobeInitConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeMaterialSpec,
    GlobeWidget,
)


if TYPE_CHECKING:
    from playwright.sync_api import Page


@pytest.mark.usefixtures("solara_test")
def test_globe_material_spec(page_session: Page, canvas_assert_capture) -> None:
    canvas_similarity_threshold = 0.9
    material = GlobeMaterialSpec(
        type="MeshPhongMaterial",
        params={"color": "#ff00ff", "emissive": "#00ff00", "wireframe": True},
    )
    updated_material = GlobeMaterialSpec(
        type="MeshBasicMaterial", params={"color": "#00ccff"}
    )
    config = GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#000000"),
        globe=GlobeLayerConfig(
            globe_material=material, show_atmosphere=False, show_graticules=False
        ),
    )
    widget = GlobeWidget(config=config)
    display(widget)

    page_session.wait_for_function(
        "document.querySelector('canvas, .jupyter-widgets') !== null", timeout=20000
    )
    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )

    canvas_assert_capture(page_session, "initial", canvas_similarity_threshold)
    widget.set_globe_material(updated_material.model_dump(mode="json"))
    page_session.wait_for_timeout(200)
    canvas_assert_capture(page_session, "updated", canvas_similarity_threshold)
