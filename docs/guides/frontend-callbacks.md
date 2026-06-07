# Frontend Python Callbacks

Most layers in pyglobegl are driven entirely by typed data models. A few
globe.gl accessors, though, are computed in the browser rather than mapped from a
single Python datum &mdash; the [hex bin layer](../layers/hex-bin.md) (whose bins
are aggregated client-side) and the
[heatmaps layer](../layers/heatmaps.md#custom-colormap) (whose colormap is a
function of normalised density) are the main examples. Rather than make you write
JavaScript, pyglobegl lets you decorate a Python function with `@frontend_python`
and run it on the frontend.

```python
from pyglobegl import frontend_python


@frontend_python
def hex_altitude(hexbin):
    return hexbin["sumWeight"] * 0.01
```

Pass the decorated function wherever an accessor callback is accepted (for
example `hex_altitude=`, `hex_top_color=`, `hex_label=`, the heatmaps
`heatmap_color_fn=`, or the arc/path/ring gradient accessors `arc_color_fn=`,
`path_color_fn=`, `ring_color_fn=`).

Most of these callbacks run at data-change time to bake globe.gl's render buffers
(for example, the heatmap colormap is sampled to build a fixed colour lookup),
not on every animation frame. Label/tooltip callbacks such as `hex_label` are the
exception &mdash; they are evaluated lazily on hover to build the tooltip. Either
way, keep the body cheap: ordinary Python arithmetic or string formatting is fast
enough.

## What your callback receives, and what it can access

A frontend callback is a **pure function**:

- **It takes exactly one argument** &mdash; the value globe.gl passes for that
  accessor: a single number `t` in `[0, 1]` for the gradient/colormap callbacks,
  or a datum `dict` for the hex-bin accessors. Nothing else is in scope.
- **It returns one value** &mdash; a CSS colour string, a number, or tooltip
  text, depending on the accessor (see the [reference table](#callback-reference)).
- **It cannot read or change anything else.** There is no access to the widget,
  the globe, other layers, your notebook's variables, the network, or the
  backend Python process. The body runs in an isolated MicroPython sandbox with
  only its argument and MicroPython's builtins in scope, and its **return value
  is the only thing that flows back out** &mdash; a callback cannot mutate globe
  state as a side effect. To change the globe, call the widget's `set_*` /
  `update_*` methods from Python instead.

### Typing your callback

`@frontend_python` is **signature-preserving**, so the annotations you put on the
callback survive, and pyglobegl exports type aliases for the two callback shapes:

- `ColorInterpolator` &mdash; `(t: float) -> str`, for the gradient/colormap
  callbacks. The `arc_color_fn` / `path_color_fn` / `ring_color_fn` /
  `heatmap_color_fn` fields are typed to it, so an annotated callback is **checked
  at the call site** (a wrong signature is flagged).
- `HexBin` &mdash; a `TypedDict` for the aggregated bin passed to the hex-bin
  styling callbacks (`{"h3Idx", "points", "sumWeight"}`). Annotate against it for
  autocomplete on the bin keys. (It is an opt-in aid: the hex-bin fields stay
  loosely typed so a plain `def fn(b: dict)` still type checks.)

MicroPython parses and ignores annotations, so annotating is always safe:

```python
from pyglobegl import ColorInterpolator, frontend_python


@frontend_python
def gradient(t: float) -> str:  # ColorInterpolator; t may be int at the endpoints
    red = int(255 * t)
    return f"rgb({red},0,{255 - red})"
```

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
    closures over your notebook's variables or third-party imports. Only the
    function's own source is shipped, so module-level names defined elsewhere are
    not available when it runs.

## Callback reference

Every accessor below takes a single argument and returns a single value; nothing
else is accessible inside the callback (see
[above](#what-your-callback-receives-and-what-it-can-access)).

| Callback (layer) | Argument | Returns | When it runs |
| --- | --- | --- | --- |
| `arc_color_fn` (arcs) | `t: float` in `[0, 1]`, start &rarr; end | CSS colour `str` | data change |
| `path_color_fn` (paths) | `t: float` in `[0, 1]`, start &rarr; end | CSS colour `str` | data change |
| `ring_color_fn` (rings) | `t: float` in `[0, 1]`, propagation | CSS colour `str` | per frame while a ring expands |
| `heatmap_color_fn` (heatmaps) | `t: float` in `[0, 1]`, normalised density | CSS colour `str` | data change |
| `hex_top_color` / `hex_side_color` (hex bin) | `hexbin: dict` | CSS colour `str` | data change |
| `hex_altitude` (hex bin) | `hexbin: dict` | non-negative `float` (globe-radius units) | data change |
| `hex_label` (hex bin) | `hexbin: dict` | HTML/text tooltip `str` | on hover |
| `hex_bin_point_lat` / `_lng` / `_weight` (hex bin) | `point: dict` | `float` | data change |
| `hex_margin` (hex bin) | `hexbin: dict` | `float` | data change |

The colour-gradient callbacks (`arc_color_fn`, `path_color_fn`, `ring_color_fn`)
are a *layer-level override*: when set, they replace the per-datum `color` field
for every element in the layer. Pass `None` (the default) to keep per-datum
colours.

!!! tip "Read dict inputs defensively"

    Upstream globe.gl shapes (such as the hex-bin aggregate) can change between
    versions. Prefer `arg.get("key", default)` over direct indexing so a missing
    key degrades gracefully. See the
    [hex bin callback I/O table](../layers/hex-bin.md#callback-io) for the exact
    `hexbin` / `point` dict shapes.
