from pathlib import Path

import anywidget
import traitlets


class GlobeWidget(anywidget.AnyWidget):
    """AnyWidget wrapper around globe.gl."""

    _esm = Path(__file__).with_name("_static") / "index.js"
    # Placeholder synced state for future configuration.
    options = traitlets.Dict().tag(sync=True)
