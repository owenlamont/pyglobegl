from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import re
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


def _try_select_python_kernel(dialog, timeout_ms: int = 20000) -> bool:
    buttons = dialog.get_by_role("button", name=re.compile(r"Python", re.IGNORECASE))
    if buttons.count() == 0:
        return False
    buttons.first.wait_for(state="visible", timeout=timeout_ms)
    buttons.first.click(timeout=timeout_ms)
    return True


def _write_debug_artifacts(page, prefix: str) -> None:
    artifacts_dir = Path("ui-artifacts")
    artifacts_dir.mkdir(exist_ok=True)
    page.screenshot(
        path=str(artifacts_dir / f"{prefix}-screenshot.png"), full_page=True
    )
    (artifacts_dir / f"{prefix}-page.html").write_text(page.content(), encoding="utf-8")
    kernel_status = page.locator(".jp-KernelStatus")
    if kernel_status.count() > 0:
        (artifacts_dir / f"{prefix}-kernel-status.txt").write_text(
            kernel_status.inner_text(), encoding="utf-8"
        )


def _select_kernel_if_prompted(page) -> None:
    select_kernel = page.get_by_role("button", name="Select Kernel")
    if not select_kernel.is_visible():
        return
    select_kernel.click(timeout=2000)
    _select_kernel_from_dialog(page)


def _select_kernel_from_dialog(page) -> None:
    dialog = page.get_by_role("dialog")
    if not dialog.is_visible():
        return
    if _try_select_python_kernel(dialog):
        page.wait_for_timeout(500)
        return
    pytest.skip("Jupyter kernel picker did not expose a Python kernel.")


def _run_cell(page, cell_text: str) -> None:
    cell = page.get_by_text(cell_text).locator(
        "xpath=ancestor::div[contains(@class,'jp-Cell')]"
    )
    cell.locator(".jp-InputArea").click()
    page.keyboard.press("Shift+Enter")


def _wait_for_canvas(page) -> None:
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


def _assert_no_root_overflow(page) -> None:
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
                proc.wait(timeout=10)


@pytest.mark.ui
def test_jupyter_widget_renders(page: "Page") -> None:
    with _jupyterlab_server() as url:
        try:
            page.goto(url)
            page.wait_for_selector(".jp-NotebookPanel", timeout=60000)
            _select_kernel_if_prompted(page)
            page.get_by_text("from pyglobegl import GlobeWidget").wait_for(
                timeout=60000
            )
            _run_cell(page, "from pyglobegl import GlobeWidget")
            _select_kernel_from_dialog(page)
            _wait_for_canvas(page)
            _assert_no_root_overflow(page)
        except Exception:
            try:
                _write_debug_artifacts(page, "jupyter")
            finally:
                raise
