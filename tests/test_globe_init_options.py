from __future__ import annotations

from typing import TYPE_CHECKING

from IPython.display import display
import pytest

from pyglobegl import GlobeConfig, GlobeInitConfig, GlobeLayoutConfig, GlobeWidget


if TYPE_CHECKING:
    from playwright.sync_api import Page


def _wait_for_init_config(page_session: Page) -> None:
    page_session.wait_for_function(
        "window.__pyglobegl_init_config !== undefined", timeout=20000
    )


@pytest.mark.usefixtures("solara_test")
def test_renderer_config_applied(page_session: Page) -> None:
    config = GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True, "antialias": False},
            animate_in=False,
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#000000"),
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _wait_for_init_config(page_session)
    page_session.wait_for_function(
        "window.__pyglobegl_globe_ready === true", timeout=20000
    )
    attrs = page_session.evaluate("() => window.__pyglobegl_renderer_attributes")
    assert attrs is not None
    assert attrs.get("preserveDrawingBuffer") is True
    assert attrs.get("antialias") is False


@pytest.mark.usefixtures("solara_test")
def test_wait_for_globe_ready_passed(page_session: Page) -> None:
    config = GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True},
            wait_for_globe_ready=False,
            animate_in=False,
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#000000"),
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _wait_for_init_config(page_session)
    init_config = page_session.evaluate("() => window.__pyglobegl_init_config")
    assert init_config is not None
    assert init_config.get("waitForGlobeReady") is False


@pytest.mark.usefixtures("solara_test")
def test_animate_in_disabled_passed(page_session: Page) -> None:
    config = GlobeConfig(
        init=GlobeInitConfig(
            renderer_config={"preserveDrawingBuffer": True}, animate_in=False
        ),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#000000"),
    )
    widget = GlobeWidget(config=config)
    display(widget)

    _wait_for_init_config(page_session)
    init_config = page_session.evaluate("() => window.__pyglobegl_init_config")
    assert init_config is not None
    assert init_config.get("animateIn") is False
