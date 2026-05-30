# Installation

`pyglobegl` is published on PyPI and requires Python 3.10 or newer.

=== "pip"

    ```bash
    pip install pyglobegl
    ```

=== "uv"

    ```bash
    uv add pyglobegl
    ```

The wheel bundles a **prebuilt JupyterLab extension**, so there is no separate
`jupyter labextension` build or install step &mdash; install the package and the
widget is ready in JupyterLab, Jupyter Notebook, Colab, VS Code, and marimo.

## Optional extras

### GeoPandas

Adds GeoPandas and Pandera for the [GeoPandas helpers](../integrations/geopandas.md):

=== "pip"

    ```bash
    pip install "pyglobegl[geopandas]"
    ```

=== "uv"

    ```bash
    uv add "pyglobegl[geopandas]"
    ```

### MovingPandas

Adds MovingPandas (and GeoPandas + Pandera) for the
[MovingPandas helpers](../integrations/movingpandas.md):

=== "pip"

    ```bash
    pip install "pyglobegl[movingpandas]"
    ```

=== "uv"

    ```bash
    uv add "pyglobegl[movingpandas]"
    ```

## Verify the install

```python
from importlib.metadata import version

print(version("pyglobegl"))
```

Then head to the [Quick start](quickstart.md) to render your first globe.
