from __future__ import annotations

from datetime import datetime, timezone
import pathlib
import struct
from typing import TYPE_CHECKING

from IPython.display import display
from PIL import Image, ImageChops

from pyglobegl import GlobeConfig, GlobeInitConfig, GlobeLayoutConfig, GlobeWidget


if TYPE_CHECKING:
    from playwright.sync_api import Page


def _read_png_dimensions(path: str) -> tuple[int, int]:
    with pathlib.Path(path).open("rb") as handle:
        signature = handle.read(8)
        if signature != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"{path} is not a PNG file.")
        length_bytes = handle.read(4)
        chunk_type = handle.read(4)
        if len(length_bytes) != 4 or chunk_type != b"IHDR":
            raise ValueError(f"{path} missing IHDR chunk.")
        length = struct.unpack(">I", length_bytes)[0]
        ihdr = handle.read(length)
        if len(ihdr) < 8:
            raise ValueError(f"{path} IHDR chunk too short.")
        width, height = struct.unpack(">II", ihdr[:8])
        return int(width), int(height)


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _reference_image_path(test_name: str) -> pathlib.Path:
    return pathlib.Path("tests/reference-images") / f"{test_name}.png"


def _compare_images(captured_path: pathlib.Path, reference_path: pathlib.Path) -> None:
    captured = Image.open(captured_path).convert("RGBA")
    reference = Image.open(reference_path).convert("RGBA")
    if captured.size != reference.size:
        raise AssertionError(
            f"Reference size {reference.size} does not match capture size "
            f"{captured.size}."
        )
    diff = ImageChops.difference(captured, reference)
    diff_bbox = diff.getbbox()
    if diff_bbox is None:
        return
    diff_pixels = sum(1 for pixel in diff.getdata() if pixel != (0, 0, 0, 0))
    diff_path = captured_path.with_name(captured_path.stem + "-diff.png")
    diff.save(diff_path)
    raise AssertionError(
        "Captured image differs from reference. "
        f"Diff pixels: {diff_pixels}. Diff saved to {diff_path}."
    )


def test_solara_canvas_capture_baseline(
    solara_test, page_session: Page, ui_artifacts_writer, canvas_capture
) -> None:
    config = GlobeConfig(
        init=GlobeInitConfig(renderer_config={"preserveDrawingBuffer": True}),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#00ff00"),
    )
    widget = GlobeWidget(config=config)
    display(widget)

    try:
        page_session.wait_for_function(
            "document.querySelector('canvas, .jupyter-widgets') !== null", timeout=20000
        )
    except Exception:
        ui_artifacts_writer(page_session, "canvas-capture-timeout")
        raise

    device_pixel_ratio = page_session.evaluate(
        """
        () => {
          const before = window.devicePixelRatio;
          try {
            Object.defineProperty(window, "devicePixelRatio", {
              get: () => 1,
              configurable: true
            });
          } catch (err) {
            // ignore if browser blocks override
          }
          return { before, after: window.devicePixelRatio };
        }
        """
    )

    page_session.evaluate(
        """
        () => {
          document.body.style.backgroundColor = "#111111";
          const canvas = document.querySelector("canvas");
          if (canvas) {
            canvas.style.border = "4px solid magenta";
          }
        }
        """
    )
    ui_artifacts_writer(page_session, "canvas-capture-baseline")
    start = page_session.evaluate("() => performance.now()")
    capture_path = canvas_capture(page_session, "canvas-capture")
    end = page_session.evaluate("() => performance.now()")

    metrics = page_session.evaluate(
        """
        () => {
          const canvas = document.querySelector("canvas");
          if (!canvas) {
            return null;
          }
          const rect = canvas.getBoundingClientRect();
          return {
            canvasWidth: canvas.width,
            canvasHeight: canvas.height,
            cssWidth: rect.width,
            cssHeight: rect.height,
            devicePixelRatio: window.devicePixelRatio
          };
        }
        """
    )

    report_lines = [
        "Canvas capture report",
        f"Timestamp: {_timestamp()}",
        f"devicePixelRatio before/after: {device_pixel_ratio}",
        f"canvas metrics: {metrics}",
        "",
        "method\tpng_width\tpng_height\tfile_bytes\tcapture_ms\tpath",
    ]
    png_width, png_height = _read_png_dimensions(str(capture_path))
    file_bytes = capture_path.stat().st_size
    capture_ms = float(end) - float(start)
    report_lines.append(
        f"data-url\t{png_width}\t{png_height}\t{file_bytes}\t{capture_ms:.2f}\t{capture_path}"
    )

    report_path = f"ui-artifacts/canvas-capture-report-{_timestamp()}.txt"
    pathlib.Path(report_path).write_text("\n".join(report_lines), encoding="utf-8")

    reference_path = _reference_image_path("test_solara_canvas_capture_baseline")
    if not reference_path.exists():
        raise AssertionError(
            f"Reference image missing. Save the capture to {reference_path} and re-run."
        )
    _compare_images(capture_path, reference_path)
