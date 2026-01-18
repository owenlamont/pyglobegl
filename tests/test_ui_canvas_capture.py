from __future__ import annotations

from datetime import datetime
import pathlib
from typing import TYPE_CHECKING

from IPython.display import display
from PIL import Image, ImageChops

from pyglobegl import GlobeConfig, GlobeInitConfig, GlobeLayoutConfig, GlobeWidget


if TYPE_CHECKING:
    from playwright.sync_api import Page


def _timestamp() -> str:
    return _safe_name(datetime.now().astimezone().isoformat(timespec="seconds"))


def _safe_name(value: str) -> str:
    return (
        value.replace("/", "_")
        .replace("\\", "_")
        .replace(":", "-")
        .replace("[", "_")
        .replace("]", "_")
        .replace(" ", "_")
    )


def _reference_image_path(test_name: str) -> pathlib.Path:
    return pathlib.Path("tests/reference-images") / f"{test_name}.png"


def _compare_images(captured: Image.Image, reference_path: pathlib.Path) -> None:
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
    diff_path = pathlib.Path("ui-artifacts") / f"canvas-capture-diff-{_timestamp()}.png"
    diff.save(diff_path)
    raise AssertionError(
        "Captured image differs from reference. "
        f"Diff pixels: {diff_pixels}. Diff saved to {diff_path}."
    )


def test_solara_canvas_capture_baseline(
    solara_test, page_session: Page, canvas_capture, request
) -> None:
    config = GlobeConfig(
        init=GlobeInitConfig(renderer_config={"preserveDrawingBuffer": True}),
        layout=GlobeLayoutConfig(width=256, height=256, background_color="#00ff00"),
    )
    widget = GlobeWidget(config=config)
    display(widget)

    page_session.wait_for_function(
        "document.querySelector('canvas, .jupyter-widgets') !== null", timeout=20000
    )

    captured_image = canvas_capture(page_session)
    test_label = _safe_name(request.node.name)
    timestamp = _timestamp()
    latest_path = pathlib.Path("ui-artifacts") / f"{test_label}-{timestamp}.png"
    captured_image.save(latest_path)

    reference_path = _reference_image_path("test_solara_canvas_capture_baseline")
    if not reference_path.exists():
        raise AssertionError(
            f"Reference image missing. Save the capture to {reference_path} and re-run."
        )
    try:
        _compare_images(captured_image, reference_path)
    except AssertionError:
        mismatch_path = (
            pathlib.Path("ui-artifacts") / f"{test_label}-mismatch-{timestamp}.png"
        )
        captured_image.save(mismatch_path)
        raise
