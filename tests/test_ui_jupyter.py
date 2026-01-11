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
    output_text = page.locator(".jp-OutputArea-output")
    if output_text.count() > 0:
        (artifacts_dir / f"{prefix}-output.txt").write_text(
            "\n".join(output_text.all_inner_texts()), encoding="utf-8"
        )
    status_text = page.locator(".jp-StatusBar-TextItem")
    if status_text.count() > 0:
        (artifacts_dir / f"{prefix}-statusbar.txt").write_text(
            "\n".join(status_text.all_inner_texts()), encoding="utf-8"
        )


def _select_kernel_if_prompted(page) -> None:
    select_kernel = page.get_by_role("button", name="Select Kernel")
    if not select_kernel.is_visible():
        return
    select_kernel.click(timeout=2000)
    _select_kernel_from_dialog(page)


def _wait_for_kernel_idle(page, timeout_ms: int = 60000) -> bool:
    kernel_status = page.locator(".jp-StatusBar-TextItem", has_text="Idle")
    start = time.monotonic()
    while time.monotonic() - start < timeout_ms / 1000:
        if kernel_status.count() > 0:
            return True
        page.wait_for_timeout(250)
    return False


def _select_kernel_from_dialog(page) -> bool:
    dialog = page.get_by_role("dialog")
    if not dialog.is_visible():
        return False
    if _try_select_python_kernel(dialog):
        page.wait_for_timeout(500)
        return True
    pytest.skip("Jupyter kernel picker did not expose a Python kernel.")
    return False


def _execute_cell(page, notebook, cell_text: str):
    cell = notebook.get_by_text(cell_text, exact=True).locator(
        "xpath=ancestor::div[contains(@class,'jp-Cell')]"
    )
    editor = cell.locator(".jp-InputArea-editor").first
    if editor.count() > 0:
        editor.click(timeout=2000)
    else:
        cell.click(timeout=2000)
    page.keyboard.press("Shift+Enter")
    run_button = page.get_by_role(
        "button", name=re.compile(r"Run this cell", re.IGNORECASE)
    )
    if run_button.count() > 0:
        run_button.first.click(timeout=2000)
    return cell


def _wait_for_canvas(page, cell, timeout_ms: int = 60000) -> None:
    output = cell.locator(".jp-OutputArea")
    output.wait_for(state="attached", timeout=timeout_ms)
    output_text = output.locator(".jp-OutputArea-output")
    if output_text.count() > 0:
        text = "\n".join(output_text.all_inner_texts()).strip()
        if text:
            raise RuntimeError(f"Cell output error:\n{text}")
    canvas = output.locator("canvas").first
    canvas.wait_for(state="attached", timeout=timeout_ms)
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        box = canvas.bounding_box()
        if box and box["width"] > 0 and box["height"] > 0:
            return
        page.wait_for_timeout(250)
    raise TimeoutError("Canvas never became visible.")


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


def _ensure_webgl_available(page) -> None:
    has_webgl = page.evaluate(
        """
        () => {
          const canvas = document.createElement("canvas");
          return !!(
            canvas.getContext("webgl") ||
            canvas.getContext("experimental-webgl")
          );
        }
        """
    )
    if not has_webgl:
        pytest.skip("WebGL is not available in this browser environment.")


def _dismiss_notifications(page) -> None:
    toast_container = page.locator(".Toastify__toast-container")
    if toast_container.count() == 0:
        return
    toast_no = toast_container.get_by_role("button", name="No").first
    if toast_no.count() > 0 and toast_no.is_visible():
        toast_no.click(timeout=2000)
        page.wait_for_timeout(200)
        return
    toast_close = toast_container.get_by_role("button", name="Hide notification").first
    if toast_close.count() > 0 and toast_close.is_visible():
        toast_close.click(timeout=2000)
        page.wait_for_timeout(200)


def _tail_log(log_path: Path, max_chars: int = 4000) -> str:
    if not log_path.exists():
        return ""
    return log_path.read_text(encoding="utf-8")[-max_chars:]


def _open_jupyter_log(port: int) -> tuple[Path, object]:
    artifacts_dir = Path("ui-artifacts")
    artifacts_dir.mkdir(exist_ok=True)
    log_path = artifacts_dir / f"jupyterlab-{port}.log"
    return log_path, log_path.open("w", encoding="utf-8")


def _start_jupyter(uv_path: str, token: str, port: int, log_file) -> subprocess.Popen:
    args = [
        uv_path,
        "run",
        "jupyter",
        "lab",
        "--no-browser",
        "--ip",
        "127.0.0.1",
        "--ServerApp.port",
        str(port),
    ]
    if token:
        args.append(f"--ServerApp.token={token}")
    args.append("--ServerApp.password=")
    return subprocess.Popen(  # noqa: S603
        args, stdout=log_file, stderr=subprocess.STDOUT
    )


def _wait_for_jupyter(
    port: int, token: str, proc: subprocess.Popen, log_path: Path
) -> str:
    url = f"http://127.0.0.1:{port}/lab/tree/examples/jupyter_demo.ipynb?token={token}"
    start = time.monotonic()
    while time.monotonic() - start < 90:
        if proc.poll() is not None:
            tail = _tail_log(log_path)
            raise RuntimeError(
                "JupyterLab exited early with code "
                f"{proc.returncode}. Log tail:\n{tail}"
            )
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return url
        time.sleep(0.1)
    tail = _tail_log(log_path)
    raise RuntimeError(f"Timed out waiting for JupyterLab. Log tail:\n{tail}")


def _shutdown_process(proc: subprocess.Popen, log_file) -> None:
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)
    if not log_file.closed:
        log_file.close()


@contextmanager
def _jupyterlab_server() -> Iterator[str]:
    port = _free_port()
    uv_path = shutil.which("uv")
    if uv_path is None:
        raise RuntimeError("uv not found on PATH.")
    token = secrets.token_urlsafe(16)
    log_path, log_file = _open_jupyter_log(port)
    proc = _start_jupyter(uv_path, token, port, log_file)

    try:
        url = _wait_for_jupyter(port, token, proc, log_path)
        yield url
    finally:
        _shutdown_process(proc, log_file)


@pytest.mark.ui
def test_jupyter_widget_renders(page: "Page") -> None:
    with _jupyterlab_server() as url:
        try:
            page.goto(url)
            page.wait_for_selector(".jp-NotebookPanel", timeout=60000)
            _dismiss_notifications(page)
            _ensure_webgl_available(page)
            _select_kernel_if_prompted(page)
            _wait_for_kernel_idle(page)
            notebook = page.locator(".jp-NotebookPanel").first
            notebook.get_by_text(
                "from pyglobegl import GlobeWidget", exact=True
            ).wait_for(timeout=60000)
            cell = _execute_cell(page, notebook, "from pyglobegl import GlobeWidget")
            if _select_kernel_from_dialog(page):
                _wait_for_kernel_idle(page)
                cell = _execute_cell(
                    page, notebook, "from pyglobegl import GlobeWidget"
                )
            _wait_for_canvas(page, cell)
            _assert_no_root_overflow(page)
        except Exception:
            try:
                _write_debug_artifacts(page, "jupyter")
            finally:
                raise
