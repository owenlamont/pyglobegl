from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import AnyUrl, BaseModel, Field, field_serializer, PositiveInt


class GlobeInitConfig(BaseModel, extra="forbid", frozen=True):
    """Initialization settings for globe.gl."""

    renderer_config: Mapping[str, object] | None = Field(
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
    show_globe: bool | None = Field(default=None, serialization_alias="showGlobe")
    show_graticules: bool | None = Field(
        default=None, serialization_alias="showGraticules"
    )
    show_atmosphere: bool | None = Field(
        default=None, serialization_alias="showAtmosphere"
    )
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

    lat: float
    lng: float
    altitude: float | None = None
    radius: float | None = None
    color: str | None = None
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
    view: GlobeViewConfig = Field(default_factory=GlobeViewConfig)
