from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field, PositiveInt


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
    background_image_url: str | None = Field(
        default=None, serialization_alias="backgroundImageUrl"
    )


class GlobeConfig(BaseModel):
    """Top-level configuration container for GlobeWidget."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    init: GlobeInitConfig = Field(default_factory=GlobeInitConfig)
    layout: GlobeLayoutConfig = Field(default_factory=GlobeLayoutConfig)
