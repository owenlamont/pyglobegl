from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Any
from uuid import uuid4

from geojson_pydantic import MultiPolygon, Polygon
from pydantic import AnyUrl, BaseModel, Field, field_serializer, model_validator, UUID4


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
    lat: float
    lng: float
    altitude: float = 0.1
    radius: float = 0.25
    color: str = "#ffffaa"
    label: str | None = None


class PointDatumPatch(BaseModel, extra="allow", frozen=True):
    """Patch model for a points layer entry."""

    id: UUID4
    lat: float | None = None
    lng: float | None = None
    altitude: float | None = None
    radius: float | None = None
    color: str | None = None
    label: str | None = None

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
    start_lat: Annotated[float, Field(serialization_alias="startLat")]
    start_lng: Annotated[float, Field(serialization_alias="startLng")]
    end_lat: Annotated[float, Field(serialization_alias="endLat")]
    end_lng: Annotated[float, Field(serialization_alias="endLng")]
    start_altitude: Annotated[
        float, Field(default=0.0, serialization_alias="startAltitude")
    ] = 0.0
    end_altitude: Annotated[
        float, Field(default=0.0, serialization_alias="endAltitude")
    ] = 0.0
    altitude: Annotated[float | None, Field(serialization_alias="altitude")] = None
    altitude_auto_scale: Annotated[
        float, Field(serialization_alias="altitudeAutoScale")
    ] = 0.5
    stroke: Annotated[float | None, Field(serialization_alias="stroke")] = None
    dash_length: Annotated[float, Field(serialization_alias="dashLength")] = 1.0
    dash_gap: Annotated[float, Field(serialization_alias="dashGap")] = 0.0
    dash_initial_gap: Annotated[float, Field(serialization_alias="dashInitialGap")] = (
        0.0
    )
    dash_animate_time: Annotated[
        float, Field(serialization_alias="dashAnimateTime")
    ] = 0.0
    color: str | list[str] = "#ffffaa"
    label: str | None = None


class ArcDatumPatch(BaseModel, extra="allow", frozen=True):
    """Patch model for an arcs layer entry."""

    id: UUID4
    start_lat: Annotated[float | None, Field(serialization_alias="startLat")] = None
    start_lng: Annotated[float | None, Field(serialization_alias="startLng")] = None
    end_lat: Annotated[float | None, Field(serialization_alias="endLat")] = None
    end_lng: Annotated[float | None, Field(serialization_alias="endLng")] = None
    start_altitude: Annotated[
        float | None, Field(serialization_alias="startAltitude")
    ] = None
    end_altitude: Annotated[float | None, Field(serialization_alias="endAltitude")] = (
        None
    )
    altitude: Annotated[float | None, Field(serialization_alias="altitude")] = None
    altitude_auto_scale: Annotated[
        float | None, Field(serialization_alias="altitudeAutoScale")
    ] = None
    stroke: Annotated[float | None, Field(serialization_alias="stroke")] = None
    dash_length: Annotated[float | None, Field(serialization_alias="dashLength")] = None
    dash_gap: Annotated[float | None, Field(serialization_alias="dashGap")] = None
    dash_initial_gap: Annotated[
        float | None, Field(serialization_alias="dashInitialGap")
    ] = None
    dash_animate_time: Annotated[
        float | None, Field(serialization_alias="dashAnimateTime")
    ] = None
    color: str | list[str] | None = None
    label: str | None = None

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
    name: str | None = None
    label: str | None = None
    cap_color: str = "#ffffaa"
    side_color: str = "#ffffaa"
    stroke_color: str | None = None
    altitude: float = 0.01
    cap_curvature_resolution: float = 5.0


class PolygonDatumPatch(BaseModel, extra="allow", frozen=True):
    """Patch model for a polygons layer entry."""

    id: UUID4
    geometry: Polygon | MultiPolygon | None = None
    name: str | None = None
    label: str | None = None
    cap_color: str | None = None
    side_color: str | None = None
    stroke_color: str | None = None
    altitude: float | None = None
    cap_curvature_resolution: float | None = None

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


class PointOfView(BaseModel, extra="forbid", frozen=True):
    """Point-of-view parameters for the globe camera."""

    lat: float
    lng: float
    altitude: float


class GlobeViewConfig(BaseModel, extra="forbid", frozen=True):
    """View configuration for globe.gl camera."""

    point_of_view: Annotated[
        PointOfView | None, Field(serialization_alias="pointOfView")
    ] = None
    transition_ms: Annotated[int | None, Field(serialization_alias="transitionMs")] = (
        None
    )


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
    view: Annotated[GlobeViewConfig, Field(default_factory=GlobeViewConfig)] = Field(
        default_factory=GlobeViewConfig
    )
