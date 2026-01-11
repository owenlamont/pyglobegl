from collections.abc import Iterator
from contextlib import contextmanager
import secrets
import shutil
import socket
import subprocess  # noqa: S404
import time
from typing import TYPE_CHECKING

import pytest


if TYPE_CHECKING:
    from playwright.sync_api import Page


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@contextmanager
def _jupyterlab_server() -> Iterator[str]:
    port = _free_port()
    uv_path = shutil.which("uv")
    if uv_path is None:
        raise RuntimeError("uv not found on PATH.")
    token = secrets.token_urlsafe(16)
    proc = subprocess.Popen(  # noqa: S603
        [
            uv_path,
            "run",
            "jupyter",
            "lab",
            "--no-browser",
            "--ip",
            "127.0.0.1",
            "--ServerApp.port",
            str(port),
            "--ServerApp.token",
            token,
            "--ServerApp.password",
            "",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )

    try:
        url = (
            f"http://127.0.0.1:{port}/lab/tree/examples/jupyter_demo.ipynb"
            f"?token={token}"
        )
        start = time.monotonic()
        while time.monotonic() - start < 90:
            if proc.poll() is not None:
                raise RuntimeError(
                    f"JupyterLab exited early with code {proc.returncode}."
                )
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                if sock.connect_ex(("127.0.0.1", port)) == 0:
                    break
            time.sleep(0.1)
        else:
            raise RuntimeError("Timed out waiting for JupyterLab.")
        yield url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.mark.ui
def test_jupyter_widget_renders(page: "Page") -> None:
    with _jupyterlab_server() as url:
        page.goto(url)
        page.get_by_text("from pyglobegl import GlobeWidget").click()
        page.keyboard.press("Shift+Enter")
        page.wait_for_selector("canvas", timeout=30000)

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
