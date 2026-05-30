# Runtime Updates & Callbacks

Once a `GlobeWidget` is rendered you can change its data and accessors in place,
and respond to user interaction with Python callbacks. Every datum gets an
auto-generated UUID4 `id` unless you provide one, and callback payloads include
that datum (and its `id`) so you can update visuals in response to input.

```python
from IPython.display import display

widget = GlobeWidget(config=config)
display(widget)


def on_polygon_hover(current, previous):
    if previous:
        widget.update_polygon(
            previous["id"],
            cap_color=previous["base_color"],
            altitude=previous["altitude"],
        )
    if current:
        widget.update_polygon(
            current["id"],
            cap_color="#2f80ff",
            altitude=current["altitude"] + 0.03,
        )


widget.on_polygon_hover(on_polygon_hover)
```

## Updating data

Use the `GlobeWidget` setters to replace or patch layer data after render. Batch
updates use the per-layer **patch models** so changes serialize with the correct
globe.gl field names:

`PointDatumPatch`, `ArcDatumPatch`, `PolygonDatumPatch`, `PathDatumPatch`,
`HeatmapDatumPatch`, `HexPolygonDatumPatch`, `TileDatumPatch`,
`ParticleDatumPatch`, `RingDatumPatch`, and `LabelDatumPatch`.

!!! note "Validated ids"

    Runtime update helpers validate UUID4 ids; an invalid id raises a validation
    error rather than silently no-op'ing.

## Hover callbacks

Hover callbacks are **only wired when you register a hover handler**. This avoids
continuous hover traffic for layers you are not interacting with, and matches
globe.gl behaviour (no hover cursor when no hover callback is registered).

!!! tip "Stash the base state"

    A hover handler receives both the `current` and `previous` datum, so you can
    restore the previous datum's appearance and highlight the new one &mdash; as
    in the example above, which reads a `base_color` extra field stored on each
    datum.
