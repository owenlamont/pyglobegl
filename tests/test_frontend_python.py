from __future__ import annotations

import pytest

from pyglobegl import (
    ArcsLayerConfig,
    frontend_python,
    FrontendPythonFunction,
    GlobeConfig,
    GlobeViewConfig,
    GlobeWidget,
    HeatmapsLayerConfig,
    HexBin,
    HexBinLayerConfig,
    HexedPolygonsLayerConfig,
    LabelsLayerConfig,
    ParticlesLayerConfig,
    PathsLayerConfig,
    PointsLayerConfig,
    PolygonsLayerConfig,
    RingsLayerConfig,
    TilesLayerConfig,
)


def test_frontend_python_decorator_keeps_callable() -> None:
    @frontend_python
    def my_hex_altitude(hexbin):
        return hexbin["sumWeight"] * 0.02

    assert my_hex_altitude({"sumWeight": 5}) == pytest.approx(0.1)


def test_hexbin_config_serializes_frontend_python_function() -> None:
    @frontend_python
    def color_fn(hexbin):
        if hexbin["sumWeight"] > 10:
            return "#ff5500"
        return "#3366ff"

    config = GlobeConfig(hex_bin=HexBinLayerConfig(hex_top_color=color_fn))
    payload = config.model_dump(by_alias=True, exclude_none=True, mode="json")
    hex_top_color = payload["hex_bin"]["hexTopColor"]

    assert isinstance(hex_top_color, dict)
    assert hex_top_color["__pyglobegl_type"] == "frontend_python_function"
    assert hex_top_color["name"] == "color_fn"
    assert "def color_fn" in hex_top_color["source"]


def test_hexbin_config_accepts_explicit_frontend_python_function() -> None:
    fn = FrontendPythonFunction(
        name="hex_alt", source="def hex_alt(hexbin):\n    return 0.1"
    )

    config = GlobeConfig(hex_bin=HexBinLayerConfig(hex_altitude=fn))
    payload = config.model_dump(by_alias=True, exclude_none=True, mode="json")

    assert payload["hex_bin"]["hexAltitude"]["name"] == "hex_alt"


def test_hexbin_config_serializes_frontend_python_label_function() -> None:
    @frontend_python
    def label_fn(hexbin):
        return f"<b>{len(hexbin['points'])}</b>"

    config = GlobeConfig(hex_bin=HexBinLayerConfig(hex_label=label_fn))
    payload = config.model_dump(by_alias=True, exclude_none=True, mode="json")
    hex_label = payload["hex_bin"]["hexLabel"]

    assert isinstance(hex_label, dict)
    assert hex_label["__pyglobegl_type"] == "frontend_python_function"
    assert hex_label["name"] == "label_fn"
    assert "def label_fn" in hex_label["source"]


def test_hexbin_config_serializes_frontend_python_margin_and_point_weight() -> None:
    @frontend_python
    def margin_fn(hexbin):
        return 0.15 if float(hexbin["sumWeight"]) > 5 else 0.02

    @frontend_python
    def point_weight_fn(point):
        return float(point["magnitude"]) * 2.0

    config = GlobeConfig(
        hex_bin=HexBinLayerConfig(
            hex_margin=margin_fn, hex_bin_point_weight=point_weight_fn
        )
    )
    payload = config.model_dump(by_alias=True, exclude_none=True, mode="json")
    hex_bin = payload["hex_bin"]

    assert isinstance(hex_bin["hexMargin"], dict)
    assert hex_bin["hexMargin"]["name"] == "margin_fn"
    assert isinstance(hex_bin["hexBinPointWeight"], dict)
    assert hex_bin["hexBinPointWeight"]["name"] == "point_weight_fn"


def test_heatmaps_config_serializes_frontend_python_color_fn() -> None:
    @frontend_python
    def colormap(t):
        channel = int(255 * t)
        return f"rgb({channel},0,{255 - channel})"

    config = GlobeConfig(heatmaps=HeatmapsLayerConfig(heatmap_color_fn=colormap))
    payload = config.model_dump(by_alias=True, exclude_none=True, mode="json")
    color_fn = payload["heatmaps"]["heatmapColorFn"]

    assert isinstance(color_fn, dict)
    assert color_fn["__pyglobegl_type"] == "frontend_python_function"
    assert color_fn["name"] == "colormap"
    assert "def colormap" in color_fn["source"]


