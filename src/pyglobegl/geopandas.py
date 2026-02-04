"""GeoPandas helpers for pyglobegl."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, TypeGuard

from pyglobegl.config import (
    ArcDatum,
    HeatmapDatum,
    HeatmapPointDatum,
    HexPolygonDatum,
    LabelDatum,
    ParticleDatum,
    ParticlePointDatum,
    PathDatum,
    PointDatum,
    PolygonDatum,
    RingDatum,
    TileDatum,
)


if TYPE_CHECKING:
    import geopandas as gpd
    import pandas as pd
    import pandera.pandas as pa
    from pandera.typing import Series
    from pandera.typing.geopandas import Geometry, GeoSeries
    from pydantic import BaseModel
    from shapely.geometry.base import BaseGeometry


def _require_geopandas() -> None:
    try:
        import geopandas as gpd  # noqa: F401
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "GeoPandas is required for pyglobegl GeoDataFrame helpers. "
            "Install with `uv add pyglobegl[geopandas]`."
        ) from exc


def _require_pandera() -> None:
    try:
        import pandera.pandas as pa  # noqa: F401
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "pandera is required for GeoDataFrame validation. "
            "Install with `uv add pyglobegl[geopandas]`."
        ) from exc


def _require_pandas() -> None:
    try:
        import pandas as pd  # noqa: F401
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "pandas is required for GeoDataFrame validation. "
            "Install with `uv add pyglobegl[geopandas]`."
        ) from exc


def _build_points_schema() -> type[pa.DataFrameModel]:
    import pandera.pandas as pa
    from pandera.typing import Series
    from pandera.typing.geopandas import Geometry, GeoSeries

    globals().update({"Series": Series, "GeoSeries": GeoSeries, "Geometry": Geometry})

    class PointsGeoDataFrameModel(pa.DataFrameModel):
        """Pandera schema for point geometries."""

        geometry: GeoSeries[Geometry] = pa.Field(
            nullable=False, dtype_kwargs={"crs": "EPSG:4326"}
        )

        class Config:
            coerce = False
            strict = False

        @pa.check("geometry", error="Geometry must be Points.")
        def _points_only(self, series: GeoSeries[Geometry]) -> Series[bool]:
            return series.geom_type == "Point"

    return PointsGeoDataFrameModel


def _build_polygons_schema() -> type[pa.DataFrameModel]:
    import pandera.pandas as pa
    from pandera.typing import Series
    from pandera.typing.geopandas import Geometry, GeoSeries

    globals().update({"Series": Series, "GeoSeries": GeoSeries, "Geometry": Geometry})

    class PolygonsGeoDataFrameModel(pa.DataFrameModel):
        """Pandera schema for polygon geometries."""

        geometry: GeoSeries[Geometry] = pa.Field(
            nullable=False, dtype_kwargs={"crs": "EPSG:4326"}
        )

        class Config:
            coerce = False
            strict = False

        @pa.check("geometry", error="Geometry must be Polygon or MultiPolygon.")
        def _polygon_only(self, series: GeoSeries[Geometry]) -> Series[bool]:
            return series.geom_type.isin(["Polygon", "MultiPolygon"])

    return PolygonsGeoDataFrameModel


def _build_paths_schema() -> type[pa.DataFrameModel]:
    import pandera.pandas as pa
    from pandera.typing import Series
    from pandera.typing.geopandas import Geometry, GeoSeries

    globals().update({"Series": Series, "GeoSeries": GeoSeries, "Geometry": Geometry})

    class PathsGeoDataFrameModel(pa.DataFrameModel):
        """Pandera schema for path geometries."""

        geometry: GeoSeries[Geometry] = pa.Field(
            nullable=False, dtype_kwargs={"crs": "EPSG:4326"}
        )

        class Config:
            coerce = False
            strict = False

        @pa.check("geometry", error="Geometry must be LineString or MultiLineString.")
        def _line_only(self, series: GeoSeries[Geometry]) -> Series[bool]:
            return series.geom_type.isin(["LineString", "MultiLineString"])

    return PathsGeoDataFrameModel


def _require_columns(gdf: gpd.GeoDataFrame, columns: Iterable[str]) -> None:
    missing = [col for col in columns if col not in gdf.columns]
    if missing:
        raise ValueError(f"GeoDataFrame missing columns: {missing}")


def _prepare_point_gdf(
    gdf: gpd.GeoDataFrame,
    *,
    geometry_column: str | None,
    default_column: str,
    context: str,
) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        raise ValueError("GeoDataFrame must have a CRS to convert to EPSG:4326.")

    if geometry_column is None and default_column in gdf.columns:
        resolved_geometry = default_column
    else:
        resolved_geometry = geometry_column or gdf.geometry.name
    geometry_name = str(resolved_geometry)
    gdf = gdf.set_geometry(geometry_name, inplace=False)
    if geometry_name != "geometry":
        gdf = gdf.rename(columns={geometry_name: "geometry"}).set_geometry(
            "geometry", inplace=False
        )
    if not gdf.geometry.geom_type.eq("Point").all():
        raise ValueError("Geometry column must contain Point geometries.")
    gdf = gdf.to_crs(4326)
    try:
        gdf = _build_points_schema().validate(gdf)
    except Exception as exc:
        _handle_schema_error(exc, f"GeoDataFrame failed {context} schema validation.")
    return gdf


def polygons_from_gdf(
    gdf: gpd.GeoDataFrame,
    *,
    geometry_column: str | None = None,
    include_columns: Iterable[str] | None = None,
) -> list[PolygonDatum]:
    """Convert a GeoDataFrame of polygon geometries into polygon data models.

    Args:
        gdf: GeoDataFrame containing polygon geometries.
        geometry_column: Optional name of the geometry column to use.
        include_columns: Optional iterable of column names to copy onto each polygon.

    Returns:
        A list of PolygonDatum models with a GeoJSON geometry plus any requested
        attributes.

    Raises:
        ValueError: If the GeoDataFrame has no CRS or contains non-polygon geometries.
    """
    _require_geopandas()
    _require_pandas()
    _require_pandera()

    if gdf.crs is None:
        raise ValueError("GeoDataFrame must have a CRS to convert to EPSG:4326.")

    if geometry_column is None and "polygons" in gdf.columns:
        resolved_geometry = "polygons"
    else:
        resolved_geometry = geometry_column or gdf.geometry.name
    gdf = gdf.set_geometry(resolved_geometry, inplace=False)
    if resolved_geometry != "geometry":
        gdf = gdf.rename(columns={resolved_geometry: "geometry"}).set_geometry(
            "geometry", inplace=False
        )
    if not gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"]).all():
        raise ValueError("Geometry column must contain Polygon or MultiPolygon.")

    gdf = gdf.to_crs(4326)
    try:
        gdf = _build_polygons_schema().validate(gdf)
    except Exception as exc:
        _handle_schema_error(exc, "polygons_from_gdf schema validation failed.")

    columns = list(include_columns) if include_columns is not None else []
    missing = [col for col in columns if col not in gdf.columns]
    if missing:
        raise ValueError(f"GeoDataFrame missing columns: {missing}")

    optional_columns = {
        "name",
        "label",
        "cap_color",
        "side_color",
        "stroke_color",
        "altitude",
        "cap_curvature_resolution",
    }
    validation_columns = set(columns)
    validation_columns.update(col for col in optional_columns if col in gdf.columns)
    # Pandera's PydanticModel schema must only contain model fields, so validate a
    # subset that matches the Pydantic model.
    validation = (
        gdf[list(validation_columns)].copy()
        if validation_columns
        else gdf.iloc[:, 0:0].copy()
    )
    validation["geometry"] = [_to_geojson_polygon_model(geom) for geom in gdf.geometry]
    _validate_rows_with_pydantic(validation, PolygonDatum, "polygons_from_gdf")

    data = gdf[columns].copy() if columns else gdf.iloc[:, 0:0].copy()
    data["geometry"] = [_to_geojson_polygon_model(geom) for geom in gdf.geometry]
    return [PolygonDatum.model_validate(record) for record in data.to_dict("records")]


def _handle_schema_error(exc: Exception, message: str) -> None:
    details = str(exc)
    if "Error while coercing" in details and "float" in details:
        details = f"column must be numeric. {details}"
    if "expected series" in details and "type str" in details:
        details = f"column must be strings. {details}"
    raise ValueError(f"{message} ({details})") from exc


def _validate_rows_with_pydantic(
    data: pd.DataFrame, model: type[BaseModel], context: str
) -> None:
    from pandera.engines.pandas_engine import PydanticModel
    import pandera.pandas as pa
    from pydantic import ValidationError

    schema = pa.DataFrameSchema(dtype=PydanticModel(model), coerce=False)
    try:
        schema.validate(data)
    except Exception as exc:
        records = data.to_dict("records")
        for record in records:
            try:
                model.model_validate(record)
            except ValidationError as val_exc:  # noqa: PERF203 - clarity over micro-optimization
                error = val_exc.errors()[0]
                location = ".".join(str(item) for item in error.get("loc", []))
                message = error.get("msg", "Invalid value.")
                detail = f"{location}: {message}" if location else message
                raise ValueError(
                    f"{context} schema validation failed. ({detail})"
                ) from val_exc
        raise ValueError(f"{context} schema validation failed.") from exc


def _to_geojson_polygon_model(geom: BaseGeometry):
    from geojson_pydantic import MultiPolygon, Polygon
    from shapely.geometry import MultiPolygon as ShapelyMultiPolygon
    from shapely.ops import orient

    if geom.geom_type == "Polygon":
        geom = orient(geom, sign=1.0)
    elif geom.geom_type == "MultiPolygon":
        geom = ShapelyMultiPolygon([orient(part, sign=1.0) for part in geom.geoms])
    mapping = geom.__geo_interface__
    if mapping.get("type") == "Polygon":
        return Polygon.model_validate(mapping)
    if mapping.get("type") == "MultiPolygon":
        return MultiPolygon.model_validate(mapping)
    raise ValueError("Geometry column must contain Polygon or MultiPolygon.")


def points_from_gdf(
    gdf: gpd.GeoDataFrame,
    *,
    include_columns: Iterable[str] | None = None,
    point_geometry: str | None = None,
) -> list[PointDatum]:
    """Convert a GeoDataFrame of point geometries into point data models.

    Args:
        gdf: GeoDataFrame containing point geometries.
        include_columns: Optional iterable of column names to copy onto each point.
        point_geometry: Optional name of the point geometry column to use.

    Returns:
        A list of PointDatum models with ``lat`` and ``lng`` plus any requested
        attributes.

    Raises:
        ValueError: If the GeoDataFrame has no CRS or contains no point geometries.
    """
    _require_geopandas()
    _require_pandas()
    _require_pandera()

    if gdf.crs is None:
        raise ValueError("GeoDataFrame must have a CRS to convert to EPSG:4326.")

    if point_geometry is None and "point" in gdf.columns:
        resolved_geometry = "point"
    else:
        resolved_geometry = point_geometry or gdf.geometry.name
    geometry_name = str(resolved_geometry)
    gdf = gdf.set_geometry(geometry_name, inplace=False)
    if geometry_name != "geometry":
        gdf = gdf.rename(columns={geometry_name: "geometry"}).set_geometry(
            "geometry", inplace=False
        )
    if not gdf.geometry.geom_type.eq("Point").all():
        raise ValueError("Geometry column must contain Point geometries.")
    gdf = gdf.to_crs(4326)
    try:
        gdf = _build_points_schema().validate(gdf)
    except Exception as exc:
        _handle_schema_error(exc, "GeoDataFrame failed point schema validation.")

    columns = list(include_columns) if include_columns is not None else []
    missing = [col for col in columns if col not in gdf.columns]
    if missing:
        raise ValueError(f"GeoDataFrame missing columns: {missing}")

    optional_columns = {"altitude", "radius", "color", "label"}
    validation_columns = set(columns)
    validation_columns.update(col for col in optional_columns if col in gdf.columns)
    # Pandera's PydanticModel schema must only contain model fields, so validate a
    # subset that matches the Pydantic model.
    validation = (
        gdf[list(validation_columns)].copy()
        if validation_columns
        else gdf.iloc[:, 0:0].copy()
    )
    validation["lat"] = gdf.geometry.y
    validation["lng"] = gdf.geometry.x
    _validate_rows_with_pydantic(validation, PointDatum, "points_from_gdf")

    data = gdf[columns].copy() if columns else gdf.iloc[:, 0:0].copy()
    data["lat"] = gdf.geometry.y
    data["lng"] = gdf.geometry.x
    return [PointDatum.model_validate(record) for record in data.to_dict("records")]


def arcs_from_gdf(
    gdf: gpd.GeoDataFrame,
    *,
    start_geometry: str = "start",
    end_geometry: str = "end",
    include_columns: Iterable[str] | None = None,
) -> list[ArcDatum]:
    """Convert a GeoDataFrame into arc data models.

    Geometry columns are reprojected to EPSG:4326 before extracting lat/lng.

    Args:
        gdf: GeoDataFrame containing arc columns.
        start_geometry: Column name for start point geometries.
        end_geometry: Column name for end point geometries.
        include_columns: Optional iterable of column names to copy onto each arc.

    Returns:
        A list of ArcDatum models with start/end coordinates plus any requested
        attributes.

    Raises:
        ValueError: If required columns are missing or schema validation fails.
    """
    _require_geopandas()
    _require_pandas()
    _require_pandera()
    import geopandas as gpd

    if gdf.crs is None:
        raise ValueError("GeoDataFrame must have a CRS to convert to EPSG:4326.")

    required_columns = {start_geometry, end_geometry}
    missing = [col for col in required_columns if col not in gdf.columns]
    if missing:
        raise ValueError(f"GeoDataFrame missing columns: {sorted(missing)}")

    start_series = gpd.GeoSeries(gdf[start_geometry], crs=gdf.crs)
    end_series = gpd.GeoSeries(gdf[end_geometry], crs=gdf.crs)
    if not start_series.geom_type.eq("Point").all():
        raise ValueError("start_geometry column must contain Point geometries.")
    if not end_series.geom_type.eq("Point").all():
        raise ValueError("end_geometry column must contain Point geometries.")

    start_series = start_series.to_crs(4326)
    end_series = end_series.to_crs(4326)

    renamed = gdf.copy()
    renamed["start_lat"] = start_series.y
    renamed["start_lng"] = start_series.x
    renamed["end_lat"] = end_series.y
    renamed["end_lng"] = end_series.x

    columns = list(include_columns) if include_columns is not None else []
    missing_extra = [col for col in columns if col not in renamed.columns]
    if missing_extra:
        raise ValueError(f"GeoDataFrame missing columns: {missing_extra}")

    optional_columns = {
        "start_altitude",
        "end_altitude",
        "altitude",
        "altitude_auto_scale",
        "stroke",
        "dash_length",
        "dash_gap",
        "dash_initial_gap",
        "dash_animate_time",
        "color",
        "label",
    }
    validation_columns = set(columns)
    validation_columns.update(col for col in optional_columns if col in renamed.columns)
    # Pandera's PydanticModel schema must only contain model fields, so validate a
    # subset that matches the Pydantic model.
    validation = (
        renamed[list(validation_columns)].copy()
        if validation_columns
        else renamed.iloc[:, 0:0].copy()
    )
    validation["start_lat"] = renamed["start_lat"]
    validation["start_lng"] = renamed["start_lng"]
    validation["end_lat"] = renamed["end_lat"]
    validation["end_lng"] = renamed["end_lng"]
    _validate_rows_with_pydantic(validation, ArcDatum, "arcs_from_gdf")

    data = renamed[columns].copy() if columns else renamed.iloc[:, 0:0].copy()
    data["start_lat"] = renamed["start_lat"]
    data["start_lng"] = renamed["start_lng"]
    data["end_lat"] = renamed["end_lat"]
    data["end_lng"] = renamed["end_lng"]
    return [ArcDatum.model_validate(record) for record in data.to_dict("records")]


def paths_from_gdf(
    gdf: gpd.GeoDataFrame,
    *,
    geometry_column: str | None = None,
    include_columns: Iterable[str] | None = None,
) -> list[PathDatum]:
    """Convert a GeoDataFrame of line geometries into path data models.

    Args:
        gdf: GeoDataFrame containing line geometries.
        geometry_column: Optional name of the geometry column to use.
        include_columns: Optional iterable of column names to copy onto each path.

    Returns:
        A list of PathDatum models with a list of coordinates plus any requested
        attributes.

    Raises:
        ValueError: If the GeoDataFrame has no CRS or contains non-line geometries.
    """
    _require_geopandas()
    _require_pandas()
    _require_pandera()
    import pandas as pd

    if gdf.crs is None:
        raise ValueError("GeoDataFrame must have a CRS to convert to EPSG:4326.")

    if geometry_column is None and "paths" in gdf.columns:
        resolved_geometry = "paths"
    else:
        resolved_geometry = geometry_column or gdf.geometry.name
    gdf = gdf.set_geometry(resolved_geometry, inplace=False)
    if resolved_geometry != "geometry":
        gdf = gdf.rename(columns={resolved_geometry: "geometry"}).set_geometry(
            "geometry", inplace=False
        )
    if not gdf.geometry.geom_type.isin(["LineString", "MultiLineString"]).all():
        raise ValueError("Geometry column must contain LineString or MultiLineString.")

    gdf = gdf.to_crs(4326)
    try:
        gdf = _build_paths_schema().validate(gdf)
    except Exception as exc:
        _handle_schema_error(exc, "GeoDataFrame failed path schema validation.")

    columns = list(include_columns) if include_columns is not None else []
    missing = [col for col in columns if col not in gdf.columns]
    if missing:
        raise ValueError(f"GeoDataFrame missing columns: {missing}")

    optional_columns = {
        "color",
        "dash_length",
        "dash_gap",
        "dash_initial_gap",
        "dash_animate_time",
        "label",
        "name",
    }
    validation_columns = set(columns)
    validation_columns.update(col for col in optional_columns if col in gdf.columns)
    # Pandera's PydanticModel schema must only contain model fields, so validate a
    # subset that matches the Pydantic model.
    validation_records = _expand_path_records(gdf, list(validation_columns))
    data_records = _expand_path_records(gdf, columns)

    if validation_records:
        validation_df = pd.DataFrame(validation_records)
    else:
        validation_df = pd.DataFrame(columns=[*validation_columns, "path"])
    _validate_rows_with_pydantic(validation_df, PathDatum, "paths_from_gdf")

    return [PathDatum.model_validate(record) for record in data_records]


def heatmaps_from_gdf(
    gdf: gpd.GeoDataFrame,
    *,
    geometry_column: str | None = None,
    weight_column: str | None = None,
    bandwidth: float | None = None,
    color_saturation: float | None = None,
    base_altitude: float | None = None,
    top_altitude: float | None = None,
) -> list[HeatmapDatum]:
    """Convert a GeoDataFrame of point geometries into heatmap data models.

    Args:
        gdf: GeoDataFrame containing point geometries.
        geometry_column: Optional name of the geometry column to use.
        weight_column: Optional column name for per-point weights.
        bandwidth: Optional heatmap bandwidth override.
        color_saturation: Optional heatmap color saturation override.
        base_altitude: Optional heatmap base altitude override.
        top_altitude: Optional heatmap top altitude override.

    Returns:
        A list containing a single HeatmapDatum with a list of points.

    """
    _require_geopandas()
    _require_pandas()
    _require_pandera()

    gdf = _prepare_point_gdf(
        gdf, geometry_column=geometry_column, default_column="point", context="heatmap"
    )

    weight_series = None
    if weight_column is not None:
        _require_columns(gdf, [weight_column])
        weight_series = gdf[weight_column]

    validation = gdf.iloc[:, 0:0].copy()
    validation["lat"] = gdf.geometry.y
    validation["lng"] = gdf.geometry.x
    validation["weight"] = weight_series if weight_series is not None else 1.0
    _validate_rows_with_pydantic(validation, HeatmapPointDatum, "heatmaps_from_gdf")

    point_records = validation[["lat", "lng", "weight"]].to_dict("records")
    points = [HeatmapPointDatum.model_validate(record) for record in point_records]

    heatmap_payload: dict[str, object] = {"points": points}
    if bandwidth is not None:
        heatmap_payload["bandwidth"] = bandwidth
    if color_saturation is not None:
        heatmap_payload["color_saturation"] = color_saturation
    if base_altitude is not None:
        heatmap_payload["base_altitude"] = base_altitude
    if top_altitude is not None:
        heatmap_payload["top_altitude"] = top_altitude

    return [HeatmapDatum.model_validate(heatmap_payload)]


def hexed_polygons_from_gdf(
    gdf: gpd.GeoDataFrame,
    *,
    geometry_column: str | None = None,
    include_columns: Iterable[str] | None = None,
) -> list[HexPolygonDatum]:
    """Convert a GeoDataFrame of polygon geometries into hexed polygon data models.

    Args:
        gdf: GeoDataFrame containing polygon geometries.
        geometry_column: Optional name of the geometry column to use.
        include_columns: Optional iterable of column names to copy onto each polygon.

    Returns:
        A list of HexPolygonDatum models.

    Raises:
        ValueError: If the GeoDataFrame is missing CRS or polygon geometry.
    """
    _require_geopandas()
    _require_pandas()
    _require_pandera()

    if gdf.crs is None:
        raise ValueError("GeoDataFrame must have a CRS to convert to EPSG:4326.")

    if geometry_column is None and "polygons" in gdf.columns:
        resolved_geometry = "polygons"
    else:
        resolved_geometry = geometry_column or gdf.geometry.name
    gdf = gdf.set_geometry(resolved_geometry, inplace=False)
    if resolved_geometry != "geometry":
        gdf = gdf.rename(columns={resolved_geometry: "geometry"}).set_geometry(
            "geometry", inplace=False
        )
    if not gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"]).all():
        raise ValueError("Geometry column must contain Polygon or MultiPolygon.")

    gdf = gdf.to_crs(4326)
    try:
        gdf = _build_polygons_schema().validate(gdf)
    except Exception as exc:
        _handle_schema_error(exc, "hexed_polygons_from_gdf schema validation failed.")

    columns = list(include_columns) if include_columns is not None else []
    missing = [col for col in columns if col not in gdf.columns]
    if missing:
        raise ValueError(f"GeoDataFrame missing columns: {missing}")

    optional_columns = {
        "label",
        "color",
        "altitude",
        "resolution",
        "margin",
        "use_dots",
        "curvature_resolution",
        "dot_resolution",
    }
    validation_columns = set(columns)
    validation_columns.update(col for col in optional_columns if col in gdf.columns)
    validation = (
        gdf[list(validation_columns)].copy()
        if validation_columns
        else gdf.iloc[:, 0:0].copy()
    )
    validation["geometry"] = [_to_geojson_polygon_model(geom) for geom in gdf.geometry]
    _validate_rows_with_pydantic(validation, HexPolygonDatum, "hexed_polygons_from_gdf")

    data = gdf[columns].copy() if columns else gdf.iloc[:, 0:0].copy()
    data["geometry"] = [_to_geojson_polygon_model(geom) for geom in gdf.geometry]
    return [
        HexPolygonDatum.model_validate(record) for record in data.to_dict("records")
    ]


def tiles_from_gdf(
    gdf: gpd.GeoDataFrame,
    *,
    geometry_column: str | None = None,
    include_columns: Iterable[str] | None = None,
) -> list[TileDatum]:
    """Convert a GeoDataFrame of point geometries into tile data models.

    Args:
        gdf: GeoDataFrame containing point geometries.
        geometry_column: Optional name of the geometry column to use.
        include_columns: Optional iterable of column names to copy onto each tile.

    Returns:
        A list of TileDatum models.

    Raises:
        ValueError: If the GeoDataFrame is missing CRS or point geometry.
    """
    _require_geopandas()
    _require_pandas()
    _require_pandera()

    if gdf.crs is None:
        raise ValueError("GeoDataFrame must have a CRS to convert to EPSG:4326.")

    if geometry_column is None and "point" in gdf.columns:
        resolved_geometry = "point"
    else:
        resolved_geometry = geometry_column or gdf.geometry.name
    geometry_name = str(resolved_geometry)
    gdf = gdf.set_geometry(geometry_name, inplace=False)
    if geometry_name != "geometry":
        gdf = gdf.rename(columns={geometry_name: "geometry"}).set_geometry(
            "geometry", inplace=False
        )
    if not gdf.geometry.geom_type.eq("Point").all():
        raise ValueError("Geometry column must contain Point geometries.")
    gdf = gdf.to_crs(4326)
    try:
        gdf = _build_points_schema().validate(gdf)
    except Exception as exc:
        _handle_schema_error(exc, "GeoDataFrame failed tiles schema validation.")

    columns = list(include_columns) if include_columns is not None else []
    missing = [col for col in columns if col not in gdf.columns]
    if missing:
        raise ValueError(f"GeoDataFrame missing columns: {missing}")

    optional_columns = {
        "altitude",
        "width",
        "height",
        "use_globe_projection",
        "curvature_resolution",
        "label",
    }
    validation_columns = set(columns)
    validation_columns.update(col for col in optional_columns if col in gdf.columns)
    validation = (
        gdf[list(validation_columns)].copy()
        if validation_columns
        else gdf.iloc[:, 0:0].copy()
    )
    validation["lat"] = gdf.geometry.y
    validation["lng"] = gdf.geometry.x
    _validate_rows_with_pydantic(validation, TileDatum, "tiles_from_gdf")

    data = gdf[columns].copy() if columns else gdf.iloc[:, 0:0].copy()
    data["lat"] = gdf.geometry.y
    data["lng"] = gdf.geometry.x
    return [TileDatum.model_validate(record) for record in data.to_dict("records")]


def particles_from_gdf(
    gdf: gpd.GeoDataFrame,
    *,
    geometry_column: str | None = None,
    altitude_column: str | None = None,
    size: float | None = None,
    size_attenuation: bool | None = None,
    color: str | None = None,
    texture: str | None = None,
    label: str | None = None,
) -> list[ParticleDatum]:
    """Convert a GeoDataFrame of point geometries into particles data models.

    Returns a single ParticleDatum containing all points.

    Args:
        gdf: GeoDataFrame containing point geometries.
        geometry_column: Optional name of the geometry column to use.
        altitude_column: Optional column name for per-point altitudes.
        size: Optional particle size override.
        size_attenuation: Optional size attenuation override.
        color: Optional color override.
        texture: Optional texture URL or data URI.
        label: Optional label for tooltips.

    Returns:
        A list containing a single ParticleDatum with a list of points.

    """
    _require_geopandas()
    _require_pandas()
    _require_pandera()

    gdf = _prepare_point_gdf(
        gdf,
        geometry_column=geometry_column,
        default_column="point",
        context="particles",
    )

    altitude_series = None
    if altitude_column is not None:
        _require_columns(gdf, [altitude_column])
        altitude_series = gdf[altitude_column]

    validation = gdf.iloc[:, 0:0].copy()
    validation["lat"] = gdf.geometry.y
    validation["lng"] = gdf.geometry.x
    validation["altitude"] = altitude_series if altitude_series is not None else 0.01
    _validate_rows_with_pydantic(validation, ParticlePointDatum, "particles_from_gdf")

    point_records = validation[["lat", "lng", "altitude"]].to_dict("records")
    points = [ParticlePointDatum.model_validate(record) for record in point_records]

    payload: dict[str, object] = {"particles": points}
    if size is not None:
        payload["size"] = size
    if size_attenuation is not None:
        payload["size_attenuation"] = size_attenuation
    if color is not None:
        payload["color"] = color
    if texture is not None:
        payload["texture"] = texture
    if label is not None:
        payload["label"] = label

    return [ParticleDatum.model_validate(payload)]


def rings_from_gdf(
    gdf: gpd.GeoDataFrame,
    *,
    geometry_column: str | None = None,
    include_columns: Iterable[str] | None = None,
) -> list[RingDatum]:
    """Convert a GeoDataFrame of point geometries into ring data models.

    Args:
        gdf: GeoDataFrame containing point geometries.
        geometry_column: Optional name of the geometry column to use.
        include_columns: Optional iterable of column names to copy onto each ring.

    Returns:
        A list of RingDatum models.

    Raises:
        ValueError: If the GeoDataFrame is missing CRS or point geometry.
    """
    _require_geopandas()
    _require_pandas()
    _require_pandera()

    if gdf.crs is None:
        raise ValueError("GeoDataFrame must have a CRS to convert to EPSG:4326.")

    if geometry_column is None and "point" in gdf.columns:
        resolved_geometry = "point"
    else:
        resolved_geometry = geometry_column or gdf.geometry.name
    geometry_name = str(resolved_geometry)
    gdf = gdf.set_geometry(geometry_name, inplace=False)
    if geometry_name != "geometry":
        gdf = gdf.rename(columns={geometry_name: "geometry"}).set_geometry(
            "geometry", inplace=False
        )
    if not gdf.geometry.geom_type.eq("Point").all():
        raise ValueError("Geometry column must contain Point geometries.")
    gdf = gdf.to_crs(4326)
    try:
        gdf = _build_points_schema().validate(gdf)
    except Exception as exc:
        _handle_schema_error(exc, "GeoDataFrame failed rings schema validation.")

    columns = list(include_columns) if include_columns is not None else []
    missing = [col for col in columns if col not in gdf.columns]
    if missing:
        raise ValueError(f"GeoDataFrame missing columns: {missing}")

    optional_columns = {
        "altitude",
        "color",
        "max_radius",
        "propagation_speed",
        "repeat_period",
    }
    validation_columns = set(columns)
    validation_columns.update(col for col in optional_columns if col in gdf.columns)
    validation = (
        gdf[list(validation_columns)].copy()
        if validation_columns
        else gdf.iloc[:, 0:0].copy()
    )
    validation["lat"] = gdf.geometry.y
    validation["lng"] = gdf.geometry.x
    _validate_rows_with_pydantic(validation, RingDatum, "rings_from_gdf")

    data = gdf[columns].copy() if columns else gdf.iloc[:, 0:0].copy()
    data["lat"] = gdf.geometry.y
    data["lng"] = gdf.geometry.x
    return [RingDatum.model_validate(record) for record in data.to_dict("records")]


def labels_from_gdf(
    gdf: gpd.GeoDataFrame,
    *,
    text_column: str = "text",
    geometry_column: str | None = None,
    include_columns: Iterable[str] | None = None,
) -> list[LabelDatum]:
    """Convert a GeoDataFrame of point geometries into label data models.

    Args:
        gdf: GeoDataFrame containing point geometries.
        text_column: Column name containing label text.
        geometry_column: Optional name of the geometry column to use.
        include_columns: Optional iterable of column names to copy onto each label.

    Returns:
        A list of LabelDatum models.

    Raises:
        ValueError: If required columns are missing or geometry is invalid.
    """
    _require_geopandas()
    _require_pandas()
    _require_pandera()

    if gdf.crs is None:
        raise ValueError("GeoDataFrame must have a CRS to convert to EPSG:4326.")

    if text_column not in gdf.columns:
        raise ValueError(f"GeoDataFrame missing columns: {[text_column]}")

    if geometry_column is None and "point" in gdf.columns:
        resolved_geometry = "point"
    else:
        resolved_geometry = geometry_column or gdf.geometry.name
    geometry_name = str(resolved_geometry)
    gdf = gdf.set_geometry(geometry_name, inplace=False)
    if geometry_name != "geometry":
        gdf = gdf.rename(columns={geometry_name: "geometry"}).set_geometry(
            "geometry", inplace=False
        )
    if not gdf.geometry.geom_type.eq("Point").all():
        raise ValueError("Geometry column must contain Point geometries.")
    gdf = gdf.to_crs(4326)
    try:
        gdf = _build_points_schema().validate(gdf)
    except Exception as exc:
        _handle_schema_error(exc, "GeoDataFrame failed labels schema validation.")

    columns = list(include_columns) if include_columns is not None else []
    missing = [col for col in columns if col not in gdf.columns]
    if missing:
        raise ValueError(f"GeoDataFrame missing columns: {missing}")

    optional_columns = {
        "altitude",
        "size",
        "rotation",
        "color",
        "include_dot",
        "dot_radius",
        "dot_orientation",
        "label",
    }
    validation_columns = set(columns)
    validation_columns.add(text_column)
    validation_columns.update(col for col in optional_columns if col in gdf.columns)
    validation = (
        gdf[list(validation_columns)].copy()
        if validation_columns
        else gdf.iloc[:, 0:0].copy()
    )
    validation = validation.rename(columns={text_column: "text"})
    validation["lat"] = gdf.geometry.y
    validation["lng"] = gdf.geometry.x
    _validate_rows_with_pydantic(validation, LabelDatum, "labels_from_gdf")

    data = gdf[columns].copy() if columns else gdf.iloc[:, 0:0].copy()
    data["text"] = gdf[text_column]
    data["lat"] = gdf.geometry.y
    data["lng"] = gdf.geometry.x
    return [LabelDatum.model_validate(record) for record in data.to_dict("records")]


def _to_path_coordinate_groups(
    geom: BaseGeometry,
) -> list[list[tuple[float, float] | tuple[float, float, float]]]:
    def _is_xyz(
        coord: tuple[float, float] | tuple[float, float, float],
    ) -> TypeGuard[tuple[float, float, float]]:
        return len(coord) == 3

    def _swap_xy(
        coord: tuple[float, float] | tuple[float, float, float],
    ) -> tuple[float, float] | tuple[float, float, float]:
        if _is_xyz(coord):
            return (coord[1], coord[0], coord[2])
        return (coord[1], coord[0])

    if geom.geom_type == "LineString":
        return [[_swap_xy(coord) for coord in geom.coords]]
    if geom.geom_type == "MultiLineString":
        return [[_swap_xy(coord) for coord in part.coords] for part in geom.geoms]
    raise ValueError("Geometry must be LineString or MultiLineString.")


def _expand_path_records(
    gdf: gpd.GeoDataFrame, columns: Sequence[str]
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for idx, geom in enumerate(gdf.geometry):
        base = {col: gdf.iloc[idx][col] for col in columns} if columns else {}
        for path in _to_path_coordinate_groups(geom):
            record = dict(base)
            record["path"] = path
            records.append(record)
    return records
