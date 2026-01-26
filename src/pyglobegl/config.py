from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import uuid4

from geojson_pydantic import MultiPolygon, Polygon
from pydantic import AnyUrl, BaseModel, Field, field_serializer, PositiveInt, UUID4


class GlobeInitConfig(BaseModel, extra="forbid", frozen=True):
    """Initialization settings for globe.gl."""

    renderer_config: Mapping[str, Any] | None = Field(
        default=None, serialization_alias="rendererConfig"
    )
    wait_for_globe_ready: bool = Field(
        default=True, serialization_alias="waitForGlobeReady"
    )
    animate_in: bool = Field(default=True, serialization_alias="animateIn")


class GlobeLayoutConfig(BaseModel, extra="forbid", frozen=True):
    """Layout settings for globe.gl rendering."""

    width: PositiveInt | None = None
    height: PositiveInt | None = None
    globe_offset: tuple[float, float] | None = Field(
        default=None, serialization_alias="globeOffset"
    )
    background_color: str | None = Field(
        default=None, serialization_alias="backgroundColor"
    )
    background_image_url: AnyUrl | None = Field(
        default=None, serialization_alias="backgroundImageUrl"
    )

    @field_serializer("background_image_url", when_used="always")
    def _serialize_background_image(self, value: AnyUrl | None) -> str | None:
        return str(value) if value is not None else None


class GlobeMaterialSpec(BaseModel, extra="forbid", frozen=True):
    """Specification for constructing a ThreeJS material in the frontend."""

    type: str
    params: dict[str, Any] = Field(default_factory=dict)


class GlobeLayerConfig(BaseModel, extra="forbid", frozen=True):
    """Globe layer settings for globe.gl."""

    globe_image_url: AnyUrl | None = Field(
        default=None, serialization_alias="globeImageUrl"
    )
    bump_image_url: AnyUrl | None = Field(
        default=None, serialization_alias="bumpImageUrl"
    )
    globe_tile_engine_url: str | None = Field(
        default=None, serialization_alias="globeTileEngineUrl"
    )
    show_globe: bool = Field(default=True, serialization_alias="showGlobe")
    show_graticules: bool = Field(default=False, serialization_alias="showGraticules")
    show_atmosphere: bool = Field(default=True, serialization_alias="showAtmosphere")
    atmosphere_color: str | None = Field(
        default=None, serialization_alias="atmosphereColor"
    )
    atmosphere_altitude: float | None = Field(
        default=None, serialization_alias="atmosphereAltitude"
    )
    globe_curvature_resolution: float | None = Field(
        default=None, serialization_alias="globeCurvatureResolution"
    )
    globe_material: GlobeMaterialSpec | dict[str, Any] | None = Field(
        default=None, serialization_alias="globeMaterial"
    )

    @field_serializer("globe_image_url", "bump_image_url", when_used="always")
    def _serialize_globe_images(self, value: AnyUrl | None) -> str | None:
        return str(value) if value is not None else None


class PointDatum(BaseModel, extra="allow", frozen=True):
    """Data model for a points layer entry."""

    id: UUID4 = Field(default_factory=uuid4)
    lat: float
    lng: float
    altitude: float | None = None
    radius: float | None = None
    color: str | list[str] | None = None
    label: str | None = None
    size: float | None = None


class PointDatumPatch(BaseModel, extra="allow", frozen=True):
    """Patch model for a points layer entry."""

    id: UUID4
    lat: float | None = None
    lng: float | None = None
    altitude: float | None = None
    radius: float | None = None
    color: str | list[str] | None = None
    label: str | None = None
    size: float | None = None


class PointsLayerConfig(BaseModel, extra="forbid", frozen=True):
    """Points layer settings for globe.gl."""

    points_data: list[PointDatum] | list[dict[str, Any]] | None = Field(
        default=None, serialization_alias="pointsData"
    )
    point_label: str | None = Field(default=None, serialization_alias="pointLabel")
    point_lat: float | str | None = Field(default=None, serialization_alias="pointLat")
    point_lng: float | str | None = Field(default=None, serialization_alias="pointLng")
    point_color: str | None = Field(default=None, serialization_alias="pointColor")
    point_altitude: float | str | None = Field(
        default=None, serialization_alias="pointAltitude"
    )
    point_radius: float | str | None = Field(
        default=None, serialization_alias="pointRadius"
    )
    point_resolution: int | None = Field(
        default=None, serialization_alias="pointResolution"
    )
    points_merge: bool | None = Field(default=None, serialization_alias="pointsMerge")
    points_transition_duration: int | None = Field(
        default=None, serialization_alias="pointsTransitionDuration"
    )


