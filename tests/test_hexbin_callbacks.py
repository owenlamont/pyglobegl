from __future__ import annotations

from threading import Event
import time
from typing import Any, TYPE_CHECKING

from IPython.display import display
from pydantic import AnyUrl
import pytest

from pyglobegl import (
    frontend_python,
    GlobeConfig,
    GlobeInitConfig,
    GlobeLayerConfig,
    GlobeLayoutConfig,
    GlobeViewConfig,
    GlobeWidget,
    HexBinLayerConfig,
    HexBinPointDatum,
    PointOfView,
)


if TYPE_CHECKING:
    from playwright.sync_api import Page


def _hexbin_config(
    globe_earth_texture_url: AnyUrl,
    *,
    merge: bool = False,
    hex_label: str | Any | None = None,
    points_data: list[HexBinPointDatum] | None = None,
) -> GlobeConfig:
    return GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#000000"),
        globe=GlobeLayerConfig(
            globe_image_url=globe_earth_texture_url,
            show_atmosphere=False,
            show_graticules=False,
        ),
        hex_bin=HexBinLayerConfig(
            hex_bin_points_data=points_data
            if points_data is not None
            else [
                HexBinPointDatum(lat=0, lng=0, weight=6.0),
                HexBinPointDatum(lat=2, lng=2, weight=4.0),
                HexBinPointDatum(lat=-2, lng=-2, weight=3.0),
            ],
            hex_bin_resolution=0,
            hex_altitude=0.35,
            hex_top_color="#ffd166",
            hex_side_color="#26547c",
            hex_label=hex_label,
            hex_bin_merge=merge,
            hex_transition_duration=0,
        ),
        view=GlobeViewConfig(
            point_of_view=PointOfView(lat=0, lng=0, altitude=1.6), transition_ms=0
        ),
    )


def _wait_for_canvas(page_session: Page) -> None:
    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )
    page_session.wait_for_function(
        """
        () => {
          const canvas = document.querySelector("canvas");
          if (!canvas) {
            return false;
          }
          const dataUrl = canvas.toDataURL("image/png");
          return dataUrl.length > 2000;
        }
        """,
        timeout=20000,
    )


def _wait_for_tooltip_text(
    page_session: Page, expected_text: str, timeout_ms: int = 60000
) -> None:
    page_session.wait_for_function(
        "document.querySelector('.scene-container') !== null", timeout=20000
    )

    sweep_offsets = [(0.50, 0.50)]
    sweep_offsets.extend(
        (x, y)
        for x in (0.15, 0.25, 0.35, 0.65, 0.75, 0.85)
        for y in (0.15, 0.25, 0.35, 0.65, 0.75, 0.85)
    )
    sweep_offsets.extend(
        [
            (0.50, 0.15),
            (0.50, 0.25),
            (0.50, 0.35),
            (0.50, 0.65),
            (0.50, 0.75),
            (0.50, 0.85),
            (0.15, 0.50),
            (0.25, 0.50),
            (0.35, 0.50),
            (0.65, 0.50),
            (0.75, 0.50),
            (0.85, 0.50),
        ]
    )

    def _tooltip_has_expected_text() -> bool:
        return bool(
            page_session.evaluate(
                """
                (text) => {
                  const tooltip = document.querySelector(".float-tooltip-kap");
                  if (!tooltip) {
                    return false;
                  }
                  const style = window.getComputedStyle(tooltip);
                  if (style.display === "none" || style.visibility === "hidden") {
                    return false;
                  }
                  return (tooltip.textContent || "").includes(text);
                }
                """,
                expected_text,
            )
        )

    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if _tooltip_has_expected_text():
            return

        for ratio_x, ratio_y in sweep_offsets:
            matched = bool(
                page_session.evaluate(
                    """
                    ({ text, ratioX, ratioY }) => {
                      const target = document.querySelector(".scene-container");
                      if (!target) {
                        return false;
                      }
                      const rect = target.getBoundingClientRect();
                      const x = rect.left + rect.width * ratioX;
                      const y = rect.top + rect.height * ratioY;
                      const opts = {
                        clientX: x,
                        clientY: y,
                        pageX: x + window.scrollX,
                        pageY: y + window.scrollY,
                        bubbles: true,
                        cancelable: true,
                        view: window,
                        pointerType: "mouse",
                        pointerId: 1,
                        isPrimary: true,
                      };
                      target.dispatchEvent(new PointerEvent("pointerover", opts));
                      target.dispatchEvent(new PointerEvent("pointerenter", opts));
                      target.dispatchEvent(new PointerEvent("pointermove", opts));
                      target.dispatchEvent(new MouseEvent("mouseover", opts));
                      target.dispatchEvent(new MouseEvent("mouseenter", opts));
                      target.dispatchEvent(new MouseEvent("mousemove", opts));

                      const tooltip = document.querySelector(".float-tooltip-kap");
                      if (!tooltip) {
                        return false;
                      }
                      const style = window.getComputedStyle(tooltip);
                      if (style.display === "none" || style.visibility === "hidden") {
                        return false;
                      }
                      return (tooltip.textContent || "").includes(text);
                    }
                    """,
                    {"text": expected_text, "ratioX": ratio_x, "ratioY": ratio_y},
                )
            )
            if matched:
                return
            page_session.wait_for_timeout(35)

        page_session.wait_for_timeout(90)
    raise TimeoutError(f"Tooltip text did not render within {timeout_ms}ms.")


