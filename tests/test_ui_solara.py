from __future__ import annotations

from typing import TYPE_CHECKING

from IPython.display import display
import pytest

from pyglobegl import GlobeWidget


if TYPE_CHECKING:
    from playwright.sync_api import Page


@pytest.mark.usefixtures("solara_test")
def test_solara_widget_renders(page_session: Page, ui_artifacts_writer) -> None:
    widget = GlobeWidget()
    display(widget)

    try:
        page_session.wait_for_function(
            "document.querySelector('canvas, .jupyter-widgets') !== null", timeout=20000
        )
    except Exception:
        ui_artifacts_writer(page_session, "solara-widget-timeout")
        raise
    has_widget = page_session.evaluate(
        "document.querySelector('canvas, .jupyter-widgets') !== null"
    )
    assert has_widget