def test_heatmaps_config_accepts_explicit_frontend_python_function() -> None:
    fn = FrontendPythonFunction(
        name="ramp", source="def ramp(t):\n    return '#ff0000'"
    )

    config = GlobeConfig(heatmaps=HeatmapsLayerConfig(heatmap_color_fn=fn))
    payload = config.model_dump(by_alias=True, exclude_none=True, mode="json")

    assert payload["heatmaps"]["heatmapColorFn"]["name"] == "ramp"


def test_heatmaps_config_color_fn_defaults_to_none() -> None:
    payload = GlobeConfig(heatmaps=HeatmapsLayerConfig()).model_dump(
        by_alias=True, exclude_none=True, mode="json"
    )

    assert "heatmapColorFn" not in payload["heatmaps"]


def test_widget_round_trips_heatmaps_color_fn() -> None:
    @frontend_python
    def colormap(t):
        return f"rgb({int(255 * t)},0,0)"

    widget = GlobeWidget(config=GlobeConfig(heatmaps=HeatmapsLayerConfig()))
    assert widget.get_heatmaps_color_fn() is None

    widget.set_heatmaps_color_fn(colormap)
    resolved = widget.get_heatmaps_color_fn()
    assert isinstance(resolved, FrontendPythonFunction)
    assert resolved.name == "colormap"
    assert "def colormap" in resolved.source

    widget.set_heatmaps_color_fn(None)
    assert widget.get_heatmaps_color_fn() is None


def test_hexbin_callback_accepts_hexbin_typed_annotation() -> None:
    # Annotating the hex-bin callback against the exported HexBin TypedDict gives
    # editor autocomplete on the bin keys and still serializes for the wire.
    @frontend_python
    def bin_color(b: HexBin) -> str:
        return "#ff5500" if b["sumWeight"] > 10 else "#3366ff"

    config = GlobeConfig(hex_bin=HexBinLayerConfig(hex_top_color=bin_color))
    payload = config.model_dump(by_alias=True, exclude_none=True, mode="json")

    assert payload["hex_bin"]["hexTopColor"]["name"] == "bin_color"


@frontend_python
def _gradient(t: float) -> str:
    # Annotated against ColorInterpolator: passing it to the narrowed
    # *_color_fn fields type checks under ty.
    red = int(255 * t)
    return f"rgba({red},0,{255 - red},{t})"


# (layer key, config class, Python field, globe.gl alias, getter, setter).
_GRADIENT_LAYERS = [
    pytest.param(
        "arcs",
        ArcsLayerConfig,
        "arc_color_fn",
        "arcColor",
        "get_arcs_color_fn",
        "set_arcs_color_fn",
        id="arcs",
    ),
    pytest.param(
        "paths",
        PathsLayerConfig,
        "path_color_fn",
        "pathColor",
        "get_paths_color_fn",
        "set_paths_color_fn",
        id="paths",
    ),
    pytest.param(
        "rings",
        RingsLayerConfig,
        "ring_color_fn",
        "ringColor",
        "get_rings_color_fn",
        "set_rings_color_fn",
        id="rings",
    ),
]


@pytest.mark.parametrize(
    ("layer", "config_cls", "field", "alias", "getter", "setter"), _GRADIENT_LAYERS
)
def test_layer_config_serializes_gradient_color_fn(
    layer, config_cls, field, alias, getter, setter
) -> None:
    config = GlobeConfig(**{layer: config_cls(**{field: _gradient})})
    payload = config.model_dump(by_alias=True, exclude_none=True, mode="json")
    color_fn = payload[layer][alias]

    assert isinstance(color_fn, dict)
    assert color_fn["__pyglobegl_type"] == "frontend_python_function"
    assert color_fn["name"] == "_gradient"
    assert "def _gradient" in color_fn["source"]


@pytest.mark.parametrize(
    ("layer", "config_cls", "field", "alias", "getter", "setter"), _GRADIENT_LAYERS
)
def test_layer_config_accepts_explicit_gradient_color_fn(
    layer, config_cls, field, alias, getter, setter
) -> None:
    fn = FrontendPythonFunction(
        name="ramp", source="def ramp(t):\n    return '#ff0000'"
    )

    config = GlobeConfig(**{layer: config_cls(**{field: fn})})
    payload = config.model_dump(by_alias=True, exclude_none=True, mode="json")

    assert payload[layer][alias]["name"] == "ramp"


