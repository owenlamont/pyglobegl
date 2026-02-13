"""Helpers for defining frontend-executed Python callbacks."""

from __future__ import annotations

from collections.abc import Callable
import inspect
import textwrap
from typing import Any

from pydantic import BaseModel


_FRONTEND_FUNCTION_ATTR = "__pyglobegl_frontend_python_function__"
_WIRE_TYPE = "frontend_python_function"


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


def frontend_python(function: Callable[..., Any]) -> Callable[..., Any]:
    """Mark a Python function for frontend execution via MicroPython.

    The function remains callable in backend Python, but pyglobegl captures its
    source so it can be sent to the browser and bound to globe.gl accessors.
    Decorated callbacks should be pure, self-contained functions with no side
    effects, because they execute in the browser MicroPython runtime (not the
    backend Python process) and may run many times per frame/render cycle.

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
    return FrontendPythonFunction.model_validate(value)


def _extract_source(function: Callable[..., Any]) -> str:
    source = textwrap.dedent(inspect.getsource(function))
    lines = source.splitlines()
    while lines and lines[0].lstrip().startswith("@"):
        lines.pop(0)
    extracted = "\n".join(lines).strip()
    if not extracted:
        raise ValueError("Unable to extract function source for frontend callback.")
    return extracted
