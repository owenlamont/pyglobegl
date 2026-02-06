from collections.abc import Callable, Sequence
import copy
from pathlib import Path
from typing import Any, TypeVar
from uuid import uuid4

import anywidget
from ipywidgets import Layout
from pydantic import BaseModel, UUID4
import traitlets

from pyglobegl.config import (
    ArcDatum,
    ArcDatumPatch,
    GlobeConfig,
    GlobeMaterialSpec,
    HeatmapDatum,
    HeatmapDatumPatch,
    HexPolygonDatum,
    HexPolygonDatumPatch,
    LabelDatum,
    LabelDatumPatch,
    ParticleDatum,
    ParticleDatumPatch,
    ParticlesLayerConfig,
    PathDatum,
    PathDatumPatch,
    PointDatum,
    PointDatumPatch,
    PolygonDatum,
    PolygonDatumPatch,
    RingDatum,
    RingDatumPatch,
    TileDatum,
    TileDatumPatch,
)


ModelT = TypeVar("ModelT", bound=BaseModel)


def _model_alias_map(model: type[BaseModel]) -> dict[str, str]:
    alias_map: dict[str, str] = {}
    for field_name, field in model.model_fields.items():
        alias = field.serialization_alias
        if isinstance(alias, str):
            alias_map[alias] = field_name
    return alias_map


