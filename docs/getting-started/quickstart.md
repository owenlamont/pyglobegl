# Quick start

`GlobeWidget` is the single entry point. Display it like any other widget and an
interactive WebGL globe renders inline in your notebook.

## A bare globe

```python
from IPython.display import display

from pyglobegl import GlobeWidget

display(GlobeWidget())
```

## A textured Earth with points

Pass a [`GlobeConfig`](../layers/globe.md) to configure the globe texture and any
layers. Here we set the day-time Earth texture and add two points:

```python
from IPython.display import display

from pyglobegl import (
    GlobeConfig,
    GlobeLayerConfig,
    GlobeWidget,
    PointDatum,
    PointsLayerConfig,
)

points = [
    PointDatum(lat=0, lng=0, altitude=0.25, color="#ff0000", label="Center"),
    PointDatum(lat=15, lng=-45, altitude=0.12, color="#00ff00", label="West"),
]

config = GlobeConfig(
    globe=GlobeLayerConfig(
        globe_image_url="https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-day.jpg"
    ),
    points=PointsLayerConfig(points_data=points),
)

display(GlobeWidget(config=config))
```

## How layer data works

pyglobegl expects layer data as **Pydantic models**, one type per layer:
`PointDatum`, `ArcDatum`, `PolygonDatum`, `PathDatum`, `HeatmapDatum`,
`HexBinPointDatum`, `HexPolygonDatum`, `TileDatum`, `ParticleDatum`, `RingDatum`,
and `LabelDatum`.

!!! note "Field names are the accessors"

    Dynamic accessor remapping is not supported &mdash; per-datum values are read
    from the model field names. Numeric fields reject string values, and each
    model's defaults mirror globe.gl's defaults so omitted values still render
    predictably.

!!! tip "Extra metadata is allowed"

    The canonical fields on each model are fixed, but you can attach extra fields
    for your own metadata; they travel with the datum and are available in
    callbacks.

## Next steps

- [Globe & images](../layers/globe.md) &mdash; textures, atmosphere, camera, and
  passing PIL images.
- [Points](../layers/points.md) and the other [layers](../layers/globe.md).
- [Runtime updates & callbacks](../guides/runtime-updates.md) &mdash; change data
  after render and respond to user input.