class ArcDatum(BaseModel, extra="allow", frozen=True):
    """Data model for an arcs layer entry."""

    id: UUID4 = Field(default_factory=uuid4)
    start_lat: float = Field(serialization_alias="startLat")
    start_lng: float = Field(serialization_alias="startLng")
    end_lat: float = Field(serialization_alias="endLat")
    end_lng: float = Field(serialization_alias="endLng")
    start_altitude: float | None = Field(
        default=None, serialization_alias="startAltitude"
    )
    end_altitude: float | None = Field(default=None, serialization_alias="endAltitude")
    altitude: float | None = Field(default=None, serialization_alias="altitude")
    altitude_auto_scale: float | None = Field(
        default=None, serialization_alias="altitudeAutoScale"
    )
    stroke: float | None = Field(default=None, serialization_alias="stroke")
    dash_length: float | None = Field(default=None, serialization_alias="dashLength")
    dash_gap: float | None = Field(default=None, serialization_alias="dashGap")
    dash_initial_gap: float | None = Field(
        default=None, serialization_alias="dashInitialGap"
    )
    dash_animate_time: float | None = Field(
        default=None, serialization_alias="dashAnimateTime"
    )
    color: str | list[str] | None = None
    label: str | None = None


class ArcDatumPatch(BaseModel, extra="allow", frozen=True):
    """Patch model for an arcs layer entry."""

    id: UUID4
    start_lat: float | None = Field(default=None, serialization_alias="startLat")
    start_lng: float | None = Field(default=None, serialization_alias="startLng")
    end_lat: float | None = Field(default=None, serialization_alias="endLat")
    end_lng: float | None = Field(default=None, serialization_alias="endLng")
    start_altitude: float | None = Field(
        default=None, serialization_alias="startAltitude"
    )
    end_altitude: float | None = Field(default=None, serialization_alias="endAltitude")
    altitude: float | None = Field(default=None, serialization_alias="altitude")
    altitude_auto_scale: float | None = Field(
        default=None, serialization_alias="altitudeAutoScale"
    )
    stroke: float | None = Field(default=None, serialization_alias="stroke")
    dash_length: float | None = Field(default=None, serialization_alias="dashLength")
    dash_gap: float | None = Field(default=None, serialization_alias="dashGap")
    dash_initial_gap: float | None = Field(
        default=None, serialization_alias="dashInitialGap"
    )
    dash_animate_time: float | None = Field(
        default=None, serialization_alias="dashAnimateTime"
    )
    color: str | list[str] | None = None
    label: str | None = None


class ArcsLayerConfig(BaseModel, extra="forbid", frozen=True):
    """Arcs layer settings for globe.gl."""

    arcs_data: list[ArcDatum] | list[dict[str, Any]] | None = Field(
        default=None, serialization_alias="arcsData"
    )
    arc_label: str | None = Field(default=None, serialization_alias="arcLabel")
    arc_start_lat: float | str | None = Field(
        default=None, serialization_alias="arcStartLat"
    )
    arc_start_lng: float | str | None = Field(
        default=None, serialization_alias="arcStartLng"
    )
    arc_start_altitude: float | str | None = Field(
        default=None, serialization_alias="arcStartAltitude"
    )
    arc_end_lat: float | str | None = Field(
        default=None, serialization_alias="arcEndLat"
    )
    arc_end_lng: float | str | None = Field(
        default=None, serialization_alias="arcEndLng"
    )
    arc_end_altitude: float | str | None = Field(
        default=None, serialization_alias="arcEndAltitude"
    )
    arc_color: str | list[str] | None = Field(
        default=None, serialization_alias="arcColor"
    )
    arc_altitude: float | str | None = Field(
        default=None, serialization_alias="arcAltitude"
    )
    arc_altitude_auto_scale: float | str | None = Field(
        default=None, serialization_alias="arcAltitudeAutoScale"
    )
    arc_stroke: float | str | None = Field(
        default=None, serialization_alias="arcStroke"
    )
    arc_curve_resolution: int | None = Field(
        default=None, serialization_alias="arcCurveResolution"
    )
    arc_circular_resolution: int | None = Field(
        default=None, serialization_alias="arcCircularResolution"
    )
    arc_dash_length: float | str | None = Field(
        default=None, serialization_alias="arcDashLength"
    )
    arc_dash_gap: float | str | None = Field(
        default=None, serialization_alias="arcDashGap"
    )
    arc_dash_initial_gap: float | str | None = Field(
        default=None, serialization_alias="arcDashInitialGap"
    )
    arc_dash_animate_time: float | str | None = Field(
        default=None, serialization_alias="arcDashAnimateTime"
    )
    arcs_transition_duration: int | None = Field(
        default=None, serialization_alias="arcsTransitionDuration"
    )


