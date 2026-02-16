from __future__ import annotations

import pytest

from pyglobegl import (
    frontend_python,
    FrontendPythonFunction,
    GlobeConfig,
    GlobeViewConfig,
    HexBinLayerConfig,
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


def test_view_config_serializes_controls_auto_rotate_settings() -> None:
    config = GlobeConfig(
        view=GlobeViewConfig(controls_auto_rotate=True, controls_auto_rotate_speed=0.6)
    )
    payload = config.model_dump(by_alias=True, exclude_none=True, mode="json")

    assert payload["view"]["controlsAutoRotate"] is True
    assert payload["view"]["controlsAutoRotateSpeed"] == pytest.approx(0.6)
