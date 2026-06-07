"""Helpers for defining frontend-executed Python callbacks."""

from __future__ import annotations

from collections.abc import Callable
import inspect
import textwrap
from typing import Any, TypedDict, TypeVar

from pydantic import BaseModel


_FRONTEND_FUNCTION_ATTR = "__pyglobegl_frontend_python_function__"
_WIRE_TYPE = "frontend_python_function"

_DecoratedCallable = TypeVar("_DecoratedCallable", bound=Callable[..., Any])

ColorInterpolator = Callable[[float], str]
"""Signature of a gradient/colormap frontend callback.

Maps a normalised parameter ``t`` in ``[0, 1]`` to a CSS colour string. This is
the contract for the arc/path/ring ``*_color_fn`` gradient accessors and the
heatmaps ``heatmap_color_fn``. Annotate your ``@frontend_python`` callback against
it (``def fn(t: float) -> str: ...``) so your editor and type checker can verify
the signature where you pass it; pyglobegl runs the body in MicroPython, where
annotations are parsed and ignored. ``t`` may arrive as an ``int`` at the ``0``
and ``1`` endpoints, which is compatible with the ``float`` annotation.
"""


class HexBin(TypedDict):
    """Shape of the aggregated bin passed to the hex-bin styling callbacks.

    globe.gl builds each bin in the browser by H3-aggregating
    ``hex_bin_points_data``, so there is no Python datum to attach styling to. The
    ``hex_top_color`` / ``hex_side_color`` / ``hex_altitude`` / ``hex_label``
    callbacks receive a bin with ``h3Idx`` (the H3 cell id), ``points`` (the
    original rows that fell in the bin), and ``sumWeight`` (their aggregated
    weight). Annotate your callback against it (``def fn(b: HexBin) -> str: ...``)
    for editor autocomplete on these keys.

    This is an opt-in annotation aid, not an enforced field type: the hex-bin
    config fields keep accepting any callable so that a plain ``def fn(b: dict)``
    still type checks (a stricter parameter type would reject it by
    contravariance). globe.gl may add or rename keys across versions, so read
    anything beyond the three documented keys with ``b.get(...)``.
    """

    # Field names mirror globe.gl's bin keys (camelCase by necessity).
    h3Idx: str
    points: list[dict[str, Any]]
    sumWeight: float


class FrontendPythonFunction(BaseModel, extra="forbid", frozen=True):
    """Serialized frontend callback executed by the MicroPython runtime."""

    name: str
    source: str

    def to_wire(self) -> dict[str, str]:
        """Serialize this callback for transport to the frontend.

        Returns:
            A wire-safe payload describing the frontend callback.
        """
        return {
            "__pyglobegl_type": _WIRE_TYPE,
            "name": self.name,
            "source": self.source,
        }


def frontend_python(function: _DecoratedCallable) -> _DecoratedCallable:
    """Mark a Python function for frontend execution via MicroPython.

    The function remains callable in backend Python, but pyglobegl captures its
    source so it can be sent to the browser and bound to globe.gl accessors.
    Decorated callbacks should be pure, self-contained functions with no side
    effects, because they execute in the browser MicroPython runtime (not the
    backend Python process) and may run many times per frame/render cycle.

    The decorator is signature-preserving: the returned callable keeps the
    annotated type of the function you pass in, so annotating your callback (for
    example ``def fn(t: float) -> str: ...``, see ``ColorInterpolator``) gives
    your editor and type checker something to verify where you pass it.

    Returns:
        The original function with a serialized frontend callback spec attached.
    """
    function_name = getattr(function, "__name__", function.__class__.__name__)
    spec = FrontendPythonFunction(name=function_name, source=_extract_source(function))
    setattr(function, _FRONTEND_FUNCTION_ATTR, spec)
    return function


def resolve_frontend_python_function(value: Any) -> FrontendPythonFunction:
    """Resolve a decorator-marked callable or explicit model to a callback spec.

    Args:
        value: Callback-like value to resolve.

    Returns:
        The serialized callback specification.

    Raises:
        TypeError: If the value is not a valid frontend callback input.
    """
    if isinstance(value, FrontendPythonFunction):
        return value
    spec = getattr(value, _FRONTEND_FUNCTION_ATTR, None)
    if callable(value) and isinstance(spec, FrontendPythonFunction):
        return spec
    raise TypeError(
        "Expected FrontendPythonFunction or a callable decorated with @frontend_python."
    )


def is_frontend_python_wire_payload(value: Any) -> bool:
    """Return True when value is a frontend Python function payload."""
    if not isinstance(value, dict):
        return False
    return value.get("__pyglobegl_type") == _WIRE_TYPE


def parse_frontend_python_wire_payload(value: Any) -> FrontendPythonFunction | None:
    """Parse a frontend payload into FrontendPythonFunction when possible.

    Args:
        value: Arbitrary payload received from widget state.

    Returns:
        Parsed callback spec when payload matches the expected wire format.
    """
    if not is_frontend_python_wire_payload(value):
        return None
    if not isinstance(value, dict):
        return None
    return FrontendPythonFunction.model_validate(
        {"name": value.get("name"), "source": value.get("source")}
    )


def _extract_source(function: Callable[..., Any]) -> str:
    source = textwrap.dedent(inspect.getsource(function))
    lines = source.splitlines()
    while lines and lines[0].lstrip().startswith("@"):
        lines.pop(0)
    extracted = "\n".join(lines).strip()
    if not extracted:
        raise ValueError("Unable to extract function source for frontend callback.")
    return extracted
