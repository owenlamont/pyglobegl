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
def test_globe_material_spec(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
) -> None:
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

    def _assert_capture(label: str) -> None:
        captured_image = canvas_capture(page_session)
        reference_path = canvas_reference_path(label)
        if not reference_path.exists():
            reference_path.parent.mkdir(parents=True, exist_ok=True)
            captured_image.save(reference_path)
            raise AssertionError(
                "Reference image missing. Saved capture to "
                f"{reference_path}; verify and re-run."
            )
        try:
            score = canvas_compare_images(captured_image, reference_path)
            passed = score >= canvas_similarity_threshold
        except Exception:
            canvas_save_capture(captured_image, label, False)
            raise
        canvas_save_capture(captured_image, label, passed)
        assert passed, (
            "Captured image similarity below threshold. "
            f"Score: {score:.4f} (threshold {canvas_similarity_threshold:.4f})."
        )

    _assert_capture("test_globe_material_spec")
    widget.set_globe_material(updated_material.model_dump(mode="json"))
    page_session.wait_for_timeout(200)
    _assert_capture("test_globe_material_spec-updated")
