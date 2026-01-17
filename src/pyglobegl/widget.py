from pathlib import Path

import anywidget
from ipywidgets import Layout
import traitlets

from pyglobegl.config import GlobeConfig


class GlobeWidget(anywidget.AnyWidget):
    """AnyWidget wrapper around globe.gl."""

    _esm = Path(__file__).with_name("_static") / "index.js"
    config = traitlets.Dict().tag(sync=True)

    def __init__(
        self,
        config: GlobeConfig | None = None,
        layout: Layout | None = None,
        **kwargs: object,
    ) -> None:
        if layout is None:
            layout = Layout(width="100%", height="auto")
        if config is None:
            config = GlobeConfig()
        if not isinstance(config, GlobeConfig):
            raise TypeError("config must be a GlobeConfig instance.")
        kwargs.setdefault("layout", layout)
        super().__init__(**kwargs)
        self.config = config.model_dump(
            by_alias=True, exclude_none=True, exclude_defaults=True
        )