class GlobeWidget(anywidget.AnyWidget):
    """AnyWidget wrapper around globe.gl."""

    _esm = Path(__file__).with_name("_static") / "index.js"
    config = traitlets.Dict().tag(sync=True)
    event_config = traitlets.Dict().tag(sync=True)

    def __init__(
        self,
        config: GlobeConfig | None = None,
        layout: Layout | None = None,
        **kwargs: Any,
    ) -> None:
        if layout is None:
            layout = Layout(width="100%", height="auto")
        if config is None:
            config = GlobeConfig()
        if not isinstance(config, GlobeConfig):
            raise TypeError("config must be a GlobeConfig instance.")
        kwargs.setdefault("layout", layout)
        super().__init__(**kwargs)
        self._globe_ready_handlers: list[Callable[[], None]] = []
        self._globe_click_handlers: list[Callable[[dict[str, float]], None]] = []
        self._globe_right_click_handlers: list[Callable[[dict[str, float]], None]] = []
        self._point_click_handlers: list[
            Callable[[dict[str, Any], dict[str, float]], None]
        ] = []
        self._point_right_click_handlers: list[
            Callable[[dict[str, Any], dict[str, float]], None]
        ] = []
        self._point_hover_handlers: list[
            Callable[[dict[str, Any] | None, dict[str, Any] | None], None]
        ] = []
        self._arc_click_handlers: list[
            Callable[[dict[str, Any], dict[str, float]], None]
        ] = []
        self._arc_right_click_handlers: list[
            Callable[[dict[str, Any], dict[str, float]], None]
        ] = []
        self._arc_hover_handlers: list[
            Callable[[dict[str, Any] | None, dict[str, Any] | None], None]
        ] = []
        self._polygon_click_handlers: list[
            Callable[[dict[str, Any], dict[str, float]], None]
        ] = []
        self._polygon_right_click_handlers: list[
            Callable[[dict[str, Any], dict[str, float]], None]
        ] = []
        self._polygon_hover_handlers: list[
            Callable[[dict[str, Any] | None, dict[str, Any] | None], None]
        ] = []
        self._path_click_handlers: list[
            Callable[[dict[str, Any], dict[str, float]], None]
        ] = []
        self._path_right_click_handlers: list[
            Callable[[dict[str, Any], dict[str, float]], None]
        ] = []
        self._path_hover_handlers: list[
            Callable[[dict[str, Any] | None, dict[str, Any] | None], None]
        ] = []
        self._heatmap_click_handlers: list[
            Callable[[dict[str, Any], dict[str, float]], None]
        ] = []
        self._heatmap_right_click_handlers: list[
            Callable[[dict[str, Any], dict[str, float]], None]
        ] = []
        self._heatmap_hover_handlers: list[
            Callable[[dict[str, Any] | None, dict[str, Any] | None], None]
        ] = []
        self._hex_polygon_click_handlers: list[
            Callable[[dict[str, Any], dict[str, float]], None]
        ] = []
        self._hex_polygon_right_click_handlers: list[
            Callable[[dict[str, Any], dict[str, float]], None]
        ] = []
        self._hex_polygon_hover_handlers: list[
            Callable[[dict[str, Any] | None, dict[str, Any] | None], None]
        ] = []
        self._tile_click_handlers: list[
            Callable[[dict[str, Any], dict[str, float]], None]
        ] = []
        self._tile_right_click_handlers: list[
            Callable[[dict[str, Any], dict[str, float]], None]
        ] = []
        self._tile_hover_handlers: list[
            Callable[[dict[str, Any] | None, dict[str, Any] | None], None]
        ] = []
        self._particle_click_handlers: list[
            Callable[[dict[str, Any], dict[str, float]], None]
        ] = []
        self._particle_right_click_handlers: list[
            Callable[[dict[str, Any], dict[str, float]], None]
        ] = []
        self._particle_hover_handlers: list[
            Callable[[dict[str, Any] | None, dict[str, Any] | None], None]
        ] = []
        self._label_click_handlers: list[
            Callable[[dict[str, Any], dict[str, float]], None]
        ] = []
        self._label_right_click_handlers: list[
            Callable[[dict[str, Any], dict[str, float]], None]
        ] = []
        self._label_hover_handlers: list[
            Callable[[dict[str, Any] | None, dict[str, Any] | None], None]
        ] = []
        self._message_handlers: dict[str, Callable[[Any], None]] = {
            "globe_ready": lambda _payload: self._dispatch_globe_ready(),
            "globe_click": self._dispatch_globe_click,
            "globe_right_click": self._dispatch_globe_right_click,
            "point_click": self._dispatch_point_click,
            "point_right_click": self._dispatch_point_right_click,
            "point_hover": self._dispatch_point_hover,
            "arc_click": self._dispatch_arc_click,
            "arc_right_click": self._dispatch_arc_right_click,
            "arc_hover": self._dispatch_arc_hover,
            "polygon_click": self._dispatch_polygon_click,
            "polygon_right_click": self._dispatch_polygon_right_click,
            "polygon_hover": self._dispatch_polygon_hover,
            "path_click": self._dispatch_path_click,
            "path_right_click": self._dispatch_path_right_click,
            "path_hover": self._dispatch_path_hover,
            "heatmap_click": self._dispatch_heatmap_click,
            "heatmap_right_click": self._dispatch_heatmap_right_click,
            "heatmap_hover": self._dispatch_heatmap_hover,
            "hex_polygon_click": self._dispatch_hex_polygon_click,
            "hex_polygon_right_click": self._dispatch_hex_polygon_right_click,
            "hex_polygon_hover": self._dispatch_hex_polygon_hover,
            "tile_click": self._dispatch_tile_click,
            "tile_right_click": self._dispatch_tile_right_click,
            "tile_hover": self._dispatch_tile_hover,
            "particle_click": self._dispatch_particle_click,
            "particle_right_click": self._dispatch_particle_right_click,
            "particle_hover": self._dispatch_particle_hover,
            "label_click": self._dispatch_label_click,
            "label_right_click": self._dispatch_label_right_click,
            "label_hover": self._dispatch_label_hover,
        }
        self.on_msg(self._handle_frontend_message)
        self.event_config = {}
        self._points_data = self._normalize_layer_data(config.points.points_data)
        self._arcs_data = self._normalize_layer_data(config.arcs.arcs_data)
        self._polygons_data = self._normalize_layer_data(config.polygons.polygons_data)
        self._paths_data = self._normalize_layer_data(config.paths.paths_data)
        self._heatmaps_data = self._normalize_layer_data(config.heatmaps.heatmaps_data)
        self._hex_polygons_data = self._normalize_layer_data(
            config.hexed_polygons.hex_polygons_data
        )
        self._tiles_data = self._normalize_tile_data(config.tiles.tiles_data)
        self._particles_data = self._normalize_layer_data(
            config.particles.particles_data
        )
        self._rings_data = self._normalize_layer_data(config.rings.rings_data)
        self._labels_data = self._normalize_layer_data(config.labels.labels_data)
        self._globe_props = config.globe.model_dump(
            by_alias=True, exclude_none=True, exclude_unset=False, mode="json"
        )
        self._points_props = config.points.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude_unset=True,
            exclude={"points_data"},
            mode="json",
        )
        self._points_props.update(
            {
                "pointLat": "lat",
                "pointLng": "lng",
                "pointAltitude": "altitude",
                "pointRadius": "radius",
                "pointColor": "color",
                "pointLabel": "label",
            }
        )
        self._arcs_props = config.arcs.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude_unset=True,
            exclude={"arcs_data"},
            mode="json",
        )
        self._arcs_props.update(
            {
                "arcStartLat": "startLat",
                "arcStartLng": "startLng",
                "arcEndLat": "endLat",
                "arcEndLng": "endLng",
                "arcStartAltitude": "startAltitude",
                "arcEndAltitude": "endAltitude",
                "arcAltitude": "altitude",
                "arcAltitudeAutoScale": "altitudeAutoScale",
                "arcStroke": "stroke",
                "arcDashLength": "dashLength",
                "arcDashGap": "dashGap",
                "arcDashInitialGap": "dashInitialGap",
                "arcDashAnimateTime": "dashAnimateTime",
                "arcColor": "color",
                "arcLabel": "label",
            }
        )
        self._polygons_props = config.polygons.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude_unset=True,
            exclude={"polygons_data"},
            mode="json",
        )
        self._polygons_props.update(
            {
                "polygonGeoJsonGeometry": "geometry",
                "polygonCapColor": "cap_color",
                "polygonSideColor": "side_color",
                "polygonStrokeColor": "stroke_color",
                "polygonAltitude": "altitude",
                "polygonCapCurvatureResolution": "cap_curvature_resolution",
                "polygonLabel": "label",
            }
        )
        self._paths_props = config.paths.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude_unset=True,
            exclude={"paths_data"},
            mode="json",
        )
        self._paths_props.update(
            {
                "pathColor": "color",
                "pathDashLength": "dashLength",
                "pathDashGap": "dashGap",
                "pathDashInitialGap": "dashInitialGap",
                "pathDashAnimateTime": "dashAnimateTime",
                "pathLabel": "label",
            }
        )
        self._heatmaps_props = config.heatmaps.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude_unset=True,
            exclude={"heatmaps_data"},
            mode="json",
        )
        self._heatmaps_props.update(
            {
                "heatmapPoints": "points",
                "heatmapPointLat": "lat",
                "heatmapPointLng": "lng",
                "heatmapPointWeight": "weight",
                "heatmapBandwidth": "bandwidth",
                "heatmapColorSaturation": "colorSaturation",
                "heatmapBaseAltitude": "baseAltitude",
                "heatmapTopAltitude": "topAltitude",
            }
        )
        self._hex_polygons_props = config.hexed_polygons.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude_unset=True,
            exclude={"hex_polygons_data"},
            mode="json",
        )
        self._hex_polygons_props.update(
            {
                "hexPolygonGeoJsonGeometry": "geometry",
                "hexPolygonColor": "color",
                "hexPolygonAltitude": "altitude",
                "hexPolygonResolution": "resolution",
                "hexPolygonMargin": "margin",
                "hexPolygonUseDots": "useDots",
                "hexPolygonCurvatureResolution": "curvatureResolution",
                "hexPolygonDotResolution": "dotResolution",
                "hexPolygonLabel": "label",
            }
        )
        self._tiles_props = config.tiles.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude_unset=True,
            exclude={"tiles_data"},
            mode="json",
        )
        self._tiles_props.update(
            {
                "tileLat": "lat",
                "tileLng": "lng",
                "tileAltitude": "altitude",
                "tileWidth": "width",
                "tileHeight": "height",
                "tileUseGlobeProjection": "useGlobeProjection",
                "tileMaterial": "material",
                "tileCurvatureResolution": "curvatureResolution",
                "tileLabel": "label",
            }
        )
        self._particles_props = self._build_particles_props(
            config.particles, self._particles_data
        )
        self._rings_props = config.rings.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude_unset=True,
            exclude={"rings_data"},
            mode="json",
        )
        self._rings_props.update(
            {
                "ringLat": "lat",
                "ringLng": "lng",
                "ringAltitude": "altitude",
                "ringColor": "color",
                "ringMaxRadius": "maxRadius",
                "ringPropagationSpeed": "propagationSpeed",
                "ringRepeatPeriod": "repeatPeriod",
            }
        )
        self._labels_props = config.labels.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude_unset=True,
            exclude={"labels_data"},
            mode="json",
        )
        self._labels_props.update(
            {
                "labelLat": "lat",
                "labelLng": "lng",
                "labelAltitude": "altitude",
                "labelText": "text",
                "labelSize": "size",
                "labelRotation": "rotation",
                "labelColor": "color",
                "labelIncludeDot": "includeDot",
                "labelDotRadius": "dotRadius",
                "labelDotOrientation": "dotOrientation",
                "labelLabel": "label",
            }
        )
        config_dict = config.model_dump(
            by_alias=True, exclude_none=True, exclude_defaults=True, mode="json"
        )
        config_dict.setdefault("points", {}).update(self._points_props)
        config_dict.setdefault("arcs", {}).update(self._arcs_props)
        config_dict.setdefault("polygons", {}).update(self._polygons_props)
        config_dict.setdefault("paths", {}).update(self._paths_props)
        config_dict.setdefault("heatmaps", {}).update(self._heatmaps_props)
        config_dict.setdefault("hexed_polygons", {}).update(self._hex_polygons_props)
        config_dict.setdefault("tiles", {}).update(self._tiles_props)
        config_dict.setdefault("particles", {}).update(self._particles_props)
        config_dict.setdefault("rings", {}).update(self._rings_props)
        config_dict.setdefault("labels", {}).update(self._labels_props)
        if self._points_data is not None:
            config_dict.setdefault("points", {})["pointsData"] = self._points_data
        if self._arcs_data is not None:
            config_dict.setdefault("arcs", {})["arcsData"] = self._arcs_data
        if self._polygons_data is not None:
            config_dict.setdefault("polygons", {})["polygonsData"] = self._polygons_data
        if self._paths_data is not None:
            config_dict.setdefault("paths", {})["pathsData"] = self._paths_data
        if self._heatmaps_data is not None:
            config_dict.setdefault("heatmaps", {})["heatmapsData"] = self._heatmaps_data
        if self._hex_polygons_data is not None:
            config_dict.setdefault("hexed_polygons", {})["hexPolygonsData"] = (
                self._hex_polygons_data
            )
        if self._tiles_data is not None:
            config_dict.setdefault("tiles", {})["tilesData"] = self._tiles_data
        if self._particles_data is not None:
            config_dict.setdefault("particles", {})["particlesData"] = (
                self._particles_data
            )
        if self._rings_data is not None:
            config_dict.setdefault("rings", {})["ringsData"] = self._rings_data
        if self._labels_data is not None:
            config_dict.setdefault("labels", {})["labelsData"] = self._labels_data
        self.config = config_dict

    def on_globe_ready(self, handler: Callable[[], None]) -> None:
        """Register a callback fired when the globe is ready."""
        self._globe_ready_handlers.append(handler)

    def on_globe_click(self, handler: Callable[[dict[str, float]], None]) -> None:
        """Register a callback fired on globe left-clicks."""
        self._globe_click_handlers.append(handler)

    def on_globe_right_click(self, handler: Callable[[dict[str, float]], None]) -> None:
        """Register a callback fired on globe right-clicks."""
        self._globe_right_click_handlers.append(handler)

    def on_point_click(
        self, handler: Callable[[dict[str, Any], dict[str, float]], None]
    ) -> None:
        """Register a callback fired on point left-clicks."""
        self._point_click_handlers.append(handler)

    def on_point_right_click(
        self, handler: Callable[[dict[str, Any], dict[str, float]], None]
    ) -> None:
        """Register a callback fired on point right-clicks."""
        self._point_right_click_handlers.append(handler)

    def on_point_hover(
        self, handler: Callable[[dict[str, Any] | None, dict[str, Any] | None], None]
    ) -> None:
        """Register a callback fired on point hover events."""
        self._point_hover_handlers.append(handler)
        self._set_event_flag("pointHover", True)

    def on_arc_click(
        self, handler: Callable[[dict[str, Any], dict[str, float]], None]
    ) -> None:
        """Register a callback fired on arc left-clicks."""
        self._arc_click_handlers.append(handler)

    def on_arc_right_click(
        self, handler: Callable[[dict[str, Any], dict[str, float]], None]
    ) -> None:
        """Register a callback fired on arc right-clicks."""
        self._arc_right_click_handlers.append(handler)

    def on_arc_hover(
        self, handler: Callable[[dict[str, Any] | None, dict[str, Any] | None], None]
    ) -> None:
        """Register a callback fired on arc hover events."""
        self._arc_hover_handlers.append(handler)
        self._set_event_flag("arcHover", True)

    def on_polygon_click(
        self, handler: Callable[[dict[str, Any], dict[str, float]], None]
    ) -> None:
        """Register a callback fired on polygon left-clicks."""
        self._polygon_click_handlers.append(handler)

    def on_polygon_right_click(
        self, handler: Callable[[dict[str, Any], dict[str, float]], None]
    ) -> None:
        """Register a callback fired on polygon right-clicks."""
        self._polygon_right_click_handlers.append(handler)

    def on_polygon_hover(
        self, handler: Callable[[dict[str, Any] | None, dict[str, Any] | None], None]
    ) -> None:
        """Register a callback fired on polygon hover events."""
        self._polygon_hover_handlers.append(handler)
        self._set_event_flag("polygonHover", True)

    def on_path_click(
        self, handler: Callable[[dict[str, Any], dict[str, float]], None]
    ) -> None:
        """Register a callback fired on path left-clicks."""
        self._path_click_handlers.append(handler)

    def on_path_right_click(
        self, handler: Callable[[dict[str, Any], dict[str, float]], None]
    ) -> None:
        """Register a callback fired on path right-clicks."""
        self._path_right_click_handlers.append(handler)

    def on_path_hover(
        self, handler: Callable[[dict[str, Any] | None, dict[str, Any] | None], None]
    ) -> None:
        """Register a callback fired on path hover events."""
        self._path_hover_handlers.append(handler)
        self._set_event_flag("pathHover", True)

    def on_heatmap_click(
        self, handler: Callable[[dict[str, Any], dict[str, float]], None]
    ) -> None:
        """Register a callback fired on heatmap left-clicks."""
        self._heatmap_click_handlers.append(handler)

    def on_heatmap_right_click(
        self, handler: Callable[[dict[str, Any], dict[str, float]], None]
    ) -> None:
        """Register a callback fired on heatmap right-clicks."""
        self._heatmap_right_click_handlers.append(handler)

    def on_heatmap_hover(
        self, handler: Callable[[dict[str, Any] | None, dict[str, Any] | None], None]
    ) -> None:
        """Register a callback fired on heatmap hover events."""
        self._heatmap_hover_handlers.append(handler)
        self._set_event_flag("heatmapHover", True)

    def on_hex_polygon_click(
        self, handler: Callable[[dict[str, Any], dict[str, float]], None]
    ) -> None:
        """Register a callback fired on hexed polygon left-clicks."""
        self._hex_polygon_click_handlers.append(handler)

    def on_hex_polygon_right_click(
        self, handler: Callable[[dict[str, Any], dict[str, float]], None]
    ) -> None:
        """Register a callback fired on hexed polygon right-clicks."""
        self._hex_polygon_right_click_handlers.append(handler)

    def on_hex_polygon_hover(
        self, handler: Callable[[dict[str, Any] | None, dict[str, Any] | None], None]
    ) -> None:
        """Register a callback fired on hexed polygon hover events."""
        self._hex_polygon_hover_handlers.append(handler)
        self._set_event_flag("hexPolygonHover", True)

    def on_tile_click(
        self, handler: Callable[[dict[str, Any], dict[str, float]], None]
    ) -> None:
        """Register a callback fired on tile left-clicks."""
        self._tile_click_handlers.append(handler)

    def on_tile_right_click(
        self, handler: Callable[[dict[str, Any], dict[str, float]], None]
    ) -> None:
        """Register a callback fired on tile right-clicks."""
        self._tile_right_click_handlers.append(handler)

    def on_tile_hover(
        self, handler: Callable[[dict[str, Any] | None, dict[str, Any] | None], None]
    ) -> None:
        """Register a callback fired on tile hover events."""
        self._tile_hover_handlers.append(handler)
        self._set_event_flag("tileHover", True)

    def on_particle_click(
        self, handler: Callable[[dict[str, Any], dict[str, float]], None]
    ) -> None:
        """Register a callback fired on particle left-clicks."""
        self._particle_click_handlers.append(handler)

    def on_particle_right_click(
        self, handler: Callable[[dict[str, Any], dict[str, float]], None]
    ) -> None:
        """Register a callback fired on particle right-clicks."""
        self._particle_right_click_handlers.append(handler)

    def on_particle_hover(
        self, handler: Callable[[dict[str, Any] | None, dict[str, Any] | None], None]
    ) -> None:
        """Register a callback fired on particle hover events."""
        self._particle_hover_handlers.append(handler)
        self._set_event_flag("particleHover", True)

    def on_label_click(
        self, handler: Callable[[dict[str, Any], dict[str, float]], None]
    ) -> None:
        """Register a callback fired on label left-clicks."""
        self._label_click_handlers.append(handler)

    def on_label_right_click(
        self, handler: Callable[[dict[str, Any], dict[str, float]], None]
    ) -> None:
        """Register a callback fired on label right-clicks."""
        self._label_right_click_handlers.append(handler)

    def on_label_hover(
        self, handler: Callable[[dict[str, Any] | None, dict[str, Any] | None], None]
    ) -> None:
        """Register a callback fired on label hover events."""
        self._label_hover_handlers.append(handler)
        self._set_event_flag("labelHover", True)

    def globe_tile_engine_clear_cache(self) -> None:
        """Clear the globe tile engine cache."""
        self.send({"type": "globe_tile_engine_clear_cache"})

    def get_globe_image_url(self) -> str | None:
        """Return the globe image URL."""
        return self._globe_props.get("globeImageUrl")

    def set_globe_image_url(self, value: str | None) -> None:
        """Set the globe image URL."""
        self._set_layer_prop("globe", self._globe_props, "globeImageUrl", value)

    def get_bump_image_url(self) -> str | None:
        """Return the bump image URL."""
        return self._globe_props.get("bumpImageUrl")

    def set_bump_image_url(self, value: str | None) -> None:
        """Set the bump image URL."""
        self._set_layer_prop("globe", self._globe_props, "bumpImageUrl", value)

    def get_globe_tile_engine_url(self) -> str | None:
        """Return the globe tile engine URL."""
        return self._globe_props.get("globeTileEngineUrl")

    def set_globe_tile_engine_url(self, value: str | None) -> None:
        """Set the globe tile engine URL."""
        self._set_layer_prop("globe", self._globe_props, "globeTileEngineUrl", value)

    def get_show_globe(self) -> bool:
        """Return whether the globe mesh is visible."""
        return bool(self._globe_props.get("showGlobe", True))

    def set_show_globe(self, value: bool) -> None:
        """Set whether the globe mesh is visible."""
        self._set_layer_prop("globe", self._globe_props, "showGlobe", value)

    def get_show_graticules(self) -> bool:
        """Return whether graticules are visible."""
        return bool(self._globe_props.get("showGraticules", False))

    def set_show_graticules(self, value: bool) -> None:
        """Set whether graticules are visible."""
        self._set_layer_prop("globe", self._globe_props, "showGraticules", value)

    def get_show_atmosphere(self) -> bool:
        """Return whether the atmosphere is visible."""
        return bool(self._globe_props.get("showAtmosphere", True))

    def set_show_atmosphere(self, value: bool) -> None:
        """Set whether the atmosphere is visible."""
        self._set_layer_prop("globe", self._globe_props, "showAtmosphere", value)

    def get_atmosphere_color(self) -> str | None:
        """Return the atmosphere color."""
        return self._globe_props.get("atmosphereColor")

    def set_atmosphere_color(self, value: str | None) -> None:
        """Set the atmosphere color."""
        self._set_layer_prop("globe", self._globe_props, "atmosphereColor", value)

    def get_atmosphere_altitude(self) -> float | None:
        """Return the atmosphere altitude."""
        return self._globe_props.get("atmosphereAltitude")

    def set_atmosphere_altitude(self, value: float | None) -> None:
        """Set the atmosphere altitude."""
        self._set_layer_prop("globe", self._globe_props, "atmosphereAltitude", value)

    def get_globe_curvature_resolution(self) -> float | None:
        """Return the globe curvature resolution."""
        return self._globe_props.get("globeCurvatureResolution")

    def set_globe_curvature_resolution(self, value: float | None) -> None:
        """Set the globe curvature resolution."""
        self._set_layer_prop(
            "globe", self._globe_props, "globeCurvatureResolution", value
        )

    def get_globe_material(self) -> GlobeMaterialSpec | None:
        """Return the globe material spec."""
        value = self._globe_props.get("globeMaterial")
        if isinstance(value, dict):
            return GlobeMaterialSpec.model_validate(value)
        return None

    def set_globe_material(self, value: GlobeMaterialSpec | None) -> None:
        """Set the globe material spec."""
        serialized = value.model_dump(mode="json") if value is not None else None
        self._set_layer_prop("globe", self._globe_props, "globeMaterial", serialized)

    def get_points_data(self) -> list[PointDatum] | None:
        """Return a copy of the cached points data."""
        return self._denormalize_layer_data(self._points_data, PointDatum)

    def set_points_data(self, data: Sequence[PointDatum]) -> None:
        """Replace the points data at runtime."""
        normalized = self._normalize_layer_data(data)
        self._points_data = normalized
        self.send({"type": "points_set_data", "payload": {"data": normalized}})

    def patch_points_data(self, patches: Sequence[PointDatumPatch]) -> None:
        """Patch points data by id."""
        normalized = self._normalize_point_patches(patches)
        self._apply_patches(self._points_data, normalized, "points")
        self.send({"type": "points_patch_data", "payload": {"patches": normalized}})

    def update_point(self, point_id: UUID4 | str, **changes: Any) -> None:
        """Update a single point by id."""
        patch = PointDatumPatch.model_validate({"id": point_id, **changes})
        self.patch_points_data([patch])

    def get_point_resolution(self) -> int:
        """Return the point resolution."""
        return int(self._points_props.get("pointResolution", 12))

    def set_point_resolution(self, value: int) -> None:
        """Set the point resolution."""
        self._set_layer_prop("points", self._points_props, "pointResolution", value)

    def get_points_merge(self) -> bool:
        """Return whether points are merged."""
        return bool(self._points_props.get("pointsMerge", False))

    def set_points_merge(self, value: bool) -> None:
        """Set whether points are merged."""
        self._set_layer_prop("points", self._points_props, "pointsMerge", value)

    def get_points_transition_duration(self) -> int:
        """Return the points transition duration."""
        return int(self._points_props.get("pointsTransitionDuration", 1000))

    def set_points_transition_duration(self, value: int) -> None:
        """Set the points transition duration."""
        self._set_layer_prop(
            "points", self._points_props, "pointsTransitionDuration", value
        )

    def get_arcs_data(self) -> list[ArcDatum] | None:
        """Return a copy of the cached arcs data."""
        return self._denormalize_layer_data(self._arcs_data, ArcDatum)

    def set_arcs_data(self, data: Sequence[ArcDatum]) -> None:
        """Replace the arcs data at runtime."""
        normalized = self._normalize_layer_data(data)
        self._arcs_data = normalized
        self.send({"type": "arcs_set_data", "payload": {"data": normalized}})

    def patch_arcs_data(self, patches: Sequence[ArcDatumPatch]) -> None:
        """Patch arcs data by id."""
        normalized = self._normalize_arc_patches(patches)
        self._apply_patches(self._arcs_data, normalized, "arcs")
        self.send({"type": "arcs_patch_data", "payload": {"patches": normalized}})

    def update_arc(self, arc_id: UUID4 | str, **changes: Any) -> None:
        """Update a single arc by id."""
        patch = ArcDatumPatch.model_validate({"id": arc_id, **changes})
        self.patch_arcs_data([patch])

    def get_arc_curve_resolution(self) -> int:
        """Return the arc curve resolution."""
        return int(self._arcs_props.get("arcCurveResolution", 64))

    def set_arc_curve_resolution(self, value: int) -> None:
        """Set the arc curve resolution."""
        self._set_layer_prop("arcs", self._arcs_props, "arcCurveResolution", value)

    def get_arc_circular_resolution(self) -> int:
        """Return the arc circular resolution."""
        return int(self._arcs_props.get("arcCircularResolution", 6))

    def set_arc_circular_resolution(self, value: int) -> None:
        """Set the arc circular resolution."""
        self._set_layer_prop("arcs", self._arcs_props, "arcCircularResolution", value)

    def get_arcs_transition_duration(self) -> int:
        """Return the arcs transition duration."""
        return int(self._arcs_props.get("arcsTransitionDuration", 1000))

    def set_arcs_transition_duration(self, value: int) -> None:
        """Set the arcs transition duration."""
        self._set_layer_prop("arcs", self._arcs_props, "arcsTransitionDuration", value)

    def get_polygon_cap_material(self) -> GlobeMaterialSpec | None:
        """Return the polygon cap material."""
        value = self._polygons_props.get("polygonCapMaterial")
        if isinstance(value, dict):
            return GlobeMaterialSpec.model_validate(value)
        return None

    def set_polygon_cap_material(self, value: GlobeMaterialSpec | None) -> None:
        """Set the polygon cap material."""
        serialized = value.model_dump(mode="json") if value is not None else None
        self._set_layer_prop(
            "polygons", self._polygons_props, "polygonCapMaterial", serialized
        )

    def get_polygon_side_material(self) -> GlobeMaterialSpec | None:
        """Return the polygon side material."""
        value = self._polygons_props.get("polygonSideMaterial")
        if isinstance(value, dict):
            return GlobeMaterialSpec.model_validate(value)
        return None

    def set_polygon_side_material(self, value: GlobeMaterialSpec | None) -> None:
        """Set the polygon side material."""
        serialized = value.model_dump(mode="json") if value is not None else None
        self._set_layer_prop(
            "polygons", self._polygons_props, "polygonSideMaterial", serialized
        )

    def get_polygons_transition_duration(self) -> int:
        """Return the polygons transition duration."""
        return int(self._polygons_props.get("polygonsTransitionDuration", 1000))

    def set_polygons_transition_duration(self, value: int) -> None:
        """Set the polygons transition duration."""
        self._set_layer_prop(
            "polygons", self._polygons_props, "polygonsTransitionDuration", value
        )

    def get_polygons_data(self) -> list[PolygonDatum] | None:
        """Return a copy of the cached polygons data."""
        return self._denormalize_layer_data(self._polygons_data, PolygonDatum)

    def set_polygons_data(self, data: Sequence[PolygonDatum]) -> None:
        """Replace the polygons data at runtime."""
        normalized = self._normalize_layer_data(data)
        self._polygons_data = normalized
        self.send({"type": "polygons_set_data", "payload": {"data": normalized}})

    def patch_polygons_data(self, patches: Sequence[PolygonDatumPatch]) -> None:
        """Patch polygons data by id."""
        normalized = self._normalize_polygon_patches(patches)
        self._apply_patches(self._polygons_data, normalized, "polygons")
        self.send({"type": "polygons_patch_data", "payload": {"patches": normalized}})

    def update_polygon(self, polygon_id: UUID4 | str, **changes: Any) -> None:
        """Update a single polygon by id."""
        patch = PolygonDatumPatch.model_validate({"id": polygon_id, **changes})
        self.patch_polygons_data([patch])

    def get_paths_data(self) -> list[PathDatum] | None:
        """Return a copy of the cached paths data."""
        return self._denormalize_layer_data(self._paths_data, PathDatum)

    def set_paths_data(self, data: Sequence[PathDatum]) -> None:
        """Replace the paths data at runtime."""
        normalized = self._normalize_layer_data(data)
        self._paths_data = normalized
        self.send({"type": "paths_set_data", "payload": {"data": normalized}})

    def patch_paths_data(self, patches: Sequence[PathDatumPatch]) -> None:
        """Patch paths data by id."""
        normalized = self._normalize_path_patches(patches)
        self._apply_patches(self._paths_data, normalized, "paths")
        self.send({"type": "paths_patch_data", "payload": {"patches": normalized}})

    def update_path(self, path_id: UUID4 | str, **changes: Any) -> None:
        """Update a single path by id."""
        patch = PathDatumPatch.model_validate({"id": path_id, **changes})
        self.patch_paths_data([patch])

    def get_path_resolution(self) -> int:
        """Return the path resolution."""
        return int(self._paths_props.get("pathResolution", 2))

    def set_path_resolution(self, value: int) -> None:
        """Set the path resolution."""
        self._set_layer_prop("paths", self._paths_props, "pathResolution", value)

    def get_path_stroke(self) -> float | None:
        """Return the path stroke."""
        return self._paths_props.get("pathStroke")

    def set_path_stroke(self, value: float | None) -> None:
        """Set the path stroke."""
        self._set_layer_prop("paths", self._paths_props, "pathStroke", value)

    def get_path_dash_length(self) -> float:
        """Return the path dash length."""
        value = self._paths_props.get("pathDashLength", 1.0)
        if isinstance(value, (int, float)):
            return float(value)
        return 1.0

    def set_path_dash_length(self, value: float) -> None:
        """Set the path dash length."""
        self._set_layer_prop("paths", self._paths_props, "pathDashLength", value)

    def get_path_dash_gap(self) -> float:
        """Return the path dash gap."""
        value = self._paths_props.get("pathDashGap", 0.0)
        if isinstance(value, (int, float)):
            return float(value)
        return 0.0

    def set_path_dash_gap(self, value: float) -> None:
        """Set the path dash gap."""
        self._set_layer_prop("paths", self._paths_props, "pathDashGap", value)

    def get_path_transition_duration(self) -> int:
        """Return the path transition duration."""
        return int(self._paths_props.get("pathTransitionDuration", 1000))

    def set_path_transition_duration(self, value: int) -> None:
        """Set the path transition duration."""
        self._set_layer_prop(
            "paths", self._paths_props, "pathTransitionDuration", value
        )

    def get_heatmaps_data(self) -> list[HeatmapDatum] | None:
        """Return a copy of the cached heatmaps data."""
        return self._denormalize_layer_data(self._heatmaps_data, HeatmapDatum)

    def set_heatmaps_data(self, data: Sequence[HeatmapDatum]) -> None:
        """Replace the heatmaps data at runtime."""
        normalized = self._normalize_layer_data(data)
        self._heatmaps_data = normalized
        self.send({"type": "heatmaps_set_data", "payload": {"data": normalized}})

    def patch_heatmaps_data(self, patches: Sequence[HeatmapDatumPatch]) -> None:
        """Patch heatmaps data by id."""
        normalized = self._normalize_heatmap_patches(patches)
        self._apply_patches(self._heatmaps_data, normalized, "heatmaps")
        self.send({"type": "heatmaps_patch_data", "payload": {"patches": normalized}})

    def update_heatmap(self, heatmap_id: UUID4 | str, **changes: Any) -> None:
        """Update a single heatmap by id."""
        patch = HeatmapDatumPatch.model_validate({"id": heatmap_id, **changes})
        self.patch_heatmaps_data([patch])

    def get_heatmaps_transition_duration(self) -> int:
        """Return the heatmaps transition duration."""
        return int(self._heatmaps_props.get("heatmapsTransitionDuration", 0))

    def set_heatmaps_transition_duration(self, value: int) -> None:
        """Set the heatmaps transition duration."""
        self._set_layer_prop(
            "heatmaps", self._heatmaps_props, "heatmapsTransitionDuration", value
        )

    def get_hex_polygons_data(self) -> list[HexPolygonDatum] | None:
        """Return a copy of the cached hexed polygons data."""
        return self._denormalize_layer_data(self._hex_polygons_data, HexPolygonDatum)

    def set_hex_polygons_data(self, data: Sequence[HexPolygonDatum]) -> None:
        """Replace the hexed polygons data at runtime."""
        normalized = self._normalize_layer_data(data)
        self._hex_polygons_data = normalized
        self.send({"type": "hex_polygons_set_data", "payload": {"data": normalized}})

    def patch_hex_polygons_data(self, patches: Sequence[HexPolygonDatumPatch]) -> None:
        """Patch hexed polygons data by id."""
        normalized = self._normalize_hex_polygon_patches(patches)
        self._apply_patches(self._hex_polygons_data, normalized, "hex_polygons")
        self.send(
            {"type": "hex_polygons_patch_data", "payload": {"patches": normalized}}
        )

    def update_hex_polygon(self, polygon_id: UUID4 | str, **changes: Any) -> None:
        """Update a single hexed polygon by id."""
        patch = HexPolygonDatumPatch.model_validate({"id": polygon_id, **changes})
        self.patch_hex_polygons_data([patch])

    def get_hex_polygons_transition_duration(self) -> int:
        """Return the hexed polygons transition duration."""
        return int(self._hex_polygons_props.get("hexPolygonsTransitionDuration", 0))

    def set_hex_polygons_transition_duration(self, value: int) -> None:
        """Set the hexed polygons transition duration."""
        self._set_layer_prop(
            "hex_polygons",
            self._hex_polygons_props,
            "hexPolygonsTransitionDuration",
            value,
        )

    def get_tiles_data(self) -> list[TileDatum] | None:
        """Return a copy of the cached tiles data."""
        return self._denormalize_layer_data(self._tiles_data, TileDatum)

    def set_tiles_data(self, data: Sequence[TileDatum]) -> None:
        """Replace the tiles data at runtime."""
        normalized = self._normalize_tile_data(data)
        self._tiles_data = normalized
        self.send({"type": "tiles_set_data", "payload": {"data": normalized}})

    def patch_tiles_data(self, patches: Sequence[TileDatumPatch]) -> None:
        """Patch tiles data by id."""
        normalized = self._normalize_tile_patches(patches)
        self._apply_patches(self._tiles_data, normalized, "tiles")
        self.send({"type": "tiles_patch_data", "payload": {"patches": normalized}})

    def update_tile(self, tile_id: UUID4 | str, **changes: Any) -> None:
        """Update a single tile by id."""
        patch = TileDatumPatch.model_validate({"id": tile_id, **changes})
        self.patch_tiles_data([patch])

    def get_tiles_transition_duration(self) -> int:
        """Return the tiles transition duration."""
        return int(self._tiles_props.get("tilesTransitionDuration", 1000))

    def set_tiles_transition_duration(self, value: int) -> None:
        """Set the tiles transition duration."""
        self._set_layer_prop(
            "tiles", self._tiles_props, "tilesTransitionDuration", value
        )

    def get_particles_data(self) -> list[ParticleDatum] | None:
        """Return a copy of the cached particles data."""
        return self._denormalize_layer_data(self._particles_data, ParticleDatum)

    def set_particles_data(self, data: Sequence[ParticleDatum]) -> None:
        """Replace the particles data at runtime."""
        normalized = self._normalize_layer_data(data)
        self._particles_data = normalized
        self.send({"type": "particles_set_data", "payload": {"data": normalized}})

    def patch_particles_data(self, patches: Sequence[ParticleDatumPatch]) -> None:
        """Patch particles data by id."""
        normalized = self._normalize_particle_patches(patches)
        self._apply_patches(self._particles_data, normalized, "particles")
        self.send({"type": "particles_patch_data", "payload": {"patches": normalized}})

    def update_particle(self, particle_id: UUID4 | str, **changes: Any) -> None:
        """Update a single particles entry by id."""
        patch = ParticleDatumPatch.model_validate({"id": particle_id, **changes})
        self.patch_particles_data([patch])

    def get_rings_data(self) -> list[RingDatum] | None:
        """Return a copy of the cached rings data."""
        return self._denormalize_layer_data(self._rings_data, RingDatum)

    def set_rings_data(self, data: Sequence[RingDatum]) -> None:
        """Replace the rings data at runtime."""
        normalized = self._normalize_layer_data(data)
        self._rings_data = normalized
        self.send({"type": "rings_set_data", "payload": {"data": normalized}})

    def patch_rings_data(self, patches: Sequence[RingDatumPatch]) -> None:
        """Patch rings data by id."""
        normalized = self._normalize_ring_patches(patches)
        self._apply_patches(self._rings_data, normalized, "rings")
        self.send({"type": "rings_patch_data", "payload": {"patches": normalized}})

    def update_ring(self, ring_id: UUID4 | str, **changes: Any) -> None:
        """Update a single ring by id."""
        patch = RingDatumPatch.model_validate({"id": ring_id, **changes})
        self.patch_rings_data([patch])

    def get_ring_resolution(self) -> int:
        """Return the ring resolution."""
        return int(self._rings_props.get("ringResolution", 64))

    def set_ring_resolution(self, value: int) -> None:
        """Set the ring resolution."""
        self._set_layer_prop("rings", self._rings_props, "ringResolution", value)

    def get_labels_data(self) -> list[LabelDatum] | None:
        """Return a copy of the cached labels data."""
        return self._denormalize_layer_data(self._labels_data, LabelDatum)

    def set_labels_data(self, data: Sequence[LabelDatum]) -> None:
        """Replace the labels data at runtime."""
        normalized = self._normalize_layer_data(data)
        self._labels_data = normalized
        self.send({"type": "labels_set_data", "payload": {"data": normalized}})

    def patch_labels_data(self, patches: Sequence[LabelDatumPatch]) -> None:
        """Patch labels data by id."""
        normalized = self._normalize_label_patches(patches)
        self._apply_patches(self._labels_data, normalized, "labels")
        self.send({"type": "labels_patch_data", "payload": {"patches": normalized}})

    def update_label(self, label_id: UUID4 | str, **changes: Any) -> None:
        """Update a single label by id."""
        patch = LabelDatumPatch.model_validate({"id": label_id, **changes})
        self.patch_labels_data([patch])

    def get_label_type_face(self) -> dict[str, Any] | None:
        """Return the label type face JSON."""
        value = self._labels_props.get("labelTypeFace")
        return value if isinstance(value, dict) else None

    def set_label_type_face(self, value: dict[str, Any] | None) -> None:
        """Set the label type face JSON."""
        self._set_layer_prop("labels", self._labels_props, "labelTypeFace", value)

    def get_label_resolution(self) -> int:
        """Return the label resolution."""
        return int(self._labels_props.get("labelResolution", 3))

    def set_label_resolution(self, value: int) -> None:
        """Set the label resolution."""
        self._set_layer_prop("labels", self._labels_props, "labelResolution", value)

    def get_labels_transition_duration(self) -> int:
        """Return the labels transition duration."""
        return int(self._labels_props.get("labelsTransitionDuration", 1000))

    def set_labels_transition_duration(self, value: int) -> None:
        """Set the labels transition duration."""
        self._set_layer_prop(
            "labels", self._labels_props, "labelsTransitionDuration", value
        )

    def _handle_frontend_message(
        self, _widget: "GlobeWidget", message: dict[str, Any], _buffers: list[bytes]
    ) -> None:
        msg_type = message.get("type")
        if not isinstance(msg_type, str):
            return
        handler = self._message_handlers.get(msg_type)
        if handler is None:
            return
        handler(message.get("payload"))

    def _denormalize_layer_data(
        self, data: list[dict[str, Any]] | None, model: type[ModelT]
    ) -> list[ModelT] | None:
        if data is None:
            return None
        alias_map = _model_alias_map(model)
        normalized = []
        for entry in data:
            copied = copy.deepcopy(entry)
            mapped = {alias_map.get(key, key): value for key, value in copied.items()}
            normalized.append(model.model_validate(mapped))
        return normalized

    def _normalize_layer_data(
        self, data: Sequence[BaseModel] | None
    ) -> list[dict[str, Any]] | None:
        if data is None:
            return None

        normalized: list[dict[str, Any]] = []
        for item in data:
            if not isinstance(item, BaseModel):
                raise TypeError("Layer data must be Pydantic models.")
            entry = item.model_dump(by_alias=True, exclude_none=True, mode="json")
            if entry.get("id") is None:
                entry["id"] = str(uuid4())
            else:
                entry["id"] = str(entry["id"])
            normalized.append(entry)
        return normalized

    def _set_event_flag(self, name: str, enabled: bool) -> None:
        updated = dict(self.event_config or {})
        if updated.get(name) == enabled:
            return
        updated[name] = enabled
        self.event_config = updated

    def _build_particles_props(
        self,
        particles_config: ParticlesLayerConfig,
        particles_data: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        props = particles_config.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude_unset=True,
            exclude={"particles_data"},
            mode="json",
        )
        props.update(
            {
                "particleLat": "lat",
                "particleLng": "lng",
                "particleAltitude": "altitude",
                "particlesSize": "size",
                "particlesSizeAttenuation": "sizeAttenuation",
                "particlesColor": "color",
                "particlesTexture": "texture",
                "particleLabel": "label",
            }
        )
        return props

    def _normalize_tile_data(
        self, data: Sequence[TileDatum] | None
    ) -> list[dict[str, Any]] | None:
        return self._normalize_layer_data(data)

    def _normalize_point_patches(
        self, patches: Sequence[PointDatumPatch]
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for patch in patches:
            if not isinstance(patch, PointDatumPatch):
                raise TypeError("Patch entries must be PointDatumPatch.")
            entry = patch.model_dump(
                by_alias=True, exclude_unset=True, exclude_none=False, mode="json"
            )
            if entry.get("id") is None:
                raise ValueError("Patch entries must include an id.")
            entry["id"] = str(entry["id"])
            normalized.append(entry)
        return normalized

    def _normalize_arc_patches(
        self, patches: Sequence[ArcDatumPatch]
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for patch in patches:
            if not isinstance(patch, ArcDatumPatch):
                raise TypeError("Patch entries must be ArcDatumPatch.")
            entry = patch.model_dump(
                by_alias=True, exclude_unset=True, exclude_none=False, mode="json"
            )
            if entry.get("id") is None:
                raise ValueError("Patch entries must include an id.")
            entry["id"] = str(entry["id"])
            normalized.append(entry)
        return normalized

    def _normalize_polygon_patches(
        self, patches: Sequence[PolygonDatumPatch]
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for patch in patches:
            if not isinstance(patch, PolygonDatumPatch):
                raise TypeError("Patch entries must be PolygonDatumPatch.")
            entry = patch.model_dump(
                by_alias=True, exclude_unset=True, exclude_none=False, mode="json"
            )
            if entry.get("id") is None:
                raise ValueError("Patch entries must include an id.")
            entry["id"] = str(entry["id"])
            normalized.append(entry)
        return normalized

    def _normalize_path_patches(
        self, patches: Sequence[PathDatumPatch]
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for patch in patches:
            if not isinstance(patch, PathDatumPatch):
                raise TypeError("Patch entries must be PathDatumPatch.")
            entry = patch.model_dump(
                by_alias=True, exclude_unset=True, exclude_none=False, mode="json"
            )
            if entry.get("id") is None:
                raise ValueError("Patch entries must include an id.")
            entry["id"] = str(entry["id"])
            normalized.append(entry)
        return normalized

    def _normalize_heatmap_patches(
        self, patches: Sequence[HeatmapDatumPatch]
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for patch in patches:
            if not isinstance(patch, HeatmapDatumPatch):
                raise TypeError("Patch entries must be HeatmapDatumPatch.")
            entry = patch.model_dump(
                by_alias=True, exclude_unset=True, exclude_none=False, mode="json"
            )
            if entry.get("id") is None:
                raise ValueError("Patch entries must include an id.")
            entry["id"] = str(entry["id"])
            normalized.append(entry)
        return normalized

    def _normalize_hex_polygon_patches(
        self, patches: Sequence[HexPolygonDatumPatch]
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for patch in patches:
            if not isinstance(patch, HexPolygonDatumPatch):
                raise TypeError("Patch entries must be HexPolygonDatumPatch.")
            entry = patch.model_dump(
                by_alias=True, exclude_unset=True, exclude_none=False, mode="json"
            )
            if entry.get("id") is None:
                raise ValueError("Patch entries must include an id.")
            entry["id"] = str(entry["id"])
            normalized.append(entry)
        return normalized

    def _normalize_tile_patches(
        self, patches: Sequence[TileDatumPatch]
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for patch in patches:
            if not isinstance(patch, TileDatumPatch):
                raise TypeError("Patch entries must be TileDatumPatch.")
            entry = patch.model_dump(
                by_alias=True, exclude_unset=True, exclude_none=False, mode="json"
            )
            if entry.get("id") is None:
                raise ValueError("Patch entries must include an id.")
            entry["id"] = str(entry["id"])
            normalized.append(entry)
        return normalized

    def _normalize_particle_patches(
        self, patches: Sequence[ParticleDatumPatch]
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for patch in patches:
            if not isinstance(patch, ParticleDatumPatch):
                raise TypeError("Patch entries must be ParticleDatumPatch.")
            entry = patch.model_dump(
                by_alias=True, exclude_unset=True, exclude_none=False, mode="json"
            )
            if entry.get("id") is None:
                raise ValueError("Patch entries must include an id.")
            entry["id"] = str(entry["id"])
            normalized.append(entry)
        return normalized

    def _normalize_ring_patches(
        self, patches: Sequence[RingDatumPatch]
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for patch in patches:
            if not isinstance(patch, RingDatumPatch):
                raise TypeError("Patch entries must be RingDatumPatch.")
            entry = patch.model_dump(
                by_alias=True, exclude_unset=True, exclude_none=False, mode="json"
            )
            if entry.get("id") is None:
                raise ValueError("Patch entries must include an id.")
            entry["id"] = str(entry["id"])
            normalized.append(entry)
        return normalized

    def _normalize_label_patches(
        self, patches: Sequence[LabelDatumPatch]
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for patch in patches:
            if not isinstance(patch, LabelDatumPatch):
                raise TypeError("Patch entries must be LabelDatumPatch.")
            entry = patch.model_dump(
                by_alias=True, exclude_unset=True, exclude_none=False, mode="json"
            )
            if entry.get("id") is None:
                raise ValueError("Patch entries must include an id.")
            entry["id"] = str(entry["id"])
            normalized.append(entry)
        return normalized

    def _apply_patches(
        self,
        data: list[dict[str, Any]] | None,
        patches: list[dict[str, Any]],
        layer_name: str,
    ) -> None:
        if data is None:
            raise ValueError(f"{layer_name} data is not initialized.")
        index = {
            str(item.get("id")): item for item in data if item.get("id") is not None
        }
        for patch in patches:
            patch_id = str(patch.get("id"))
            target = index.get(patch_id)
            if target is None:
                raise ValueError(f"{layer_name} id not found: {patch_id}")
            for key, value in patch.items():
                if key == "id":
                    continue
                target[key] = value

    def _set_layer_prop(
        self, layer: str, props: dict[str, Any], prop: str, value: Any
    ) -> None:
        props[prop] = value
        self.send({"type": f"{layer}_prop", "payload": {"prop": prop, "value": value}})

    def _dispatch_globe_ready(self) -> None:
        for handler in self._globe_ready_handlers:
            handler()

    def _dispatch_globe_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        for handler in self._globe_click_handlers:
            handler(payload)

    def _dispatch_globe_right_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        for handler in self._globe_right_click_handlers:
            handler(payload)

    def _dispatch_point_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        point = payload.get("point")
        coords = payload.get("coords")
        if isinstance(point, dict) and isinstance(coords, dict):
            for handler in self._point_click_handlers:
                handler(point, coords)

    def _dispatch_point_right_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        point = payload.get("point")
        coords = payload.get("coords")
        if isinstance(point, dict) and isinstance(coords, dict):
            for handler in self._point_right_click_handlers:
                handler(point, coords)

    def _dispatch_point_hover(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        point = payload.get("point")
        prev_point = payload.get("prev_point")
        if point is not None and not isinstance(point, dict):
            return
        if prev_point is not None and not isinstance(prev_point, dict):
            return
        for handler in self._point_hover_handlers:
            handler(point, prev_point)

    def _dispatch_arc_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        arc = payload.get("arc")
        coords = payload.get("coords")
        if isinstance(arc, dict) and isinstance(coords, dict):
            for handler in self._arc_click_handlers:
                handler(arc, coords)

    def _dispatch_arc_right_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        arc = payload.get("arc")
        coords = payload.get("coords")
        if isinstance(arc, dict) and isinstance(coords, dict):
            for handler in self._arc_right_click_handlers:
                handler(arc, coords)

    def _dispatch_arc_hover(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        arc = payload.get("arc")
        prev_arc = payload.get("prev_arc")
        if arc is not None and not isinstance(arc, dict):
            return
        if prev_arc is not None and not isinstance(prev_arc, dict):
            return
        for handler in self._arc_hover_handlers:
            handler(arc, prev_arc)

    def _dispatch_polygon_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        polygon = payload.get("polygon")
        coords = payload.get("coords")
        if isinstance(polygon, dict) and isinstance(coords, dict):
            for handler in self._polygon_click_handlers:
                handler(polygon, coords)

    def _dispatch_polygon_right_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        polygon = payload.get("polygon")
        coords = payload.get("coords")
        if isinstance(polygon, dict) and isinstance(coords, dict):
            for handler in self._polygon_right_click_handlers:
                handler(polygon, coords)

    def _dispatch_polygon_hover(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        polygon = payload.get("polygon")
        prev_polygon = payload.get("prev_polygon")
        if polygon is not None and not isinstance(polygon, dict):
            return
        if prev_polygon is not None and not isinstance(prev_polygon, dict):
            return
        for handler in self._polygon_hover_handlers:
            handler(polygon, prev_polygon)

    def _dispatch_path_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        path = payload.get("path")
        coords = payload.get("coords")
        if isinstance(path, dict) and isinstance(coords, dict):
            for handler in self._path_click_handlers:
                handler(path, coords)

    def _dispatch_path_right_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        path = payload.get("path")
        coords = payload.get("coords")
        if isinstance(path, dict) and isinstance(coords, dict):
            for handler in self._path_right_click_handlers:
                handler(path, coords)

    def _dispatch_path_hover(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        path = payload.get("path")
        prev_path = payload.get("prev_path")
        if path is not None and not isinstance(path, dict):
            return
        if prev_path is not None and not isinstance(prev_path, dict):
            return
        for handler in self._path_hover_handlers:
            handler(path, prev_path)

    def _dispatch_heatmap_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        heatmap = payload.get("heatmap")
        coords = payload.get("coords")
        if isinstance(heatmap, dict) and isinstance(coords, dict):
            for handler in self._heatmap_click_handlers:
                handler(heatmap, coords)

    def _dispatch_heatmap_right_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        heatmap = payload.get("heatmap")
        coords = payload.get("coords")
        if isinstance(heatmap, dict) and isinstance(coords, dict):
            for handler in self._heatmap_right_click_handlers:
                handler(heatmap, coords)

    def _dispatch_heatmap_hover(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        heatmap = payload.get("heatmap")
        prev_heatmap = payload.get("prev_heatmap")
        if heatmap is not None and not isinstance(heatmap, dict):
            return
        if prev_heatmap is not None and not isinstance(prev_heatmap, dict):
            return
        for handler in self._heatmap_hover_handlers:
            handler(heatmap, prev_heatmap)

    def _dispatch_hex_polygon_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        hex_polygon = payload.get("hex_polygon")
        coords = payload.get("coords")
        if isinstance(hex_polygon, dict) and isinstance(coords, dict):
            for handler in self._hex_polygon_click_handlers:
                handler(hex_polygon, coords)

    def _dispatch_hex_polygon_right_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        hex_polygon = payload.get("hex_polygon")
        coords = payload.get("coords")
        if isinstance(hex_polygon, dict) and isinstance(coords, dict):
            for handler in self._hex_polygon_right_click_handlers:
                handler(hex_polygon, coords)

    def _dispatch_hex_polygon_hover(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        hex_polygon = payload.get("hex_polygon")
        prev_hex_polygon = payload.get("prev_hex_polygon")
        if hex_polygon is not None and not isinstance(hex_polygon, dict):
            return
        if prev_hex_polygon is not None and not isinstance(prev_hex_polygon, dict):
            return
        for handler in self._hex_polygon_hover_handlers:
            handler(hex_polygon, prev_hex_polygon)

    def _dispatch_tile_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        tile = payload.get("tile")
        coords = payload.get("coords")
        if isinstance(tile, dict) and isinstance(coords, dict):
            for handler in self._tile_click_handlers:
                handler(tile, coords)

    def _dispatch_tile_right_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        tile = payload.get("tile")
        coords = payload.get("coords")
        if isinstance(tile, dict) and isinstance(coords, dict):
            for handler in self._tile_right_click_handlers:
                handler(tile, coords)

    def _dispatch_tile_hover(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        tile = payload.get("tile")
        prev_tile = payload.get("prev_tile")
        if tile is not None and not isinstance(tile, dict):
            return
        if prev_tile is not None and not isinstance(prev_tile, dict):
            return
        for handler in self._tile_hover_handlers:
            handler(tile, prev_tile)

    def _dispatch_particle_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        particle = payload.get("particle")
        coords = payload.get("coords")
        if isinstance(particle, dict) and isinstance(coords, dict):
            for handler in self._particle_click_handlers:
                handler(particle, coords)

    def _dispatch_particle_right_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        particle = payload.get("particle")
        coords = payload.get("coords")
        if isinstance(particle, dict) and isinstance(coords, dict):
            for handler in self._particle_right_click_handlers:
                handler(particle, coords)

    def _dispatch_particle_hover(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        particle = payload.get("particle")
        prev_particle = payload.get("prev_particle")
        if particle is not None and not isinstance(particle, dict):
            return
        if prev_particle is not None and not isinstance(prev_particle, dict):
            return
        for handler in self._particle_hover_handlers:
            handler(particle, prev_particle)

    def _dispatch_label_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        label = payload.get("label")
        coords = payload.get("coords")
        if isinstance(label, dict) and isinstance(coords, dict):
            for handler in self._label_click_handlers:
                handler(label, coords)

    def _dispatch_label_right_click(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        label = payload.get("label")
        coords = payload.get("coords")
        if isinstance(label, dict) and isinstance(coords, dict):
            for handler in self._label_right_click_handlers:
                handler(label, coords)

    def _dispatch_label_hover(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        label = payload.get("label")
        prev_label = payload.get("prev_label")
        if label is not None and not isinstance(label, dict):
            return
        if prev_label is not None and not isinstance(prev_label, dict):
            return
        for handler in self._label_hover_handlers:
            handler(label, prev_label)
