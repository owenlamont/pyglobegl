# pyglobegl

[anywidget](https://github.com/manzt/anywidget) wrapper for
[globe.gl](https://github.com/vasturiano/globe.gl) with integrations with
popular Python spatial packages.

![pyglobegl rendering a population hex-bin layer on the globe](https://raw.githubusercontent.com/owenlamont/pyglobegl/main/docs/images/layers/hex-bin.png)

📖 **Full documentation: <https://pyglobegl.pages.dev/>**

pyglobegl renders interactive WebGL globes in modern notebook environments
(Jupyter, JupyterLab, Colab, VS Code, marimo) and drives them from a friendly,
strongly typed Python API. It ships a prebuilt JupyterLab extension, so
`pip install` is all you need.

## Installation

```bash
pip install pyglobegl
```

Optional spatial extras:

```bash
pip install "pyglobegl[geopandas]"     # GeoPandas + Pandera helpers
pip install "pyglobegl[movingpandas]"  # MovingPandas (includes GeoPandas)
```

See the [installation guide](https://pyglobegl.pages.dev/getting-started/installation/)
for uv and extras details.

## Quick start

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

Layer data are typed Pydantic models (no dynamic accessor remapping), and
defaults mirror globe.gl so omitted values still render predictably. See the
[quick start](https://pyglobegl.pages.dev/getting-started/quickstart/) for more.

## Layers & features

Each globe.gl layer is exposed as typed data models:

- [Globe & images](https://pyglobegl.pages.dev/layers/globe/)
- [Points](https://pyglobegl.pages.dev/layers/points/)
- [Arcs](https://pyglobegl.pages.dev/layers/arcs/)
- [Polygons](https://pyglobegl.pages.dev/layers/polygons/)
- [Paths](https://pyglobegl.pages.dev/layers/paths/)
- [Heatmaps](https://pyglobegl.pages.dev/layers/heatmaps/)
- [Hex bin](https://pyglobegl.pages.dev/layers/hex-bin/)
- [Hexed polygons](https://pyglobegl.pages.dev/layers/hexed-polygons/)
- [Tiles](https://pyglobegl.pages.dev/layers/tiles/)
- [Particles](https://pyglobegl.pages.dev/layers/particles/)
- [Rings](https://pyglobegl.pages.dev/layers/rings/)
- [Labels](https://pyglobegl.pages.dev/layers/labels/)

Plus:

- [Runtime updates & callbacks](https://pyglobegl.pages.dev/guides/runtime-updates/)
  — update data and respond to hover/click after render
- [Frontend Python callbacks](https://pyglobegl.pages.dev/guides/frontend-callbacks/)
  — `@frontend_python` accessors that run in the browser
- [GeoPandas helpers](https://pyglobegl.pages.dev/integrations/geopandas/)
  — build layer data straight from GeoDataFrames
- [MovingPandas helpers](https://pyglobegl.pages.dev/integrations/movingpandas/)
  — render trajectories as paths

## Documentation

- [Getting started](https://pyglobegl.pages.dev/getting-started/installation/)
- [Layers](https://pyglobegl.pages.dev/layers/globe/)
- [Guides](https://pyglobegl.pages.dev/guides/runtime-updates/)
- [Integrations](https://pyglobegl.pages.dev/integrations/geopandas/)
- [Goals & roadmap](https://pyglobegl.pages.dev/about/roadmap/)

## Contributing

### Build Assets (Release Checklist)

1. `cd frontend && pnpm run build`
2. `uv build`

### UI Test Artifacts

- Canvas captures are saved under `ui-artifacts` as
  `{test-name}-pass-<timestamp>.png` or `{test-name}-fail-<timestamp>.png`.
- Canvas comparisons use SSIM (structural similarity) with a fixed threshold
  (currently `0.86`).
