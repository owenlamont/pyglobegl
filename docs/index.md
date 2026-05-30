---
icon: lucide/globe
---

# pyglobegl

## An anywidget wrapper for globe.gl

`pyglobegl` wraps [globe.gl](https://github.com/vasturiano/globe.gl) as an
[anywidget](https://github.com/manzt/anywidget), so you can render interactive
WebGL globes in modern notebook environments &mdash; Jupyter, JupyterLab, Colab,
VS Code, and marimo &mdash; and drive them from a friendly, strongly typed Python
API. It ships a prebuilt JupyterLab extension, so `pip install` is all you need.

![pyglobegl rendering a population hex-bin layer on the globe](images/layers/hex-bin.png)

<div class="grid cards" markdown>

-   :material-layers-triple:{ .lg .middle } **Twelve typed layers**

    ---

    Points, arcs, polygons, paths, heatmaps, hex bins, hexed polygons, tiles,
    particles, rings, and labels &mdash; every layer is driven by Pydantic data
    models, not raw dicts.

    [:octicons-arrow-right-24: Browse the layers](layers/globe.md)

-   :material-map-search:{ .lg .middle } **Spatial data, built in**

    ---

    Turn GeoDataFrames and MovingPandas trajectories straight into layer data
    with Pandera-validated helpers that reproject to EPSG:4326 for you.

    [:octicons-arrow-right-24: Integrations](integrations/geopandas.md)

-   :material-update:{ .lg .middle } **Live updates & callbacks**

    ---

    Update data and accessors after render, and respond to hover/click with
    Python callbacks that receive each datum and its stable `id`.

    [:octicons-arrow-right-24: Runtime updates](guides/runtime-updates.md)

-   :material-package-variant-closed:{ .lg .middle } **Drop-in install**

    ---

    `pip install pyglobegl` ships the prebuilt JupyterLab extension &mdash; no
    separate lab build or extension install step.

    [:octicons-arrow-right-24: Install](getting-started/installation.md)

</div>

## Quick start

```python
from IPython.display import display

from pyglobegl import GlobeWidget

display(GlobeWidget())
```

That renders a bare globe. Add a textured Earth and a points layer:

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

## Design at a glance

- **Typed data, not accessors.** Layer data are Pydantic models (`PointDatum`,
  `ArcDatum`, `PolygonDatum`, …). Dynamic accessor remapping and string
  field-name accessors are intentionally not exposed; per-datum values come from
  model field names.
- **globe.gl defaults, mirrored.** Omitted fields fall back to globe.gl's own
  defaults, so partial configs still render predictably.
- **Numbers stay numbers.** Numeric fields reject string values to catch
  mistakes early.

## Next steps

<div class="grid cards" markdown>

-   [:octicons-download-24: __Install pyglobegl__](getting-started/installation.md)

    pip or uv, plus the optional GeoPandas and MovingPandas extras.

-   [:octicons-play-24: __Render your first globe__](getting-started/quickstart.md)

    A textured Earth with a points layer in under a minute.

-   [:octicons-book-24: __Explore the layers__](layers/globe.md)

    One focused page per globe.gl layer, each with a runnable example.

-   [:octicons-gear-24: __Goals & roadmap__](about/roadmap.md)

    What pyglobegl supports today and where it is headed.

</div>
