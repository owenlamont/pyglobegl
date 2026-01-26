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
    PointDatum,
    PointDatumPatch,
    PolygonDatum,
    PolygonDatumPatch,
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
        }
        self.on_msg(self._handle_frontend_message)
        self._points_data = self._normalize_layer_data(config.points.points_data)
        self._arcs_data = self._normalize_layer_data(config.arcs.arcs_data)
        self._polygons_data = self._normalize_layer_data(config.polygons.polygons_data)
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
        config_dict = config.model_dump(
            by_alias=True, exclude_none=True, exclude_defaults=True, mode="json"
        )
        config_dict.setdefault("points", {}).update(self._points_props)
        config_dict.setdefault("arcs", {}).update(self._arcs_props)
        config_dict.setdefault("polygons", {}).update(self._polygons_props)
        if self._points_data is not None:
            config_dict.setdefault("points", {})["pointsData"] = self._points_data
        if self._arcs_data is not None:
            config_dict.setdefault("arcs", {})["arcsData"] = self._arcs_data
        if self._polygons_data is not None:
            config_dict.setdefault("polygons", {})["polygonsData"] = self._polygons_data
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
        self, data: Sequence[PointDatum | ArcDatum | PolygonDatum] | None
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
