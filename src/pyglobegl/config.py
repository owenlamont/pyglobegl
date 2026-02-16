from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Annotated, Any, Literal
from uuid import uuid4

from geojson_pydantic import MultiPolygon, Polygon
from pydantic import (
    AnyUrl,
    BaseModel,
    BeforeValidator,
    Field,
    field_serializer,
    model_validator,
    StrictStr,
    UUID4,
)
from pydantic_extra_types.color import Color

from pyglobegl.frontend_python import (
    FrontendPythonFunction,
    resolve_frontend_python_function,
)


FiniteFloat = Annotated[float, Field(allow_inf_nan=False)]
NonNegativeFloat = Annotated[float, Field(ge=0, allow_inf_nan=False)]
PositiveFloat = Annotated[float, Field(gt=0, allow_inf_nan=False)]
Latitude = Annotated[float, Field(ge=-90, le=90, allow_inf_nan=False)]
Longitude = Annotated[float, Field(ge=-180, le=180, allow_inf_nan=False)]
PathCoordinate = (
    tuple[FiniteFloat, FiniteFloat] | tuple[FiniteFloat, FiniteFloat, FiniteFloat]
)


def _to_color(value: Any) -> Color:
    if isinstance(value, Color):
        return value
    return Color(value)


ColorValue = Annotated[Color | str, BeforeValidator(_to_color)]
FrontendPythonFunctionInput = FrontendPythonFunction | Callable[..., Any]


