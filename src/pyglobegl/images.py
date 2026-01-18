from __future__ import annotations

import base64
import io

from PIL import Image


def image_to_data_url(image: Image.Image) -> str:
    """Convert a PIL image to a PNG data URL.

    Args:
        image: PIL image to encode as PNG.

    Returns:
        PNG data URL string suitable for globe.gl image inputs.

    Raises:
        TypeError: If image is not a PIL.Image.Image instance.
    """
    if not isinstance(image, Image.Image):
        raise TypeError("image must be a PIL.Image.Image instance.")
    rgba_image = image.convert("RGBA") if image.mode != "RGBA" else image
    buffer = io.BytesIO()
    rgba_image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