class PolygonDatum(BaseModel, extra="allow", frozen=True):
    """Data model for a polygons layer entry."""

    id: UUID4 = Field(default_factory=uuid4)
    geometry: Polygon | MultiPolygon
    name: str | None = None
    label: str | None = None
    cap_color: str | None = None
    side_color: str | None = None
    stroke_color: str | None = None
    altitude: float | None = None
    cap_curvature_resolution: float | None = None


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


class PolygonsLayerConfig(BaseModel, extra="forbid", frozen=True):
    """Polygons layer settings for globe.gl."""

    polygons_data: list[PolygonDatum] | list[dict[str, Any]] | None = Field(
        default=None, serialization_alias="polygonsData"
    )
    polygon_label: str | None = Field(default=None, serialization_alias="polygonLabel")
    polygon_geojson_geometry: str | None = Field(
        default=None, serialization_alias="polygonGeoJsonGeometry"
    )
    polygon_cap_color: str | None = Field(
        default=None, serialization_alias="polygonCapColor"
    )
    polygon_cap_material: GlobeMaterialSpec | dict[str, Any] | None = Field(
        default=None, serialization_alias="polygonCapMaterial"
    )
    polygon_side_color: str | None = Field(
        default=None, serialization_alias="polygonSideColor"
    )
    polygon_side_material: GlobeMaterialSpec | dict[str, Any] | None = Field(
        default=None, serialization_alias="polygonSideMaterial"
    )
    polygon_stroke_color: str | None = Field(
        default=None, serialization_alias="polygonStrokeColor"
    )
    polygon_altitude: float | str | None = Field(
        default=None, serialization_alias="polygonAltitude"
    )
    polygon_cap_curvature_resolution: float | str | None = Field(
        default=None, serialization_alias="polygonCapCurvatureResolution"
    )
    polygons_transition_duration: int | None = Field(
        default=None, serialization_alias="polygonsTransitionDuration"
    )


class PointOfView(BaseModel, extra="forbid", frozen=True):
    """Point-of-view parameters for the globe camera."""

    lat: float
    lng: float
    altitude: float


class GlobeViewConfig(BaseModel, extra="forbid", frozen=True):
    """View configuration for globe.gl camera."""

    point_of_view: PointOfView | None = Field(
        default=None, serialization_alias="pointOfView"
    )
    transition_ms: int | None = Field(default=None, serialization_alias="transitionMs")


class GlobeConfig(BaseModel, extra="forbid", frozen=True):
    """Top-level configuration container for GlobeWidget."""

    init: GlobeInitConfig = Field(default_factory=GlobeInitConfig)
    layout: GlobeLayoutConfig = Field(default_factory=GlobeLayoutConfig)
    globe: GlobeLayerConfig = Field(default_factory=GlobeLayerConfig)
    points: PointsLayerConfig = Field(default_factory=PointsLayerConfig)
    arcs: ArcsLayerConfig = Field(default_factory=ArcsLayerConfig)
    polygons: PolygonsLayerConfig = Field(default_factory=PolygonsLayerConfig)
    view: GlobeViewConfig = Field(default_factory=GlobeViewConfig)
