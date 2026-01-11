from collections.abc import Callable
import pathlib
from typing import Any

import pytest


def _is_wsl() -> bool:
    version = pathlib.Path("/proc/version")
    if not version.exists():
        return False
    return "microsoft" in version.read_text().lower()


@pytest.fixture(scope="session")
def browser_type_launch_args(pytestconfig: pytest.Config) -> dict:
    launch_options: dict = {}
    headed_option = pytestconfig.getoption("--headed")
    if headed_option:
        launch_options["headless"] = False
    browser_channel_option = pytestconfig.getoption("--browser-channel")
    if browser_channel_option:
        launch_options["channel"] = browser_channel_option
    elif _is_wsl():
        launch_options["channel"] = "chromium"
    slowmo_option = pytestconfig.getoption("--slowmo")
    if slowmo_option:
        launch_options["slow_mo"] = slowmo_option

    launch_options["chromium_sandbox"] = False
    launch_options["args"] = [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-crashpad",
        "--disable-crash-reporter",
    ]
    return launch_options


@pytest.fixture(scope="session")
def browser(launch_browser: Callable[..., Any]):
    if _is_wsl():
        pytest.skip(
            "Playwright Chromium fails on WSL; run UI tests in Windows "
            "or a Linux environment that supports Chromium."
        )
    return launch_browser()