@pytest.mark.parametrize(
    ("layer", "config_cls", "field", "alias", "getter", "setter"), _GRADIENT_LAYERS
)
def test_layer_config_gradient_color_fn_defaults_to_none(
    layer, config_cls, field, alias, getter, setter
) -> None:
    payload = GlobeConfig(**{layer: config_cls()}).model_dump(
        by_alias=True, exclude_none=True, mode="json"
    )

    # The bare layer config never emits the gradient alias; the widget injects
    # the per-datum "color" field accessor instead (see the snapshot test below).
    assert alias not in payload.get(layer, {})


@pytest.mark.parametrize(
    ("layer", "config_cls", "field", "alias", "getter", "setter"), _GRADIENT_LAYERS
)
def test_widget_snapshot_gradient_overrides_field_accessor(
    layer, config_cls, field, alias, getter, setter
) -> None:
    default_widget = GlobeWidget(config=GlobeConfig(**{layer: config_cls()}))
    assert default_widget.config[layer][alias] == "color"

    grad_widget = GlobeWidget(
        config=GlobeConfig(**{layer: config_cls(**{field: _gradient})})
    )
    assert isinstance(grad_widget.config[layer][alias], dict)


@pytest.mark.parametrize(
    ("layer", "config_cls", "field", "alias", "getter", "setter"), _GRADIENT_LAYERS
)
def test_widget_round_trips_gradient_color_fn(
    layer, config_cls, field, alias, getter, setter
) -> None:
    widget = GlobeWidget(config=GlobeConfig(**{layer: config_cls()}))
    assert getattr(widget, getter)() is None

    getattr(widget, setter)(_gradient)
    resolved = getattr(widget, getter)()
    assert isinstance(resolved, FrontendPythonFunction)
    assert resolved.name == "_gradient"
    assert "def _gradient" in resolved.source

    getattr(widget, setter)(None)
    assert getattr(widget, getter)() is None


def test_view_config_serializes_controls_auto_rotate_settings() -> None:
    config = GlobeConfig(
        view=GlobeViewConfig(controls_auto_rotate=True, controls_auto_rotate_speed=0.6)
    )
    payload = config.model_dump(by_alias=True, exclude_none=True, mode="json")

    assert payload["view"]["controlsAutoRotate"] is True
    assert payload["view"]["controlsAutoRotateSpeed"] == pytest.approx(0.6)


@frontend_python
def _tooltip(datum) -> str:
    # Loosely typed datum dict (a stricter param would break by contravariance);
    # reads the per-datum label and wraps it in markup for the hover tooltip.
    return f"<b>{datum.get('label', '?')}</b>"


# (layer key, config class, Python field, globe.gl alias, getter, setter).
_LABEL_LAYERS = [
    pytest.param(
        "points",
        PointsLayerConfig,
        "point_label",
        "pointLabel",
        "get_point_label",
        "set_point_label",
        id="points",
    ),
    pytest.param(
        "arcs",
        ArcsLayerConfig,
        "arc_label",
        "arcLabel",
        "get_arc_label",
        "set_arc_label",
        id="arcs",
    ),
    pytest.param(
        "paths",
        PathsLayerConfig,
        "path_label",
        "pathLabel",
        "get_path_label",
        "set_path_label",
        id="paths",
    ),
    pytest.param(
        "polygons",
        PolygonsLayerConfig,
        "polygon_label",
        "polygonLabel",
        "get_polygon_label",
        "set_polygon_label",
        id="polygons",
    ),
    pytest.param(
        "hexed_polygons",
        HexedPolygonsLayerConfig,
        "hex_polygon_label",
        "hexPolygonLabel",
        "get_hex_polygon_label",
        "set_hex_polygon_label",
        id="hexed_polygons",
    ),
    pytest.param(
        "tiles",
        TilesLayerConfig,
        "tile_label",
        "tileLabel",
        "get_tile_label",
        "set_tile_label",
        id="tiles",
    ),
    pytest.param(
        "particles",
        ParticlesLayerConfig,
        "particle_label",
        "particleLabel",
        "get_particle_label",
        "set_particle_label",
        id="particles",
    ),
    pytest.param(
        "labels",
        LabelsLayerConfig,
        "label_label",
        "labelLabel",
        "get_label_label",
        "set_label_label",
        id="labels",
    ),
]


