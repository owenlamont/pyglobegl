from pathlib import Path

import anywidget
from ipywidgets import Layout
import traitlets


class GlobeWidget(anywidget.AnyWidget):
    """AnyWidget wrapper around globe.gl."""

    _esm = Path(__file__).with_name("_static") / "index.js"
    # Placeholder synced state for future configuration.
    options = traitlets.Dict().tag(sync=True)

    def __init__(self, **kwargs: object) -> None:
        if "layout" not in kwargs:
            kwargs["layout"] = Layout(width="100%", height="auto")
        super().__init__(**kwargs)
