# Frontend Python Callbacks

Most layers in pyglobegl are driven entirely by typed data models. A few
globe.gl accessors, though, are computed per-datum in the browser &mdash; the
[hex bin layer](../layers/hex-bin.md) is the main example. Rather than make you
write JavaScript, pyglobegl lets you decorate a Python function with
`@frontend_python` and run it on the frontend.

```python
from pyglobegl import frontend_python


@frontend_python
def hex_altitude(hexbin):
    return hexbin["sumWeight"] * 0.01
```

Pass the decorated function wherever an accessor callback is accepted (for
example `hex_altitude=`, `hex_top_color=`, `hex_label=`).

## How it works

- `@frontend_python` returns a `FrontendPythonFunction`. The function's source is
  shipped to the widget and executed in the browser via MicroPython, so it runs
  client-side without a Python round-trip per datum.
- Callback arguments are **normalised to plain Python values** (dict / list /
  str / float / bool / None) when they are JSON-serializable, so dict methods
  like `.get(...)` work inside the callback.

!!! warning "Keep callbacks self-contained"

    Because the body runs in the browser's MicroPython runtime, it should rely
    only on its arguments and the Python builtins available there &mdash; not on
    closures over your notebook's variables or third-party imports.

!!! tip "Read inputs defensively"

    Upstream globe.gl shapes (such as the hex-bin aggregate) can change between
    versions. Prefer `arg.get("key", default)` over direct indexing so a missing
    key degrades gracefully. See the
    [hex bin callback I/O table](../layers/hex-bin.md#callback-io) for the exact
    argument shapes.
