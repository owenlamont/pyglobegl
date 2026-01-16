from collections.abc import Iterator
from contextlib import contextmanager, suppress
import shutil
import socket
import subprocess  # noqa: S404
import time
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from playwright.sync_api import Page


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@contextmanager
def _marimo_server() -> Iterator[str]:
    port = _free_port()
    uv_path = shutil.which("uv")
    if uv_path is None:
        raise RuntimeError("uv not found on PATH.")
    proc = subprocess.Popen(  # noqa: S603
        [
            uv_path,
            "run",
            "marimo",
            "run",
            "examples/marimo_demo.py",
            "--headless",
            "--port",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )

    try:
        url = f"http://127.0.0.1:{port}"
        start = time.monotonic()
        while time.monotonic() - start < 60:
            if proc.poll() is not None:
                raise RuntimeError(
                    f"Marimo server exited early with code {proc.returncode}."
                )
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                if sock.connect_ex(("127.0.0.1", port)) == 0:
                    break
            time.sleep(0.1)
        else:
            raise RuntimeError("Timed out waiting for marimo server.")
        yield url
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                with suppress(subprocess.TimeoutExpired):
                    proc.wait(timeout=5)


def _wait_for_canvas(page: "Page", timeout_ms: int = 20000) -> None:
    page.wait_for_function(
        "document.getElementById('root')?.children.length > 0", timeout=timeout_ms
    )
    page.wait_for_selector("canvas", timeout=timeout_ms)


def test_marimo_widget_renders(page: "Page", ui_artifacts_writer) -> None:
    with _marimo_server() as url:
        page.goto(url)
        try:
            _wait_for_canvas(page, timeout_ms=20000)
        except Exception:
            try:
                page.reload(wait_until="domcontentloaded")
                page.wait_for_timeout(500)
                _wait_for_canvas(page, timeout_ms=20000)
            except Exception:
                ui_artifacts_writer(page, "marimo-canvas-timeout")
                raise

        root_overflow = page.evaluate(
            """
            () => {
              const doc = document.documentElement;
              const body = document.body;
              return (
                doc.scrollHeight > doc.clientHeight + 1 ||
                body.scrollHeight > body.clientHeight + 1
              );
            }
            """
        )
        assert not root_overflow