@pytest.mark.parametrize(
    ("layer", "config_cls", "field", "alias", "getter", "setter"), _LABEL_LAYERS
)
def test_layer_config_serializes_label_callback(
    layer, config_cls, field, alias, getter, setter
) -> None:
    config = GlobeConfig(**{layer: config_cls(**{field: _tooltip})})
    payload = config.model_dump(by_alias=True, exclude_none=True, mode="json")
    label = payload[layer][alias]

    assert isinstance(label, dict)
    assert label["__pyglobegl_type"] == "frontend_python_function"
    assert label["name"] == "_tooltip"
    assert "def _tooltip" in label["source"]


@pytest.mark.parametrize(
    ("layer", "config_cls", "field", "alias", "getter", "setter"), _LABEL_LAYERS
)
def test_layer_config_serializes_label_constant_string(
    layer, config_cls, field, alias, getter, setter
) -> None:
    config = GlobeConfig(**{layer: config_cls(**{field: "Tooltip text"})})
    payload = config.model_dump(by_alias=True, exclude_none=True, mode="json")

    assert payload[layer][alias] == "Tooltip text"


@pytest.mark.parametrize(
    ("layer", "config_cls", "field", "alias", "getter", "setter"), _LABEL_LAYERS
)
def test_layer_config_accepts_explicit_label_function(
    layer, config_cls, field, alias, getter, setter
) -> None:
    fn = FrontendPythonFunction(name="tip", source="def tip(d):\n    return 'x'")

    config = GlobeConfig(**{layer: config_cls(**{field: fn})})
    payload = config.model_dump(by_alias=True, exclude_none=True, mode="json")

    assert payload[layer][alias]["name"] == "tip"


@pytest.mark.parametrize(
    ("layer", "config_cls", "field", "alias", "getter", "setter"), _LABEL_LAYERS
)
def test_layer_config_label_defaults_to_none(
    layer, config_cls, field, alias, getter, setter
) -> None:
    payload = GlobeConfig(**{layer: config_cls()}).model_dump(
        by_alias=True, exclude_none=True, mode="json"
    )

    assert alias not in payload.get(layer, {})


@pytest.mark.parametrize(
    ("layer", "config_cls", "field", "alias", "getter", "setter"), _LABEL_LAYERS
)
def test_widget_snapshot_label_default_omits_alias(
    layer, config_cls, field, alias, getter, setter
) -> None:
    # Unlike the gradient accessors (which inject the per-datum "color" field
    # accessor on the wire), the label default is omitted: the frontend pre-binds
    # the "label" field accessor instead, so a user string can be a constant.
    default_widget = GlobeWidget(config=GlobeConfig(**{layer: config_cls()}))
    assert alias not in default_widget.config.get(layer, {})

    callback_widget = GlobeWidget(
        config=GlobeConfig(**{layer: config_cls(**{field: _tooltip})})
    )
    assert isinstance(callback_widget.config[layer][alias], dict)

    const_widget = GlobeWidget(
        config=GlobeConfig(**{layer: config_cls(**{field: "Tip"})})
    )
    assert const_widget.config[layer][alias] == "Tip"


@pytest.mark.parametrize(
    ("layer", "config_cls", "field", "alias", "getter", "setter"), _LABEL_LAYERS
)
def test_widget_round_trips_label(
    layer, config_cls, field, alias, getter, setter
) -> None:
    widget = GlobeWidget(config=GlobeConfig(**{layer: config_cls()}))
    assert getattr(widget, getter)() is None

    getattr(widget, setter)(_tooltip)
    resolved = getattr(widget, getter)()
    assert isinstance(resolved, FrontendPythonFunction)
    assert resolved.name == "_tooltip"
    assert "def _tooltip" in resolved.source

    getattr(widget, setter)("Static tip")
    assert getattr(widget, getter)() == "Static tip"

    getattr(widget, setter)(None)
    assert getattr(widget, getter)() is None
