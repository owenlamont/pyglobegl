from IPython.display import display
import pytest

from pyglobegl import GlobeWidget


@pytest.mark.ui
def test_solara_widget_renders(solara_test, page_session) -> None:
    widget = GlobeWidget()
    display(widget)

    page_session.wait_for_function(
        "document.querySelector('canvas, .jupyter-widgets') !== null", timeout=20000
    )
    has_widget = page_session.evaluate(
        "document.querySelector('canvas, .jupyter-widgets') !== null"
    )
    assert has_widget
