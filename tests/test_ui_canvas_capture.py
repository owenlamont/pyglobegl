from __future__ import annotations

from typing import TYPE_CHECKING

from IPython.display import display

from pyglobegl import GlobeConfig, GlobeLayoutConfig, GlobeWidget


if TYPE_CHECKING:
    from playwright.sync_api import Page


def test_solara_canvas_capture_baseline(
    solara_test, page_session: Page, ui_artifacts_writer
) -> None:
    config = GlobeConfig(
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#00ff00")
    )
    widget = GlobeWidget(config=config)
    display(widget)

    try:
        page_session.wait_for_function(
            "document.querySelector('canvas, .jupyter-widgets') !== null", timeout=20000
        )
    except Exception:
        ui_artifacts_writer(page_session, "canvas-capture-timeout")
        raise

    page_session.evaluate(
        """
        () => {
          document.body.style.backgroundColor = "#111111";
          const canvas = document.querySelector("canvas");
          if (canvas) {
            canvas.style.border = "4px solid magenta";
          }
        }
        """
    )
    ui_artifacts_writer(page_session, "canvas-capture-baseline")
