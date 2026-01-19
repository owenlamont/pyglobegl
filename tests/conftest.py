from __future__ import annotations

import base64
from collections.abc import Callable, Generator
import contextlib
from datetime import datetime, timezone
import io
import os
import pathlib
import shutil
import socketserver
import threading
from typing import Any, Literal, TYPE_CHECKING

from PIL import Image, ImageChops
from pydantic import AnyUrl, TypeAdapter
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
def _clear_ui_artifacts_dir(request: pytest.FixtureRequest) -> None:
    from xdist import get_xdist_worker_id

    worker_id = get_xdist_worker_id(request)
    if worker_id not in {"master", "gw0"}:
        return
    artifacts_dir = pathlib.Path("ui-artifacts")
    artifacts_dir.mkdir(exist_ok=True)
    for entry in artifacts_dir.iterdir():
        if entry.is_dir():
            shutil.rmtree(entry, ignore_errors=True)
        else:
            with contextlib.suppress(OSError):
                entry.unlink()


def _capture_canvas_data_url(page: PlaywrightPage) -> bytes:
    page.wait_for_selector("canvas", timeout=20000)
    data_url = page.evaluate(
        """
        () => {
          const container = document.querySelector(".scene-container");
          const canvas = container ? container.querySelector("canvas") : null;
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
    return base64.b64decode(encoded)


@pytest.fixture(scope="session")
def globe_earth_texture_url() -> AnyUrl:
    return TypeAdapter(AnyUrl).validate_python(
        "https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-day.jpg"
    )


@pytest.fixture(scope="session")
def globe_background_night_sky_url() -> AnyUrl:
    return TypeAdapter(AnyUrl).validate_python(
        "https://cdn.jsdelivr.net/npm/three-globe/example/img/night-sky.png"
    )


@pytest.fixture
def globe_clicker() -> Callable[[PlaywrightPage, Literal["left", "right"]], None]:
    def _click(page: PlaywrightPage, button: Literal["left", "right"] = "left") -> None:
        success = page.evaluate(
            """
            async ({ button }) => {
              const target = document.querySelector(".scene-container");
              if (!target) {
                return false;
              }
              const rect = target.getBoundingClientRect();
              const x = rect.left + rect.width / 2;
              const y = rect.top + rect.height / 2;
              const buttonMap = { left: 0, right: 2 };
              const buttonCode = buttonMap[button] ?? 0;
              const buttons = buttonCode === 2 ? 2 : 1;
              const opts = {
                clientX: x,
                clientY: y,
                pageX: x + window.scrollX,
                pageY: y + window.scrollY,
                button: buttonCode,
                buttons,
                bubbles: true,
                cancelable: true,
                view: window,
                pointerType: "mouse",
                pointerId: 1,
                isPrimary: true,
              };
              const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
              target.dispatchEvent(new PointerEvent("pointermove", opts));
              await wait(50);
              target.dispatchEvent(new PointerEvent("pointerdown", opts));
              await wait(50);
              target.dispatchEvent(new PointerEvent("pointerup", opts));
              if (buttonCode === 2) {
                target.dispatchEvent(new MouseEvent("contextmenu", opts));
              } else {
                target.dispatchEvent(new MouseEvent("click", opts));
              }
              return true;
            }
            """,
            {"button": button},
        )
        if not success:
            raise AssertionError("Failed to dispatch globe click event.")

    return _click


def _make_bump_test_map(width: int = 360, height: int = 180) -> Image.Image:
    image = Image.new("L", (width, height))
    stripe_width = max(1, width // 12)
    for x in range(width):
        shade = 255 if (x // stripe_width) % 2 == 0 else 0
        image.paste(shade, (x, 0, x + 1, height))
    return image


@pytest.fixture(scope="session")
def globe_bump_test_data_url() -> str:
    from pyglobegl.images import image_to_data_url

    image = _make_bump_test_map()
    return image_to_data_url(image)


def _make_flat_globe_texture(width: int = 360, height: int = 180) -> Image.Image:
    return Image.new("RGB", (width, height), (140, 140, 140))


@pytest.fixture(scope="session")
def globe_flat_texture_data_url() -> str:
    from pyglobegl.images import image_to_data_url

    image = _make_flat_globe_texture()
    return image_to_data_url(image)


def _make_solid_tile(color: tuple[int, int, int]) -> Image.Image:
    return Image.new("RGB", (64, 64), color)


@pytest.fixture(scope="session")
def globe_tile_red_data_url() -> str:
    from pyglobegl.images import image_to_data_url

    image = _make_solid_tile((255, 0, 0))
    return image_to_data_url(image)


@pytest.fixture(scope="session")
def globe_tile_green_data_url() -> str:
    from pyglobegl.images import image_to_data_url

    image = _make_solid_tile((0, 255, 0))
    return image_to_data_url(image)


def _png_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def globe_tile_server() -> Generator[tuple[str, Callable[[bytes], None]], None, None]:
    class TileData:
        def __init__(self) -> None:
            self._lock = threading.Lock()
            self._data: bytes = b""

        def set(self, data: bytes) -> None:
            with self._lock:
                self._data = data

        def get(self) -> bytes:
            with self._lock:
                return self._data

    tile_data = TileData()

    class TileHandler(socketserver.BaseRequestHandler):
        def handle(self) -> None:
            data = self.request.recv(1024)
            if not data:
                return
            request_line = data.split(b"\r\n", 1)[0]
            if not request_line.startswith(b"GET"):
                return
            body = tile_data.get()
            if not body:
                response = (
                    b"HTTP/1.1 404 Not Found\r\n"
                    b"Access-Control-Allow-Origin: *\r\n"
                    b"Cache-Control: no-store, no-cache, must-revalidate, max-age=0\r\n"
                    b"Pragma: no-cache\r\n"
                    b"Expires: 0\r\n"
                    b"Content-Length: 0\r\n\r\n"
                )
                self.request.sendall(response)
                return
            headers = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: image/png\r\n"
                b"Access-Control-Allow-Origin: *\r\n"
                b"Cache-Control: no-store, no-cache, must-revalidate, max-age=0\r\n"
                b"Pragma: no-cache\r\n"
                b"Expires: 0\r\n"
                + f"Content-Length: {len(body)}\r\n".encode("ascii")
                + b"\r\n"
            )
            self.request.sendall(headers + body)

    server = socketserver.TCPServer(("127.0.0.1", 0), TileHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host = server.server_address[0]
    port = server.server_address[1]

    def _set_bytes(data: bytes) -> None:
        tile_data.set(data)

    try:
        yield f"http://{host}:{port}", _set_bytes
    finally:
        server.shutdown()
        server.server_close()


def _safe_name(value: str) -> str:
    return (
        value.replace("/", "_")
        .replace("\\", "_")
        .replace(":", "-")
        .replace("[", "_")
        .replace("]", "_")
        .replace(" ", "_")
    )


def _timestamp_local() -> str:
    return _safe_name(datetime.now().astimezone().isoformat(timespec="seconds"))


def _images_identical(first: Image.Image, second: Image.Image) -> bool:
    if first.size != second.size:
        return False
    diff = ImageChops.difference(first, second)
    return diff.getbbox() is None


@pytest.fixture
def canvas_capture() -> Callable[[PlaywrightPage, int], Image.Image]:
    def _capture(page: PlaywrightPage, max_attempts: int = 3) -> Image.Image:
        png_bytes = _capture_canvas_data_url(page)
        current = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        for _ in range(max_attempts - 1):
            page.wait_for_timeout(100)
            next_bytes = _capture_canvas_data_url(page)
            next_image = Image.open(io.BytesIO(next_bytes)).convert("RGBA")
            if _images_identical(current, next_image):
                return current
            current = next_image
        return current

    return _capture


@pytest.fixture
def canvas_label(request: pytest.FixtureRequest) -> str:
    base = getattr(request.node, "originalname", request.node.name)
    if hasattr(request.node, "callspec"):
        ids = request.node.callspec.id.split("-")
        browser = request.node.callspec.params.get("browser_name")
        if browser:
            ids = [item for item in ids if item != browser]
        if ids:
            base = f"{base}-{'-'.join(ids)}"
    return _safe_name(base)


@pytest.fixture
def canvas_reference_path() -> Callable[[str], pathlib.Path]:
    def _resolve(test_name: str) -> pathlib.Path:
        return pathlib.Path("tests/reference-images") / f"{test_name}.png"

    return _resolve


@pytest.fixture
def canvas_save_capture() -> Callable[[Image.Image, str], pathlib.Path]:
    def _save(image: Image.Image, label: str) -> pathlib.Path:
        filename = f"{_safe_name(label)}-{_timestamp_local()}.png"
        path = pathlib.Path("ui-artifacts") / filename
        image.save(path)
        return path

    return _save


@pytest.fixture
def canvas_compare_images() -> Callable[[Image.Image, pathlib.Path], None]:
    def _compare(captured: Image.Image, reference_path: pathlib.Path) -> None:
        reference = Image.open(reference_path).convert("RGBA")
        if captured.size != reference.size:
            raise AssertionError(
                f"Reference size {reference.size} does not match capture size "
                f"{captured.size}."
            )
        diff = ImageChops.difference(captured, reference)
        diff_pixels = sum(
            1 for pixel in diff.get_flattened_data() if pixel != (0, 0, 0, 0)
        )
        if diff_pixels == 0:
            return
        diff_path = (
            pathlib.Path("ui-artifacts")
            / f"canvas-capture-diff-{_timestamp_local()}.png"
        )
        diff.save(diff_path)
        raise AssertionError(
            "Captured image differs from reference. "
            f"Diff pixels: {diff_pixels}. Diff saved to {diff_path}."
        )

    return _compare


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
