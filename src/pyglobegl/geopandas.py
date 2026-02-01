"""GeoPandas helpers for pyglobegl."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

from pyglobegl.config import ArcDatum, PathDatum, PointDatum, PolygonDatum


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


def _to_path_coordinate_groups(
    geom: BaseGeometry,
) -> list[list[tuple[float, float] | tuple[float, float, float]]]:
    if geom.geom_type == "LineString":
        return [list(geom.coords)]
    if geom.geom_type == "MultiLineString":
        return [list(part.coords) for part in geom.geoms]
    raise ValueError("Geometry must be LineString or MultiLineString.")


def _expand_path_records(
    gdf: gpd.GeoDataFrame, columns: Sequence[str]
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for idx, geom in enumerate(gdf.geometry):
        base = {col: gdf.loc[idx, col] for col in columns} if columns else {}
        for path in _to_path_coordinate_groups(geom):
            record = dict(base)
            record["path"] = path
            records.append(record)
    return records