@frontend_python
def _hex_label_fn(hexbin):
    sum_weight = 0.0
    if isinstance(hexbin, dict):
        sum_weight = float(hexbin.get("sumWeight", 0.0))
    return f"HEX TEST {int(sum_weight)}"


@frontend_python
def _hex_label_fn_using_get(hexbin):
    points = hexbin.get("points", [])
    first_weight = 0.0
    if points:
        first_weight = float(points[0].get("weight", 0.0))
    return f"HEX GET {len(points)} / {first_weight:.1f}"


@pytest.mark.usefixtures("solara_test")
def test_on_hexbin_click_callback(
    page_session: Page, globe_clicker, globe_earth_texture_url
) -> None:
    click_event = Event()
    payload: dict[str, Any] = {}

    def _on_click(hexbin: dict[str, Any], coords: dict[str, float]) -> None:
        payload["hexbin"] = hexbin
        payload["coords"] = coords
        click_event.set()

    widget = GlobeWidget(config=_hexbin_config(globe_earth_texture_url))
    widget.on_hexbin_click(_on_click)
    display(widget)

    _wait_for_canvas(page_session)
    globe_clicker(page_session, "left")

    assert click_event.wait(5), "Expected hexbin click callback to fire."
    assert isinstance(payload.get("hexbin"), dict)
    assert isinstance(payload.get("coords"), dict)


@pytest.mark.usefixtures("solara_test")
def test_on_hexbin_right_click_callback(
    page_session: Page, globe_clicker, globe_earth_texture_url
) -> None:
    click_event = Event()
    payload: dict[str, Any] = {}

    def _on_click(hexbin: dict[str, Any], coords: dict[str, float]) -> None:
        payload["hexbin"] = hexbin
        payload["coords"] = coords
        click_event.set()

    widget = GlobeWidget(config=_hexbin_config(globe_earth_texture_url))
    widget.on_hexbin_right_click(_on_click)
    display(widget)

    _wait_for_canvas(page_session)
    globe_clicker(page_session, "right")

    assert click_event.wait(5), "Expected hexbin right-click callback to fire."
    assert isinstance(payload.get("hexbin"), dict)
    assert isinstance(payload.get("coords"), dict)


@pytest.mark.usefixtures("solara_test")
def test_on_hexbin_hover_callback(
    page_session: Page, globe_hoverer, globe_earth_texture_url
) -> None:
    hover_event = Event()
    payload: dict[str, Any] = {}

    def _on_hover(hexbin: dict[str, Any] | None, prev: dict[str, Any] | None) -> None:
        payload["hexbin"] = hexbin
        payload["prev"] = prev
        hover_event.set()

    widget = GlobeWidget(config=_hexbin_config(globe_earth_texture_url))
    widget.on_hexbin_hover(_on_hover)
    display(widget)

    _wait_for_canvas(page_session)
    globe_hoverer(page_session)

    assert hover_event.wait(5), "Expected hexbin hover callback to fire."
    assert payload.get("hexbin") is None or isinstance(payload.get("hexbin"), dict)
    assert payload.get("prev") is None or isinstance(payload.get("prev"), dict)


@pytest.mark.usefixtures("solara_test")
def test_hexbin_merge_disables_click(
    page_session: Page, globe_clicker, globe_earth_texture_url
) -> None:
    click_event = Event()

    def _on_click(_: dict[str, Any], __: dict[str, float]) -> None:
        click_event.set()

    widget = GlobeWidget(config=_hexbin_config(globe_earth_texture_url, merge=True))
    widget.on_hexbin_click(_on_click)
    display(widget)

    _wait_for_canvas(page_session)
    globe_clicker(page_session, "left")

    assert not click_event.wait(1.5), "Hexbin click should not fire when merged."


@pytest.mark.usefixtures("solara_test")
def test_hexbin_label_frontend_python_tooltip_renders(
    page_session: Page, globe_earth_texture_url
) -> None:
    widget = GlobeWidget(
        config=_hexbin_config(
            globe_earth_texture_url,
            hex_label=_hex_label_fn,
            points_data=[HexBinPointDatum(lat=0, lng=0, weight=12.0)],
        )
    )
    display(widget)

    _wait_for_canvas(page_session)
    _wait_for_tooltip_text(page_session, "HEX TEST")


@pytest.mark.usefixtures("solara_test")
def test_hexbin_label_frontend_python_tooltip_accepts_dict_get(
    page_session: Page, globe_earth_texture_url
) -> None:
    widget = GlobeWidget(
        config=_hexbin_config(
            globe_earth_texture_url,
            hex_label=_hex_label_fn_using_get,
            points_data=[HexBinPointDatum(lat=0, lng=0, weight=9.0)],
        )
    )
    display(widget)

    _wait_for_canvas(page_session)
    _wait_for_tooltip_text(page_session, "HEX GET")
