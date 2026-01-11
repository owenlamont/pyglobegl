from collections.abc import Iterator
from contextlib import contextmanager, suppress
import re
import secrets
import shutil
import socket
import subprocess  # noqa: S404
import time
from typing import TYPE_CHECKING

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
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
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                with suppress(subprocess.TimeoutExpired):
                    proc.wait(timeout=10)


@pytest.mark.ui
def test_jupyter_widget_renders(page: "Page") -> None:
    with _jupyterlab_server() as url:
        page.goto(url)
        page.wait_for_selector(".jp-NotebookPanel", timeout=60000)
        select_kernel = page.get_by_role("button", name="Select Kernel")
        if select_kernel.is_visible():
            select_kernel.click()
            dialog = page.get_by_role("dialog")
            dialog.get_by_role(
                "button", name=re.compile(r"Python", re.IGNORECASE)
            ).first.click()
            page.wait_for_timeout(500)
        cell_text = page.get_by_text("from pyglobegl import GlobeWidget")
        cell_text.wait_for(timeout=60000)
        cell = cell_text.locator("xpath=ancestor::div[contains(@class,'jp-Cell')]")
        cell.locator(".jp-InputArea").click()
        page.keyboard.press("Shift+Enter")
        dialog = page.get_by_role("dialog")
        with suppress(PlaywrightTimeoutError):
            dialog.wait_for(timeout=2000)
        if dialog.is_visible():
            dialog.get_by_role(
                "button", name=re.compile(r"Python", re.IGNORECASE)
            ).first.click()
            page.wait_for_timeout(500)
            cell.locator(".jp-InputArea").click()
            page.keyboard.press("Shift+Enter")
        page.wait_for_selector("canvas", state="attached", timeout=60000)
        page.wait_for_function(
            """
            () => {
              const canvas = document.querySelector("canvas");
              if (!canvas) {
                return false;
              }
              const rect = canvas.getBoundingClientRect();
              return rect.width > 0 && rect.height > 0;
            }
            """,
            timeout=60000,
        )

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
