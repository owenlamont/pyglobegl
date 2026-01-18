from __future__ import annotations

import base64
from collections.abc import Callable
import contextlib
from datetime import datetime, timezone
import os
import pathlib
import shutil
from typing import Any, TYPE_CHECKING

import pytest


def _is_wsl() -> bool:
    version = pathlib.Path("/proc/version")
    if not version.exists():
        return False
    return "microsoft" in version.read_text().lower()


def _is_truthy_env(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _wslg_available() -> bool:
    if not _is_wsl():
        return False
    return pathlib.Path("/mnt/wslg").exists() and bool(
        os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY")
    )


def _wsl_browser_args() -> list[str]:
    args = ["--enable-gpu", "--ignore-gpu-blocklist", "--use-gl=egl"]
    if os.environ.get("WAYLAND_DISPLAY"):
        args.extend(["--enable-features=UseOzonePlatform", "--ozone-platform=wayland"])
    return args


def _wsl_env_overrides() -> dict[str, str]:
    if not _is_wsl():
        return {}
    overrides: dict[str, str] = {}
    if "GALLIUM_DRIVER" not in os.environ:
        overrides["GALLIUM_DRIVER"] = "d3d12"
    if "MESA_LOADER_DRIVER_OVERRIDE" not in os.environ:
        overrides["MESA_LOADER_DRIVER_OVERRIDE"] = "d3d12"
    adapter = os.environ.get("PYGLOBEGL_WSL_GPU_ADAPTER")
    if adapter and "MESA_D3D12_DEFAULT_ADAPTER_NAME" not in os.environ:
        overrides["MESA_D3D12_DEFAULT_ADAPTER_NAME"] = adapter
    return overrides


def _should_require_hw_accel() -> bool:
    return _is_truthy_env(os.environ.get("PYGLOBEGL_REQUIRE_HW_ACCEL"))


def _is_software_renderer(renderer: str | None) -> bool:
    if renderer is None:
        return False
    renderer_lower = renderer.lower()
    return any(
        term in renderer_lower for term in ("llvmpipe", "swiftshader", "software")
    )


def _probe_webgl(browser: Any) -> tuple[bool, str | None, str | None]:
    context = browser.new_context()
    page = context.new_page()
    try:
        page.goto("about:blank")
        result = page.evaluate(
            """
            () => {
              const canvas = document.createElement("canvas");
              const gl =
                canvas.getContext("webgl") ||
                canvas.getContext("experimental-webgl");
              if (!gl) {
                return { ok: false, renderer: null, vendor: null };
              }
              const debug = gl.getExtension("WEBGL_debug_renderer_info");
              const renderer = debug
                ? gl.getParameter(debug.UNMASKED_RENDERER_WEBGL)
                : null;
              const vendor = debug
                ? gl.getParameter(debug.UNMASKED_VENDOR_WEBGL)
                : null;
              return { ok: true, renderer, vendor };
            }
            """
        )
    finally:
        context.close()
    return bool(result.get("ok")), result.get("renderer"), result.get("vendor")


if TYPE_CHECKING:
    from playwright.sync_api import Page as PlaywrightPage


def _ui_artifacts_dir() -> pathlib.Path:
    artifacts_dir = pathlib.Path("ui-artifacts")
    artifacts_dir.mkdir(exist_ok=True)
    return artifacts_dir


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _write_debug_artifacts(page: PlaywrightPage, prefix: str) -> None:
    artifacts_dir = _ui_artifacts_dir()
    page.screenshot(
        path=str(artifacts_dir / f"{prefix}-screenshot.png"), full_page=True
    )
    (artifacts_dir / f"{prefix}-page.html").write_text(page.content(), encoding="utf-8")


@pytest.fixture(scope="session")
def ui_artifacts_writer() -> Callable[[PlaywrightPage, str], None]:
    return _write_debug_artifacts


@pytest.fixture(scope="session", autouse=True)
def _clear_ui_artifacts_dir() -> None:
    artifacts_dir = pathlib.Path("ui-artifacts")
    artifacts_dir.mkdir(exist_ok=True)
    for entry in artifacts_dir.iterdir():
        if entry.is_dir():
            shutil.rmtree(entry, ignore_errors=True)
        else:
            with contextlib.suppress(OSError):
                entry.unlink()


def _capture_canvas_data_url(page: PlaywrightPage, path: pathlib.Path) -> None:
    page.wait_for_selector("canvas", timeout=20000)
    data_url = page.evaluate(
        """
        () => {
          const canvas = document.querySelector("canvas");
          if (!canvas) {
            return null;
          }
          return canvas.toDataURL("image/png");
        }
        """
    )
    if not data_url:
        raise RuntimeError("Canvas data URL not available.")
    header, encoded = data_url.split(",", 1)
    if not header.startswith("data:image/png"):
        raise RuntimeError(f"Unexpected data URL header: {header}")
    path.write_bytes(base64.b64decode(encoded))


@pytest.fixture
def canvas_capture() -> Callable[[PlaywrightPage, str], pathlib.Path]:
    def _capture(page: PlaywrightPage, prefix: str) -> pathlib.Path:
        artifacts_dir = _ui_artifacts_dir()
        path = artifacts_dir / f"{prefix}-{_timestamp()}.png"
        _capture_canvas_data_url(page, path)
        return path

    return _capture


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
    if _is_wsl():
        launch_options["args"].extend(_wsl_browser_args())
    return launch_options


@pytest.fixture(scope="session")
def browser(launch_browser: Callable[..., Any]):
    if _is_wsl() and not _wslg_available():
        pytest.skip(
            "WSLg display sockets not detected. Set DISPLAY/WAYLAND_DISPLAY or "
            "run WSL with GUI support enabled."
        )
    browser_instance = launch_browser()
    has_webgl, renderer, _vendor = _probe_webgl(browser_instance)
    if _is_wsl() and (not has_webgl or _is_software_renderer(renderer)):
        browser_instance.close()
        env_overrides = _wsl_env_overrides()
        if env_overrides:
            browser_instance = launch_browser(env={**os.environ, **env_overrides})
            has_webgl, renderer, _vendor = _probe_webgl(browser_instance)
    if not has_webgl:
        browser_instance.close()
        pytest.skip("WebGL is not available in this browser environment.")
    if _should_require_hw_accel() and _is_software_renderer(renderer):
        browser_instance.close()
        pytest.skip(
            "WebGL is using a software renderer; set up GPU acceleration or "
            "unset PYGLOBEGL_REQUIRE_HW_ACCEL."
        )
    return browser_instance
