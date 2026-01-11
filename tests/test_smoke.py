from pathlib import Path

from pyglobegl import GlobeWidget, widget as widget_module


def test_widget_smoke() -> None:
    widget = GlobeWidget()
    assert widget is not None
    if widget_module.__file__ is None:
        raise AssertionError("widget module file is missing")
    expected_esm = Path(widget_module.__file__).with_name("_static") / "index.js"
    assert expected_esm.exists()
    assert isinstance(widget._esm, (Path, str))
