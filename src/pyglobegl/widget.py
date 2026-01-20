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
        self._point_click_handlers: list[
            Callable[[dict[str, Any], dict[str, float]], None]
        ] = []
        self._point_right_click_handlers: list[
            Callable[[dict[str, Any], dict[str, float]], None]
        ] = []
        self._point_hover_handlers: list[
            Callable[[dict[str, Any] | None, dict[str, Any] | None], None]
        ] = []
        self._message_handlers: dict[str, Callable[[Any], None]] = {
            "globe_ready": lambda _payload: self._dispatch_globe_ready(),
            "globe_click": self._dispatch_globe_click,
            "globe_right_click": self._dispatch_globe_right_click,
            "point_click": self._dispatch_point_click,
            "point_right_click": self._dispatch_point_right_click,
            "point_hover": self._dispatch_point_hover,
        }
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

    def on_point_click(
        self, handler: Callable[[dict[str, Any], dict[str, float]], None]
    ) -> None:
        """Register a callback fired on point left-clicks."""
        self._point_click_handlers.append(handler)

    def on_point_right_click(
        self, handler: Callable[[dict[str, Any], dict[str, float]], None]
    ) -> None:
        """Register a callback fired on point right-clicks."""
        self._point_right_click_handlers.append(handler)

    def on_point_hover(
        self, handler: Callable[[dict[str, Any] | None, dict[str, Any] | None], None]
    ) -> None:
        """Register a callback fired on point hover events."""
        self._point_hover_handlers.append(handler)

    def globe_tile_engine_clear_cache(self) -> None:
        """Clear the globe tile engine cache."""
        self.send({"type": "globe_tile_engine_clear_cache"})

    def _handle_frontend_message(
        self, _widget: "GlobeWidget", message: dict[str, Any], _buffers: list[bytes]
    ) -> None:
        msg_type = message.get("type")
        if not isinstance(msg_type, str):
            return
        handler = self._message_handlers.get(msg_type)
        if handler is None:
            return
        handler(message.get("payload"))

    def _dispatch_globe_ready(self) -> None:
        for handler in self._globe_ready_handlers:
            handler()

    def _dispatch_globe_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        for handler in self._globe_click_handlers:
            handler(payload)

    def _dispatch_globe_right_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        for handler in self._globe_right_click_handlers:
            handler(payload)

    def _dispatch_point_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        point = payload.get("point")
        coords = payload.get("coords")
        if isinstance(point, dict) and isinstance(coords, dict):
            for handler in self._point_click_handlers:
                handler(point, coords)

    def _dispatch_point_right_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        point = payload.get("point")
        coords = payload.get("coords")
        if isinstance(point, dict) and isinstance(coords, dict):
            for handler in self._point_right_click_handlers:
                handler(point, coords)

    def _dispatch_point_hover(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        point = payload.get("point")
        prev_point = payload.get("prev_point")
        if point is not None and not isinstance(point, dict):
            return
        if prev_point is not None and not isinstance(prev_point, dict):
            return
        for handler in self._point_hover_handlers:
            handler(point, prev_point)