def _serialize_color_single(value: ColorValue | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _serialize_color_list(
    value: ColorValue | list[ColorValue] | None,
) -> str | list[str] | None:
    if value is None:
        return None
    if isinstance(value, list):
        return [str(item) for item in value]
    return str(value)


def _serialize_color_list_required(
    value: ColorValue | list[ColorValue],
) -> str | list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return str(value)


def _serialize_hexbin_accessor(
    value: ColorValue | FrontendPythonFunction | str | float | None,
) -> str | float | dict[str, str] | None:
    if value is None:
        return None
    if callable(value):
        value = resolve_frontend_python_function(value)
    if isinstance(value, FrontendPythonFunction):
        return value.to_wire()
    if isinstance(value, Color):
        return str(value)
    return value


def _default_hex_altitude_accessor() -> FrontendPythonFunction:
    return FrontendPythonFunction(
        name="pyglobegl_default_hex_altitude",
        source=(
            "def pyglobegl_default_hex_altitude(hexbin):\n"
            '    return hexbin["sumWeight"] * 0.01'
        ),
    )


def _default_tile_material() -> GlobeMaterialSpec:
    return GlobeMaterialSpec(
        type="MeshLambertMaterial",
        params={"color": "#ffbb88", "opacity": 0.4, "transparent": True},
    )


class GlobeInitConfig(BaseModel, extra="forbid", frozen=True):
    """Initialization settings for globe.gl."""

    renderer_config: Annotated[
        Mapping[str, Any] | None, Field(serialization_alias="rendererConfig")
    ] = None
    wait_for_globe_ready: Annotated[
        bool, Field(serialization_alias="waitForGlobeReady")
    ] = True
    animate_in: Annotated[bool, Field(serialization_alias="animateIn")] = True


class GlobeLayoutConfig(BaseModel, extra="forbid", frozen=True):
    """Layout settings for globe.gl rendering."""

    width: Annotated[int | None, Field(gt=0)] = None
    height: Annotated[int | None, Field(gt=0)] = None
    globe_offset: Annotated[
        tuple[float, float] | None, Field(serialization_alias="globeOffset")
    ] = None
    background_color: Annotated[
        str | None, Field(serialization_alias="backgroundColor")
    ] = None
    background_image_url: Annotated[
        AnyUrl | None, Field(serialization_alias="backgroundImageUrl")
    ] = None

    @field_serializer("background_image_url", when_used="always")
    def _serialize_background_image(self, value: AnyUrl | None) -> str | None:
        return str(value) if value is not None else None


class GlobeMaterialSpec(BaseModel, extra="forbid", frozen=True):
    """Specification for constructing a ThreeJS material in the frontend."""

    type: str
    # Keep explicit default assignment for type checkers even with Annotated Field.
    params: Annotated[dict[str, Any], Field(default_factory=dict)] = Field(
        default_factory=dict
    )


class GlobeLayerConfig(BaseModel, extra="forbid", frozen=True):
    """Globe layer settings for globe.gl."""

    globe_image_url: Annotated[
        AnyUrl | None, Field(serialization_alias="globeImageUrl")
    ] = None
    bump_image_url: Annotated[
        AnyUrl | None, Field(serialization_alias="bumpImageUrl")
    ] = None
    globe_tile_engine_url: Annotated[
        str | None, Field(serialization_alias="globeTileEngineUrl")
    ] = None
    show_globe: Annotated[bool, Field(serialization_alias="showGlobe")] = True
    show_graticules: Annotated[bool, Field(serialization_alias="showGraticules")] = (
        False
    )
    show_atmosphere: Annotated[bool, Field(serialization_alias="showAtmosphere")] = True
    atmosphere_color: Annotated[
        str | None, Field(serialization_alias="atmosphereColor")
    ] = None
    atmosphere_altitude: Annotated[
        float | None, Field(serialization_alias="atmosphereAltitude")
    ] = None
    globe_curvature_resolution: Annotated[
        float | None, Field(serialization_alias="globeCurvatureResolution")
    ] = None
    globe_material: Annotated[
        GlobeMaterialSpec | None, Field(serialization_alias="globeMaterial")
    ] = None

    @field_serializer("globe_image_url", "bump_image_url", when_used="always")
    def _serialize_globe_images(self, value: AnyUrl | None) -> str | None:
        return str(value) if value is not None else None


class PointDatum(BaseModel, extra="allow", frozen=True):
    """Data model for a points layer entry."""

    id: Annotated[UUID4, Field(default_factory=uuid4)] = Field(default_factory=uuid4)
    lat: Latitude
    lng: Longitude
    altitude: NonNegativeFloat = 0.1
    radius: PositiveFloat = 0.25
    color: ColorValue = Color("#ffffaa")
    label: StrictStr | None = None

    @field_serializer("color", when_used="always")
    def _serialize_color(self, value: ColorValue) -> str:
        return str(value)


class PointDatumPatch(BaseModel, extra="allow", frozen=True):
    """Patch model for a points layer entry."""

    id: UUID4
    lat: Latitude | None = None
    lng: Longitude | None = None
    altitude: NonNegativeFloat | None = None
    radius: PositiveFloat | None = None
    color: ColorValue | None = None
    label: StrictStr | None = None

    @field_serializer("color", when_used="always")
    def _serialize_color(self, value: ColorValue | None) -> str | None:
        return _serialize_color_single(value)

    @model_validator(mode="after")
    def _reject_none_for_required_fields(self) -> PointDatumPatch:
        for field in ("lat", "lng", "altitude", "radius", "color"):
            if field in self.__pydantic_fields_set__ and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be None.")
        return self


class PointsLayerConfig(BaseModel, extra="forbid", frozen=True):
    """Points layer settings for globe.gl."""

    points_data: Annotated[
        list[PointDatum] | None, Field(serialization_alias="pointsData")
    ] = None
    point_resolution: Annotated[
        int, Field(gt=0, serialization_alias="pointResolution")
    ] = 12
    points_merge: Annotated[bool, Field(serialization_alias="pointsMerge")] = False
    points_transition_duration: Annotated[
        int, Field(serialization_alias="pointsTransitionDuration")
    ] = 1000


class ArcDatum(BaseModel, extra="allow", frozen=True):
    """Data model for an arcs layer entry."""

    id: Annotated[UUID4, Field(default_factory=uuid4)] = Field(default_factory=uuid4)
    start_lat: Annotated[Latitude, Field(serialization_alias="startLat")]
    start_lng: Annotated[Longitude, Field(serialization_alias="startLng")]
    end_lat: Annotated[Latitude, Field(serialization_alias="endLat")]
    end_lng: Annotated[Longitude, Field(serialization_alias="endLng")]
    start_altitude: Annotated[
        NonNegativeFloat, Field(default=0.0, serialization_alias="startAltitude")
    ] = 0.0
    end_altitude: Annotated[
        NonNegativeFloat, Field(default=0.0, serialization_alias="endAltitude")
    ] = 0.0
    altitude: Annotated[
        NonNegativeFloat | None, Field(serialization_alias="altitude")
    ] = None
    altitude_auto_scale: Annotated[
        NonNegativeFloat, Field(serialization_alias="altitudeAutoScale")
    ] = 0.5
    stroke: Annotated[PositiveFloat | None, Field(serialization_alias="stroke")] = None
    dash_length: Annotated[PositiveFloat, Field(serialization_alias="dashLength")] = 1.0
    dash_gap: Annotated[NonNegativeFloat, Field(serialization_alias="dashGap")] = 0.0
    dash_initial_gap: Annotated[
        NonNegativeFloat, Field(serialization_alias="dashInitialGap")
    ] = 0.0
    dash_animate_time: Annotated[
        NonNegativeFloat, Field(serialization_alias="dashAnimateTime")
    ] = 0.0
    color: ColorValue | list[ColorValue] = Color("#ffffaa")
    label: StrictStr | None = None

    @field_serializer("color", when_used="always")
    def _serialize_color(self, value: ColorValue | list[ColorValue]) -> str | list[str]:
        return _serialize_color_list_required(value)


class ArcDatumPatch(BaseModel, extra="allow", frozen=True):
    """Patch model for an arcs layer entry."""

    id: UUID4
    start_lat: Annotated[Latitude | None, Field(serialization_alias="startLat")] = None
    start_lng: Annotated[Longitude | None, Field(serialization_alias="startLng")] = None
    end_lat: Annotated[Latitude | None, Field(serialization_alias="endLat")] = None
    end_lng: Annotated[Longitude | None, Field(serialization_alias="endLng")] = None
    start_altitude: Annotated[
        NonNegativeFloat | None, Field(serialization_alias="startAltitude")
    ] = None
    end_altitude: Annotated[
        NonNegativeFloat | None, Field(serialization_alias="endAltitude")
    ] = None
    altitude: Annotated[
        NonNegativeFloat | None, Field(serialization_alias="altitude")
    ] = None
    altitude_auto_scale: Annotated[
        NonNegativeFloat | None, Field(serialization_alias="altitudeAutoScale")
    ] = None
    stroke: Annotated[PositiveFloat | None, Field(serialization_alias="stroke")] = None
    dash_length: Annotated[
        PositiveFloat | None, Field(serialization_alias="dashLength")
    ] = None
    dash_gap: Annotated[
        NonNegativeFloat | None, Field(serialization_alias="dashGap")
    ] = None
    dash_initial_gap: Annotated[
        NonNegativeFloat | None, Field(serialization_alias="dashInitialGap")
    ] = None
    dash_animate_time: Annotated[
        NonNegativeFloat | None, Field(serialization_alias="dashAnimateTime")
    ] = None
    color: ColorValue | list[ColorValue] | None = None
    label: StrictStr | None = None

    @field_serializer("color", when_used="always")
    def _serialize_color(
        self, value: ColorValue | list[ColorValue] | None
    ) -> str | list[str] | None:
        return _serialize_color_list(value)

    @model_validator(mode="after")
    def _reject_none_for_required_fields(self) -> ArcDatumPatch:
        for field in (
            "start_lat",
            "start_lng",
            "end_lat",
            "end_lng",
            "start_altitude",
            "end_altitude",
            "altitude_auto_scale",
            "dash_length",
            "dash_gap",
            "dash_initial_gap",
            "dash_animate_time",
            "color",
        ):
            if field in self.__pydantic_fields_set__ and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be None.")
        return self


class ArcsLayerConfig(BaseModel, extra="forbid", frozen=True):
    """Arcs layer settings for globe.gl."""

    arcs_data: Annotated[
        list[ArcDatum] | None, Field(serialization_alias="arcsData")
    ] = None
    arc_curve_resolution: Annotated[
        int, Field(gt=0, serialization_alias="arcCurveResolution")
    ] = 64
    arc_circular_resolution: Annotated[
        int, Field(gt=0, serialization_alias="arcCircularResolution")
    ] = 6
    arcs_transition_duration: Annotated[
        int, Field(serialization_alias="arcsTransitionDuration")
    ] = 1000


class PolygonDatum(BaseModel, extra="allow", frozen=True):
    """Data model for a polygons layer entry."""

    id: Annotated[UUID4, Field(default_factory=uuid4)] = Field(default_factory=uuid4)
    geometry: Polygon | MultiPolygon
    name: StrictStr | None = None
    label: StrictStr | None = None
    cap_color: ColorValue = Color("#ffffaa")
    side_color: ColorValue = Color("#ffffaa")
    stroke_color: ColorValue | None = None
    altitude: NonNegativeFloat = 0.01
    cap_curvature_resolution: PositiveFloat = 5.0

    @field_serializer("cap_color", "side_color", "stroke_color", when_used="always")
    def _serialize_colors(self, value: ColorValue | None) -> str | None:
        return _serialize_color_single(value)


class PolygonDatumPatch(BaseModel, extra="allow", frozen=True):
    """Patch model for a polygons layer entry."""

    id: UUID4
    geometry: Polygon | MultiPolygon | None = None
    name: StrictStr | None = None
    label: StrictStr | None = None
    cap_color: ColorValue | None = None
    side_color: ColorValue | None = None
    stroke_color: ColorValue | None = None
    altitude: NonNegativeFloat | None = None
    cap_curvature_resolution: PositiveFloat | None = None

    @field_serializer("cap_color", "side_color", "stroke_color", when_used="always")
    def _serialize_colors(self, value: ColorValue | None) -> str | None:
        return _serialize_color_single(value)

    @model_validator(mode="after")
    def _reject_none_for_required_fields(self) -> PolygonDatumPatch:
        for field in (
            "geometry",
            "cap_color",
            "side_color",
            "altitude",
            "cap_curvature_resolution",
        ):
            if field in self.__pydantic_fields_set__ and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be None.")
        return self


class PolygonsLayerConfig(BaseModel, extra="forbid", frozen=True):
    """Polygons layer settings for globe.gl."""

    polygons_data: Annotated[
        list[PolygonDatum] | None, Field(serialization_alias="polygonsData")
    ] = None
    polygon_cap_material: Annotated[
        GlobeMaterialSpec | None, Field(serialization_alias="polygonCapMaterial")
    ] = None
    polygon_side_material: Annotated[
        GlobeMaterialSpec | None, Field(serialization_alias="polygonSideMaterial")
    ] = None
    polygons_transition_duration: Annotated[
        int, Field(serialization_alias="polygonsTransitionDuration")
    ] = 1000


class PathDatum(BaseModel, extra="allow", frozen=True):
    """Data model for a paths layer entry."""

    id: Annotated[UUID4, Field(default_factory=uuid4)] = Field(default_factory=uuid4)
    path: list[PathCoordinate]
    name: StrictStr | None = None
    label: StrictStr | None = None
    color: ColorValue | list[ColorValue] = Color("#ffffaa")
    dash_length: Annotated[PositiveFloat, Field(serialization_alias="dashLength")] = 1.0
    dash_gap: Annotated[NonNegativeFloat, Field(serialization_alias="dashGap")] = 0.0
    dash_initial_gap: Annotated[
        NonNegativeFloat, Field(serialization_alias="dashInitialGap")
    ] = 0.0
    dash_animate_time: Annotated[
        NonNegativeFloat, Field(serialization_alias="dashAnimateTime")
    ] = 0.0

    @field_serializer("color", when_used="always")
    def _serialize_color(self, value: ColorValue | list[ColorValue]) -> str | list[str]:
        return _serialize_color_list_required(value)


class PathDatumPatch(BaseModel, extra="allow", frozen=True):
    """Patch model for a paths layer entry."""

    id: UUID4
    path: list[PathCoordinate] | None = None
    name: StrictStr | None = None
    label: StrictStr | None = None
    color: ColorValue | list[ColorValue] | None = None
    dash_length: Annotated[
        PositiveFloat | None, Field(serialization_alias="dashLength")
    ] = None
    dash_gap: Annotated[
        NonNegativeFloat | None, Field(serialization_alias="dashGap")
    ] = None
    dash_initial_gap: Annotated[
        NonNegativeFloat | None, Field(serialization_alias="dashInitialGap")
    ] = None
    dash_animate_time: Annotated[
        NonNegativeFloat | None, Field(serialization_alias="dashAnimateTime")
    ] = None

    @field_serializer("color", when_used="always")
    def _serialize_color(
        self, value: ColorValue | list[ColorValue] | None
    ) -> str | list[str] | None:
        return _serialize_color_list(value)

    @model_validator(mode="after")
    def _reject_none_for_required_fields(self) -> PathDatumPatch:
        for field in (
            "path",
            "color",
            "dash_length",
            "dash_gap",
            "dash_initial_gap",
            "dash_animate_time",
        ):
            if field in self.__pydantic_fields_set__ and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be None.")
        return self


class PathsLayerConfig(BaseModel, extra="forbid", frozen=True):
    """Paths layer settings for globe.gl."""

    paths_data: Annotated[
        list[PathDatum] | None, Field(serialization_alias="pathsData")
    ] = None
    path_resolution: Annotated[
        int, Field(gt=0, serialization_alias="pathResolution")
    ] = 2
    path_stroke: Annotated[float | None, Field(serialization_alias="pathStroke")] = None
    path_transition_duration: Annotated[
        int, Field(serialization_alias="pathTransitionDuration")
    ] = 1000


class HeatmapPointDatum(BaseModel, extra="allow", frozen=True):
    """Data model for a heatmap point entry."""

    lat: Latitude
    lng: Longitude
    weight: FiniteFloat = 1.0


class HeatmapDatum(BaseModel, extra="allow", frozen=True):
    """Data model for a heatmap layer entry."""

    id: Annotated[UUID4, Field(default_factory=uuid4)] = Field(default_factory=uuid4)
    points: Annotated[list[HeatmapPointDatum], Field(min_length=1)]
    bandwidth: PositiveFloat = 2.5
    color_saturation: Annotated[
        PositiveFloat, Field(serialization_alias="colorSaturation")
    ] = 1.5
    base_altitude: Annotated[
        NonNegativeFloat, Field(serialization_alias="baseAltitude")
    ] = 0.01
    top_altitude: Annotated[
        NonNegativeFloat | None, Field(serialization_alias="topAltitude")
    ] = None


class HeatmapDatumPatch(BaseModel, extra="allow", frozen=True):
    """Patch model for a heatmap layer entry."""

    id: UUID4
    points: list[HeatmapPointDatum] | None = None
    bandwidth: PositiveFloat | None = None
    color_saturation: Annotated[
        PositiveFloat | None, Field(serialization_alias="colorSaturation")
    ] = None
    base_altitude: Annotated[
        NonNegativeFloat | None, Field(serialization_alias="baseAltitude")
    ] = None
    top_altitude: Annotated[
        NonNegativeFloat | None, Field(serialization_alias="topAltitude")
    ] = None

    @model_validator(mode="after")
    def _reject_none_for_required_fields(self) -> HeatmapDatumPatch:
        for field in ("points", "bandwidth", "color_saturation", "base_altitude"):
            if field in self.__pydantic_fields_set__ and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be None.")
        return self


class HeatmapsLayerConfig(BaseModel, extra="forbid", frozen=True):
    """Heatmaps layer settings for globe.gl."""

    heatmaps_data: Annotated[
        list[HeatmapDatum] | None, Field(serialization_alias="heatmapsData")
    ] = None
    heatmaps_transition_duration: Annotated[
        int, Field(serialization_alias="heatmapsTransitionDuration")
    ] = 0


class HexBinPointDatum(BaseModel, extra="allow", frozen=True):
    """Data model for a hex bin points layer entry."""

    id: Annotated[UUID4, Field(default_factory=uuid4)] = Field(default_factory=uuid4)
    lat: Latitude
    lng: Longitude
    weight: FiniteFloat = 1.0


class HexBinPointDatumPatch(BaseModel, extra="allow", frozen=True):
    """Patch model for a hex bin points layer entry."""

    id: UUID4
    lat: Latitude | None = None
    lng: Longitude | None = None
    weight: FiniteFloat | None = None

    @model_validator(mode="after")
    def _reject_none_for_required_fields(self) -> HexBinPointDatumPatch:
        for field in ("lat", "lng", "weight"):
            if field in self.__pydantic_fields_set__ and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be None.")
        return self


class HexBinLayerConfig(BaseModel, extra="forbid", frozen=True):
    """Hex bin layer settings for globe.gl.

    Frontend callback fields (`hex_top_color`, `hex_side_color`, `hex_altitude`,
    `hex_label`) accept ``FrontendPythonFunction`` values (or callables decorated
    with ``@frontend_python``). Those callbacks run in browser-side MicroPython
    and receive a single ``hexbin`` argument shaped like:

    ``{"h3Idx": str, "points": list[dict], "sumWeight": float}``

    Notes:
    - ``points`` are the original records from ``hex_bin_points_data`` for that bin.
    - ``sumWeight`` is the aggregate over ``hex_bin_point_weight``.
    - In practice, extra fields may be present upstream; callback code should use
      defensive access (for example, ``hexbin.get("sumWeight", 0)``).

    Expected callback returns:
    - ``hex_top_color``: CSS color string.
    - ``hex_side_color``: CSS color string.
    - ``hex_altitude``: non-negative numeric altitude in globe-radius units.
    - ``hex_label``: HTML/text string for hover tooltip content.

    Reference:
    https://github.com/vasturiano/globe.gl?tab=readme-ov-file#hex-bin-layer
    """

    hex_bin_points_data: Annotated[
        list[HexBinPointDatum] | None, Field(serialization_alias="hexBinPointsData")
    ] = None
    # Per-point latitude accessor (constant or frontend callback).
    # Callback input: a single point datum dict from hex_bin_points_data.
    # Callback output: numeric latitude in degrees.
    hex_bin_point_lat: Annotated[
        Latitude | FrontendPythonFunctionInput | None,
        Field(serialization_alias="hexBinPointLat"),
    ] = None
    # Per-point longitude accessor (constant or frontend callback).
    # Callback input: a single point datum dict from hex_bin_points_data.
    # Callback output: numeric longitude in degrees.
    hex_bin_point_lng: Annotated[
        Longitude | FrontendPythonFunctionInput | None,
        Field(serialization_alias="hexBinPointLng"),
    ] = None
    # Per-point weight accessor (constant or frontend callback).
    # Callback input: a single point datum dict from hex_bin_points_data.
    # Callback output: numeric weight for aggregation.
    hex_bin_point_weight: Annotated[
        FiniteFloat | FrontendPythonFunctionInput | None,
        Field(serialization_alias="hexBinPointWeight"),
    ] = None
    hex_bin_resolution: Annotated[
        int, Field(ge=0, le=15, serialization_alias="hexBinResolution")
    ] = 4
    hex_margin: Annotated[
        NonNegativeFloat | FrontendPythonFunctionInput,
        Field(serialization_alias="hexMargin"),
    ] = 0.2
    hex_top_curvature_resolution: Annotated[
        PositiveFloat, Field(serialization_alias="hexTopCurvatureResolution")
    ] = 5.0
    # Hex top face color accessor.
    # Callback input: a single hexbin dict (h3Idx, points, sumWeight).
    # Callback output: CSS color string.
    hex_top_color: Annotated[
        ColorValue | FrontendPythonFunctionInput,
        Field(serialization_alias="hexTopColor"),
    ] = Color("#ffffaa")
    # Hex side face color accessor.
    # Callback input: a single hexbin dict (h3Idx, points, sumWeight).
    # Callback output: CSS color string.
    hex_side_color: Annotated[
        ColorValue | FrontendPythonFunctionInput,
        Field(serialization_alias="hexSideColor"),
    ] = Color("#ffffaa")
    # Hex extrusion accessor.
    # Callback input: a single hexbin dict (h3Idx, points, sumWeight).
    # Callback output: non-negative numeric altitude in globe-radius units.
    hex_altitude: Annotated[
        NonNegativeFloat | FrontendPythonFunctionInput,
        Field(serialization_alias="hexAltitude"),
    ] = Field(default_factory=_default_hex_altitude_accessor)
    # Hex hover label accessor.
    # Callback input: a single hexbin dict (h3Idx, points, sumWeight).
    # Callback output: tooltip HTML/text string.
    hex_label: Annotated[
        StrictStr | FrontendPythonFunctionInput | None,
        Field(serialization_alias="hexLabel"),
    ] = None
    hex_bin_merge: Annotated[bool, Field(serialization_alias="hexBinMerge")] = False
    hex_transition_duration: Annotated[
        int, Field(serialization_alias="hexTransitionDuration")
    ] = 1000

    @model_validator(mode="before")
    @classmethod
    def _coerce_frontend_functions(cls, data: Any) -> Any:
        if not isinstance(data, Mapping):
            return data
        normalized = dict(data)
        for field_name in (
            "hex_bin_point_lat",
            "hex_bin_point_lng",
            "hex_bin_point_weight",
            "hex_top_color",
            "hex_side_color",
            "hex_margin",
            "hex_altitude",
            "hex_label",
        ):
            value = normalized.get(field_name)
            if callable(value) or isinstance(value, FrontendPythonFunction):
                normalized[field_name] = resolve_frontend_python_function(value)
        return normalized

    @field_serializer(
        "hex_bin_point_lat",
        "hex_bin_point_lng",
        "hex_bin_point_weight",
        when_used="always",
    )
    def _serialize_hex_point_accessors(
        self, value: Latitude | Longitude | FiniteFloat | FrontendPythonFunction | None
    ) -> float | dict[str, str] | None:
        serialized = _serialize_hexbin_accessor(value)
        if serialized is None:
            return None
        if isinstance(serialized, dict):
            return serialized
        if isinstance(serialized, (int, float)):
            return float(serialized)
        raise TypeError(
            "hex point accessor must serialize to float, function, or None."
        )

    @field_serializer("hex_margin", when_used="always")
    def _serialize_hex_margin(
        self, value: NonNegativeFloat | FrontendPythonFunction
    ) -> float | dict[str, str]:
        serialized = _serialize_hexbin_accessor(value)
        if isinstance(serialized, dict):
            return serialized
        if isinstance(serialized, (int, float)):
            return float(serialized)
        raise TypeError("hex margin accessor must serialize to float or function.")

    @field_serializer("hex_top_color", "hex_side_color", when_used="always")
    def _serialize_hex_colors(
        self, value: ColorValue | FrontendPythonFunction
    ) -> str | dict[str, str]:
        serialized = _serialize_hexbin_accessor(value)
        if isinstance(serialized, str):
            return serialized
        if isinstance(serialized, dict):
            return serialized
        raise TypeError(
            "hex color accessor must serialize to color string or function."
        )

    @field_serializer("hex_altitude", when_used="always")
    def _serialize_hex_altitude(
        self, value: NonNegativeFloat | FrontendPythonFunction
    ) -> float | dict[str, str]:
        serialized = _serialize_hexbin_accessor(value)
        if isinstance(serialized, dict):
            return serialized
        if isinstance(serialized, (int, float)):
            return float(serialized)
        raise TypeError("hex altitude accessor must serialize to float or function.")

    @field_serializer("hex_label", when_used="always")
    def _serialize_hex_label(
        self, value: StrictStr | FrontendPythonFunction | None
    ) -> str | dict[str, str] | None:
        serialized = _serialize_hexbin_accessor(value)
        if serialized is None:
            return None
        if isinstance(serialized, str):
            return serialized
        if isinstance(serialized, dict):
            return serialized
        raise TypeError("hex label accessor must serialize to string or function.")


class HexPolygonDatum(BaseModel, extra="allow", frozen=True):
    """Data model for a hexed polygon layer entry."""

    id: Annotated[UUID4, Field(default_factory=uuid4)] = Field(default_factory=uuid4)
    geometry: Polygon | MultiPolygon
    label: StrictStr | None = None
    color: ColorValue = Color("#ffffaa")
    altitude: NonNegativeFloat = 0.001
    resolution: Annotated[int, Field(ge=0, le=15)] = 3
    margin: NonNegativeFloat = 0.2
    use_dots: Annotated[bool, Field(serialization_alias="useDots")] = False
    curvature_resolution: Annotated[
        PositiveFloat, Field(serialization_alias="curvatureResolution")
    ] = 5.0
    dot_resolution: Annotated[
        PositiveFloat, Field(serialization_alias="dotResolution")
    ] = 12.0

    @field_serializer("color", when_used="always")
    def _serialize_color(self, value: ColorValue) -> str:
        return str(value)


class HexPolygonDatumPatch(BaseModel, extra="allow", frozen=True):
    """Patch model for a hexed polygon layer entry."""

    id: UUID4
    geometry: Polygon | MultiPolygon | None = None
    label: StrictStr | None = None
    color: ColorValue | None = None
    altitude: NonNegativeFloat | None = None
    resolution: Annotated[int | None, Field(ge=0, le=15)] = None
    margin: NonNegativeFloat | None = None
    use_dots: Annotated[bool | None, Field(serialization_alias="useDots")] = None
    curvature_resolution: Annotated[
        PositiveFloat | None, Field(serialization_alias="curvatureResolution")
    ] = None
    dot_resolution: Annotated[
        PositiveFloat | None, Field(serialization_alias="dotResolution")
    ] = None

    @field_serializer("color", when_used="always")
    def _serialize_color(self, value: ColorValue | None) -> str | None:
        return _serialize_color_single(value)

    @model_validator(mode="after")
    def _reject_none_for_required_fields(self) -> HexPolygonDatumPatch:
        for field in (
            "geometry",
            "color",
            "altitude",
            "resolution",
            "margin",
            "use_dots",
            "curvature_resolution",
            "dot_resolution",
        ):
            if field in self.__pydantic_fields_set__ and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be None.")
        return self


class HexedPolygonsLayerConfig(BaseModel, extra="forbid", frozen=True):
    """Hexed polygons layer settings for globe.gl."""

    hex_polygons_data: Annotated[
        list[HexPolygonDatum] | None, Field(serialization_alias="hexPolygonsData")
    ] = None
    hex_polygons_transition_duration: Annotated[
        int, Field(serialization_alias="hexPolygonsTransitionDuration")
    ] = 0


class TileDatum(BaseModel, extra="allow", frozen=True):
    """Data model for a tiles layer entry."""

    id: Annotated[UUID4, Field(default_factory=uuid4)] = Field(default_factory=uuid4)
    lat: Latitude
    lng: Longitude
    altitude: NonNegativeFloat = 0.01
    width: PositiveFloat = 1.0
    height: PositiveFloat = 1.0
    use_globe_projection: Annotated[
        bool, Field(serialization_alias="useGlobeProjection")
    ] = True
    material: Annotated[
        GlobeMaterialSpec, Field(default_factory=_default_tile_material)
    ] = Field(default_factory=_default_tile_material)
    curvature_resolution: Annotated[
        PositiveFloat, Field(serialization_alias="curvatureResolution")
    ] = 5.0
    label: StrictStr | None = None


class TileDatumPatch(BaseModel, extra="allow", frozen=True):
    """Patch model for a tiles layer entry."""

    id: UUID4
    lat: Latitude | None = None
    lng: Longitude | None = None
    altitude: NonNegativeFloat | None = None
    width: PositiveFloat | None = None
    height: PositiveFloat | None = None
    use_globe_projection: Annotated[
        bool | None, Field(serialization_alias="useGlobeProjection")
    ] = None
    material: GlobeMaterialSpec | None = None
    curvature_resolution: Annotated[
        PositiveFloat | None, Field(serialization_alias="curvatureResolution")
    ] = None
    label: StrictStr | None = None

    @model_validator(mode="after")
    def _reject_none_for_required_fields(self) -> TileDatumPatch:
        for field in (
            "lat",
            "lng",
            "altitude",
            "width",
            "height",
            "use_globe_projection",
            "material",
            "curvature_resolution",
        ):
            if field in self.__pydantic_fields_set__ and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be None.")
        return self


class TilesLayerConfig(BaseModel, extra="forbid", frozen=True):
    """Tiles layer settings for globe.gl."""

    tiles_data: Annotated[
        list[TileDatum] | None, Field(serialization_alias="tilesData")
    ] = None
    tiles_transition_duration: Annotated[
        int, Field(serialization_alias="tilesTransitionDuration")
    ] = 1000


class ParticlePointDatum(BaseModel, extra="allow", frozen=True):
    """Data model for a particles layer point entry."""

    lat: Latitude
    lng: Longitude
    altitude: NonNegativeFloat = 0.01
    label: StrictStr | None = None


class ParticleDatum(BaseModel, extra="allow", frozen=True):
    """Data model for a particles layer entry."""

    id: Annotated[UUID4, Field(default_factory=uuid4)] = Field(default_factory=uuid4)
    particles: Annotated[list[ParticlePointDatum], Field(min_length=1)]
    size: PositiveFloat = 0.5
    size_attenuation: Annotated[bool, Field(serialization_alias="sizeAttenuation")] = (
        True
    )
    color: ColorValue = Color("white")
    texture: StrictStr | None = None
    label: StrictStr | None = None

    @field_serializer("color", when_used="always")
    def _serialize_color(self, value: ColorValue) -> str:
        return str(value)


class ParticleDatumPatch(BaseModel, extra="allow", frozen=True):
    """Patch model for a particles layer entry."""

    id: UUID4
    particles: list[ParticlePointDatum] | None = None
    size: PositiveFloat | None = None
    size_attenuation: Annotated[
        bool | None, Field(serialization_alias="sizeAttenuation")
    ] = None
    color: ColorValue | None = None
    texture: StrictStr | None = None
    label: StrictStr | None = None

    @field_serializer("color", when_used="always")
    def _serialize_color(self, value: ColorValue | None) -> str | None:
        return _serialize_color_single(value)

    @model_validator(mode="after")
    def _reject_none_for_required_fields(self) -> ParticleDatumPatch:
        for field in ("particles", "size", "size_attenuation", "color"):
            if field in self.__pydantic_fields_set__ and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be None.")
        return self


class ParticlesLayerConfig(BaseModel, extra="forbid", frozen=True):
    """Particles layer settings for globe.gl."""

    particles_data: Annotated[
        list[ParticleDatum] | None, Field(serialization_alias="particlesData")
    ] = None


class RingDatum(BaseModel, extra="allow", frozen=True):
    """Data model for a rings layer entry."""

    id: Annotated[UUID4, Field(default_factory=uuid4)] = Field(default_factory=uuid4)
    lat: Latitude
    lng: Longitude
    altitude: NonNegativeFloat = 0.0015
    color: ColorValue | list[ColorValue] = Color("#ffffaa")
    max_radius: Annotated[NonNegativeFloat, Field(serialization_alias="maxRadius")] = 2
    propagation_speed: Annotated[
        FiniteFloat, Field(serialization_alias="propagationSpeed")
    ] = 1.0
    repeat_period: Annotated[
        NonNegativeFloat, Field(serialization_alias="repeatPeriod")
    ] = 700

    @field_serializer("color", when_used="always")
    def _serialize_color(self, value: ColorValue | list[ColorValue]) -> str | list[str]:
        return _serialize_color_list_required(value)


class RingDatumPatch(BaseModel, extra="allow", frozen=True):
    """Patch model for a rings layer entry."""

    id: UUID4
    lat: Latitude | None = None
    lng: Longitude | None = None
    altitude: NonNegativeFloat | None = None
    color: ColorValue | list[ColorValue] | None = None
    max_radius: Annotated[
        NonNegativeFloat | None, Field(serialization_alias="maxRadius")
    ] = None
    propagation_speed: Annotated[
        FiniteFloat | None, Field(serialization_alias="propagationSpeed")
    ] = None
    repeat_period: Annotated[
        NonNegativeFloat | None, Field(serialization_alias="repeatPeriod")
    ] = None

    @field_serializer("color", when_used="always")
    def _serialize_color(
        self, value: ColorValue | list[ColorValue] | None
    ) -> str | list[str] | None:
        return _serialize_color_list(value)

    @model_validator(mode="after")
    def _reject_none_for_required_fields(self) -> RingDatumPatch:
        for field in (
            "lat",
            "lng",
            "altitude",
            "color",
            "max_radius",
            "propagation_speed",
            "repeat_period",
        ):
            if field in self.__pydantic_fields_set__ and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be None.")
        return self


class RingsLayerConfig(BaseModel, extra="forbid", frozen=True):
    """Rings layer settings for globe.gl."""

    rings_data: Annotated[
        list[RingDatum] | None, Field(serialization_alias="ringsData")
    ] = None
    ring_resolution: Annotated[
        int, Field(gt=0, serialization_alias="ringResolution")
    ] = 64


class LabelDatum(BaseModel, extra="allow", frozen=True):
    """Data model for a labels layer entry."""

    id: Annotated[UUID4, Field(default_factory=uuid4)] = Field(default_factory=uuid4)
    lat: Latitude
    lng: Longitude
    altitude: NonNegativeFloat = 0.002
    text: StrictStr
    size: NonNegativeFloat = 0.5
    rotation: FiniteFloat = 0.0
    color: ColorValue = Color("lightgrey")
    include_dot: Annotated[bool, Field(serialization_alias="includeDot")] = True
    dot_radius: Annotated[NonNegativeFloat, Field(serialization_alias="dotRadius")] = (
        0.1
    )
    dot_orientation: Annotated[
        Literal["right", "top", "bottom"], Field(serialization_alias="dotOrientation")
    ] = "bottom"
    label: StrictStr | None = None

    @field_serializer("color", when_used="always")
    def _serialize_color(self, value: ColorValue) -> str:
        return str(value)


class LabelDatumPatch(BaseModel, extra="allow", frozen=True):
    """Patch model for a labels layer entry."""

    id: UUID4
    lat: Latitude | None = None
    lng: Longitude | None = None
    altitude: NonNegativeFloat | None = None
    text: StrictStr | None = None
    size: NonNegativeFloat | None = None
    rotation: FiniteFloat | None = None
    color: ColorValue | None = None
    include_dot: Annotated[bool | None, Field(serialization_alias="includeDot")] = None
    dot_radius: Annotated[
        NonNegativeFloat | None, Field(serialization_alias="dotRadius")
    ] = None
    dot_orientation: Annotated[
        Literal["right", "top", "bottom"] | None,
        Field(serialization_alias="dotOrientation"),
    ] = None
    label: StrictStr | None = None

    @field_serializer("color", when_used="always")
    def _serialize_color(self, value: ColorValue | None) -> str | None:
        return _serialize_color_single(value)

    @model_validator(mode="after")
    def _reject_none_for_required_fields(self) -> LabelDatumPatch:
        for field in (
            "lat",
            "lng",
            "altitude",
            "text",
            "size",
            "rotation",
            "color",
            "include_dot",
            "dot_radius",
            "dot_orientation",
        ):
            if field in self.__pydantic_fields_set__ and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be None.")
        return self


class LabelsLayerConfig(BaseModel, extra="forbid", frozen=True):
    """Labels layer settings for globe.gl."""

    labels_data: Annotated[
        list[LabelDatum] | None, Field(serialization_alias="labelsData")
    ] = None
    label_type_face: Annotated[
        dict[str, Any] | None, Field(serialization_alias="labelTypeFace")
    ] = None
    label_resolution: Annotated[
        int, Field(gt=0, serialization_alias="labelResolution")
    ] = 3
    labels_transition_duration: Annotated[
        int, Field(serialization_alias="labelsTransitionDuration")
    ] = 1000


class PointOfView(BaseModel, extra="forbid", frozen=True):
    """Point-of-view parameters for the globe camera."""

    lat: Latitude
    lng: Longitude
    altitude: FiniteFloat


class GlobeViewConfig(BaseModel, extra="forbid", frozen=True):
    """View configuration for globe.gl camera."""

    point_of_view: Annotated[
        PointOfView | None, Field(serialization_alias="pointOfView")
    ] = None
    transition_ms: Annotated[int | None, Field(serialization_alias="transitionMs")] = (
        None
    )
    controls_auto_rotate: Annotated[
        bool | None, Field(serialization_alias="controlsAutoRotate")
    ] = None
    controls_auto_rotate_speed: Annotated[
        FiniteFloat | None, Field(serialization_alias="controlsAutoRotateSpeed")
    ] = None


class GlobeConfig(BaseModel, extra="forbid", frozen=True):
    """Top-level configuration container for GlobeWidget."""

    init: Annotated[GlobeInitConfig, Field(default_factory=GlobeInitConfig)] = Field(
        default_factory=GlobeInitConfig
    )
    layout: Annotated[GlobeLayoutConfig, Field(default_factory=GlobeLayoutConfig)] = (
        Field(default_factory=GlobeLayoutConfig)
    )
    globe: Annotated[GlobeLayerConfig, Field(default_factory=GlobeLayerConfig)] = Field(
        default_factory=GlobeLayerConfig
    )
    points: Annotated[PointsLayerConfig, Field(default_factory=PointsLayerConfig)] = (
        Field(default_factory=PointsLayerConfig)
    )
    arcs: Annotated[ArcsLayerConfig, Field(default_factory=ArcsLayerConfig)] = Field(
        default_factory=ArcsLayerConfig
    )
    polygons: Annotated[
        PolygonsLayerConfig, Field(default_factory=PolygonsLayerConfig)
    ] = Field(default_factory=PolygonsLayerConfig)
    paths: Annotated[PathsLayerConfig, Field(default_factory=PathsLayerConfig)] = Field(
        default_factory=PathsLayerConfig
    )
    heatmaps: Annotated[
        HeatmapsLayerConfig, Field(default_factory=HeatmapsLayerConfig)
    ] = Field(default_factory=HeatmapsLayerConfig)
    hex_bin: Annotated[HexBinLayerConfig, Field(default_factory=HexBinLayerConfig)] = (
        Field(default_factory=HexBinLayerConfig)
    )
    hexed_polygons: Annotated[
        HexedPolygonsLayerConfig, Field(default_factory=HexedPolygonsLayerConfig)
    ] = Field(default_factory=HexedPolygonsLayerConfig)
    tiles: Annotated[TilesLayerConfig, Field(default_factory=TilesLayerConfig)] = Field(
        default_factory=TilesLayerConfig
    )
    particles: Annotated[
        ParticlesLayerConfig, Field(default_factory=ParticlesLayerConfig)
    ] = Field(default_factory=ParticlesLayerConfig)
    rings: Annotated[RingsLayerConfig, Field(default_factory=RingsLayerConfig)] = Field(
        default_factory=RingsLayerConfig
    )
    labels: Annotated[LabelsLayerConfig, Field(default_factory=LabelsLayerConfig)] = (
        Field(default_factory=LabelsLayerConfig)
    )
    view: Annotated[GlobeViewConfig, Field(default_factory=GlobeViewConfig)] = Field(
        default_factory=GlobeViewConfig
    )
