from __future__ import annotations

from collections.abc import Mapping

from pydantic import AnyUrl, BaseModel, ConfigDict, Field, field_serializer, PositiveInt


class GlobeInitConfig(BaseModel):
    """Initialization settings for globe.gl."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    renderer_config: Mapping[str, object] | None = Field(
        default=None, serialization_alias="rendererConfig"
    )
    wait_for_globe_ready: bool = Field(
        default=True, serialization_alias="waitForGlobeReady"
    )
    animate_in: bool = Field(default=True, serialization_alias="animateIn")


class GlobeLayoutConfig(BaseModel):
    """Layout settings for globe.gl rendering."""

    model_config = ConfigDict(extra="forbid", frozen=True)

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


class GlobeLayerConfig(BaseModel):
    """Globe layer settings for globe.gl."""

    model_config = ConfigDict(extra="forbid", frozen=True)

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
    globe_material: object | None = Field(
        default=None, serialization_alias="globeMaterial"
    )

    @field_serializer("globe_image_url", "bump_image_url", when_used="always")
    def _serialize_globe_images(self, value: AnyUrl | None) -> str | None:
        return str(value) if value is not None else None


class PointOfView(BaseModel):
    """Point-of-view parameters for the globe camera."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    lat: float
    lng: float
    altitude: float


class GlobeViewConfig(BaseModel):
    """View configuration for globe.gl camera."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    point_of_view: PointOfView | None = Field(
        default=None, serialization_alias="pointOfView"
    )
    transition_ms: int | None = Field(default=None, serialization_alias="transitionMs")


class GlobeConfig(BaseModel):
    """Top-level configuration container for GlobeWidget."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    init: GlobeInitConfig = Field(default_factory=GlobeInitConfig)
    layout: GlobeLayoutConfig = Field(default_factory=GlobeLayoutConfig)
    globe: GlobeLayerConfig = Field(default_factory=GlobeLayerConfig)
    view: GlobeViewConfig = Field(default_factory=GlobeViewConfig)
