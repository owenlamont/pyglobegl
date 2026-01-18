from collections.abc import Callable
from pathlib import Path
from typing import Any

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
        self._globe_ready_handlers: list[Callable[[], None]] = []
        self._globe_click_handlers: list[Callable[[dict[str, float]], None]] = []
        self._globe_right_click_handlers: list[Callable[[dict[str, float]], None]] = []
        self.on_msg(self._handle_frontend_message)
        self.config = config.model_dump(
            by_alias=True, exclude_none=True, exclude_defaults=True
        )

    def on_globe_ready(self, handler: Callable[[], None]) -> None:
        """Register a callback fired when the globe is ready."""
        self._globe_ready_handlers.append(handler)

    def on_globe_click(self, handler: Callable[[dict[str, float]], None]) -> None:
        """Register a callback fired on globe left-clicks."""
        self._globe_click_handlers.append(handler)

    def on_globe_right_click(self, handler: Callable[[dict[str, float]], None]) -> None:
        """Register a callback fired on globe right-clicks."""
        self._globe_right_click_handlers.append(handler)

    def _handle_frontend_message(
        self, _widget: "GlobeWidget", message: dict[str, Any], _buffers: list[bytes]
    ) -> None:
        msg_type = message.get("type")
        payload = message.get("payload")
        if msg_type == "globe_ready":
            for handler in self._globe_ready_handlers:
                handler()
        elif msg_type == "globe_click" and isinstance(payload, dict):
            for handler in self._globe_click_handlers:
                handler(payload)
        elif msg_type == "globe_right_click" and isinstance(payload, dict):
            for handler in self._globe_right_click_handlers:
                handler(payload)
