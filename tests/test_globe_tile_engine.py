from __future__ import annotations

import io
from typing import TYPE_CHECKING

from IPython.display import display
import pytest

from pyglobegl import (
    GlobeConfig,
    GlobeInitConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeWidget,
)


if TYPE_CHECKING:
    from playwright.sync_api import Page


def _wait_for_canvas_color(page_session: Page, color: str) -> None:
    page_session.wait_for_function(
        """
        async ({ targetColor }) => {
          const container = document.querySelector(".scene-container");
          const canvas = container ? container.querySelector("canvas") : null;
          if (!canvas) {
            return false;
          }
          const dataUrl = canvas.toDataURL("image/png");
          if (!dataUrl || dataUrl.length < 2000) {
            return false;
          }
          const img = new Image();
          img.src = dataUrl;
          await img.decode();
          const offscreen = document.createElement("canvas");
          offscreen.width = img.width;
          offscreen.height = img.height;
          const ctx = offscreen.getContext("2d");
          if (!ctx) {
            return false;
          }
          ctx.drawImage(img, 0, 0);
          const midX = Math.floor(img.width / 2);
          const midY = Math.floor(img.height / 2);
          const data = ctx.getImageData(midX, midY, 1, 1).data;
          const hex = (value) => value.toString(16).padStart(2, "0");
          const pixel = `#${hex(data[0])}${hex(data[1])}${hex(data[2])}`;
          return pixel.toLowerCase() === targetColor.toLowerCase();
        }
        """,
        arg={"targetColor": color},
        timeout=20000,
    )


def _make_tile_bytes(color: tuple[int, int, int]) -> bytes:
    from PIL import Image

    image = Image.new("RGB", (64, 64), color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.mark.usefixtures("solara_test")
def test_globe_tile_engine_cache_reset(
    page_session: Page,
    canvas_capture,
    canvas_reference_path,
    canvas_compare_images,
    canvas_save_capture,
    globe_tile_server,
) -> None:
    base_url, set_tile_bytes = globe_tile_server
    set_tile_bytes(_make_tile_bytes((255, 0, 0)))
    tile_template = f"{base_url}/{{z}}/{{x}}/{{y}}.png"

    base_config = GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#000000"),
        globe=GlobeLayerConfig(
            show_atmosphere=False,
            show_graticules=False,
            globe_tile_engine_url=tile_template,
        ),
    )
    widget = GlobeWidget(config=base_config)
    display(widget)

    page_session.wait_for_function(
        "document.querySelector('canvas, .jupyter-widgets') !== null", timeout=20000
    )
    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )
    _wait_for_canvas_color(page_session, "#ff0000")

    initial_image = canvas_capture(page_session)
    canvas_save_capture(
        initial_image, "test_globe_tile_engine_cache_reset-initial", True
    )
    initial_ref = canvas_reference_path("test_globe_tile_engine_cache_reset-initial")
    if not initial_ref.exists():
        raise AssertionError(
            f"Reference image missing. Save the capture to {initial_ref} and re-run."
        )
    canvas_compare_images(initial_image, initial_ref)

    set_tile_bytes(_make_tile_bytes((0, 255, 0)))

    cached_image = canvas_capture(page_session)
    canvas_save_capture(cached_image, "test_globe_tile_engine_cache_reset-cached", True)
    cached_ref = canvas_reference_path("test_globe_tile_engine_cache_reset-cached")
    if not cached_ref.exists():
        raise AssertionError(
            f"Reference image missing. Save the capture to {cached_ref} and re-run."
        )
    canvas_compare_images(cached_image, cached_ref)

    widget.globe_tile_engine_clear_cache()
    disabled_config = base_config.model_dump(
        by_alias=True, exclude_none=True, exclude_defaults=True
    )
    disabled_globe = dict(disabled_config.get("globe", {}))
    disabled_globe["globeTileEngineUrl"] = None
    disabled_config["globe"] = disabled_globe
    widget.config = disabled_config
    widget.config = base_config.model_dump(
        by_alias=True, exclude_none=True, exclude_defaults=True
    )
    _wait_for_canvas_color(page_session, "#00ff00")

    cleared_image = canvas_capture(page_session)
    canvas_save_capture(
        cleared_image, "test_globe_tile_engine_cache_reset-cleared", True
    )
    cleared_ref = canvas_reference_path("test_globe_tile_engine_cache_reset-cleared")
    if not cleared_ref.exists():
        raise AssertionError(
            f"Reference image missing. Save the capture to {cleared_ref} and re-run."
        )
    canvas_compare_images(cleared_image, cleared_ref)


@pytest.mark.usefixtures("solara_test")
def test_globe_tile_engine_url_setter(
    page_session: Page,
    canvas_assert_capture,
    globe_flat_texture_data_url,
    globe_tile_server,
) -> None:
    canvas_similarity_threshold = 0.99
    base_url, set_tile_bytes = globe_tile_server
    set_tile_bytes(_make_tile_bytes((255, 0, 0)))
    tile_template = f"{base_url}/{{z}}/{{x}}/{{y}}.png"

    config = GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#000000"),
        globe=GlobeLayerConfig(
            globe_image_url=globe_flat_texture_data_url,
            show_atmosphere=False,
            show_graticules=False,
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

    canvas_assert_capture(page_session, "initial", canvas_similarity_threshold)
    widget.set_globe_tile_engine_url(tile_template)
    _wait_for_canvas_color(page_session, "#ff0000")
    canvas_assert_capture(page_session, "updated", canvas_similarity_threshold)
