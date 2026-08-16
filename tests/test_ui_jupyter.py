from collections.abc import Iterator
from contextlib import contextmanager
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess  # ruff: ignore[suspicious-subprocess-import]
import time
from typing import Any, TYPE_CHECKING
import urllib.error
import urllib.request

from playwright.sync_api import Error as PlaywrightError
import pytest
import stamina


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


def _write_debug_artifacts(page, prefix: str, ui_artifacts_writer) -> None:
    ui_artifacts_writer(page, prefix)
    artifacts_dir = Path("ui-artifacts")
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


def _cell_error_text(cell) -> str:
    """Return the cell's stderr/traceback output text, if any."""
    stderr = cell.locator(
        ".jp-OutputArea-output[data-mime-type='application/vnd.jupyter.stderr']"
    )
    if stderr.count() > 0:
        return "\n".join(stderr.all_inner_texts()).strip()
    return ""


def _wait_for_canvas(
    page, cell, output_timeout_ms: int = 15000, canvas_timeout_ms: int = 30000
) -> None:
    """Wait for a sized canvas in the cell output.

    The output area attaches quickly once the cell executes, so a short
    ``output_timeout_ms`` surfaces a missed render promptly — the caller then
    reloads and retries rather than waiting longer, since a stretched timeout
    does not fix a render that wedged or never started.

    Raises:
        RuntimeError: The cell produced a traceback (a deterministic failure
            that should not be retried).
        TimeoutError: The canvas never attached or never gained a size (the
            retryable, browser-timing failure).
    """
    output = cell.locator(".jp-OutputArea")
    output.wait_for(state="attached", timeout=output_timeout_ms)
    error = _cell_error_text(cell)
    if error:
        raise RuntimeError(f"Cell output error:\n{error}")
    canvas = output.locator("canvas").first
    canvas.wait_for(state="attached", timeout=canvas_timeout_ms)
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        box = canvas.bounding_box()
        if box and box["width"] > 0 and box["height"] > 0:
            return
        page.wait_for_timeout(250)
    raise TimeoutError("Canvas attached but never became visible.")


def _open_notebook(page, url: str, cell_text: str):
    """Open (or, on a retry, reload) the demo notebook and select its kernel.

    Returns:
        The notebook-panel locator, with the widget cell present.
    """
    _goto_with_retry(page, url)
    page.wait_for_selector(".jp-NotebookPanel", timeout=60000)
    _dismiss_notifications(page)
    _ensure_webgl_available(page)
    _select_kernel_if_prompted(page)
    _wait_for_kernel_idle(page)
    notebook = page.locator(".jp-NotebookPanel").first
    notebook.get_by_text(cell_text, exact=True).wait_for(timeout=60000)
    return notebook


def _render_widget(page, url: str, cell_text: str) -> None:
    """Open the notebook, render the widget, and wait for its canvas.

    The page is reloaded between attempts. The browser flakes here are wedged or
    missed renders, not merely slow ones, so a fresh page load — which
    re-bootstraps JupyterLab and reconnects the kernel session — clears them
    where a longer wait or an in-place cell re-run would not (the marimo UI test
    hardens the same way, reloading on a canvas miss). On retry ``_open_notebook``
    re-navigates to the notebook URL, which reloads the page. A cell traceback
    raises ``RuntimeError``, not retried.
    """
    for attempt in stamina.retry_context(
        on=(PlaywrightError, TimeoutError), attempts=3, timeout=None
    ):
        with attempt:
            notebook = _open_notebook(page, url, cell_text)
            cell = _execute_cell(page, notebook, cell_text)
            if _select_kernel_from_dialog(page):
                _wait_for_kernel_idle(page)
            _wait_for_canvas(page, cell)


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


def _goto_with_retry(page, url: str, timeout_s: float = 30) -> None:
    deadline = time.monotonic() + timeout_s
    last_exc: Exception | None = None
    while time.monotonic() < deadline:
        try:
            page.goto(url, wait_until="load")
            return
        except PlaywrightError as exc:
            last_exc = exc
            if "ERR_CONNECTION_FAILED" not in str(exc):
                raise
        page.wait_for_timeout(200)
    if last_exc is not None:
        raise last_exc
    raise TimeoutError(f"Timed out waiting to load {url}.")


def _tail_log(log_path: Path, max_chars: int = 4000) -> str:
    if not log_path.exists():
        return ""
    return log_path.read_text(encoding="utf-8")[-max_chars:]


def _open_jupyter_log(port: int) -> tuple[Path, Any]:
    artifacts_dir = Path("ui-artifacts")
    artifacts_dir.mkdir(exist_ok=True)
    log_path = artifacts_dir / f"jupyterlab-{port}.log"
    return log_path, log_path.open("w", encoding="utf-8", buffering=1)


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
    env = dict(os.environ)
    env.setdefault("PYTHONUNBUFFERED", "1")
    return subprocess.Popen(  # ruff: ignore[subprocess-without-shell-equals-true]
        args, stdout=log_file, stderr=subprocess.STDOUT, env=env
    )


def _jupyter_http_ready(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as response:  # ruff: ignore[suspicious-url-open-usage]
            return response.status < 500
    except urllib.error.HTTPError as exc:
        status_ok = exc.code < 500
        exc.close()
        return status_ok
    except (urllib.error.URLError, TimeoutError):
        return False


def _wait_for_jupyter(
    port: int, token: str, proc: subprocess.Popen, log_path: Path
) -> str:
    ready_url = f"http://127.0.0.1:{port}/lab?token={token}"
    url = f"http://127.0.0.1:{port}/lab/tree/examples/jupyter_demo.ipynb?token={token}"
    start = time.monotonic()
    while time.monotonic() - start < 180:
        if proc.poll() is not None:
            tail = _tail_log(log_path)
            raise RuntimeError(
                "JupyterLab exited early with code "
                f"{proc.returncode}. Log tail:\n{tail}"
            )
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(("127.0.0.1", port)) == 0 and _jupyter_http_ready(
                ready_url
            ):
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
        yield _wait_for_jupyter(port, token, proc, log_path)
    finally:
        _shutdown_process(proc, log_file)


@pytest.mark.timeout(360)
def test_jupyter_widget_renders(page: "Page", ui_artifacts_writer) -> None:
    cell_text = "from pyglobegl import GlobeWidget"
    with _jupyterlab_server() as url:
        try:
            _render_widget(page, url, cell_text)
            _assert_no_root_overflow(page)
        except Exception:
            try:
                _write_debug_artifacts(page, "jupyter", ui_artifacts_writer)
            finally:
                raise
