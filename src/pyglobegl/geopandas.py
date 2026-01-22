"""GeoPandas helpers for pyglobegl."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, TYPE_CHECKING

import pandas as pd
from pandera.errors import SchemaError
import pandera.pandas as pa
from pandera.typing import Series
from pandera.typing.geopandas import Geometry, GeoSeries


if TYPE_CHECKING:
    import geopandas as gpd


class PointsGeoDataFrameModel(pa.DataFrameModel):
    """Pandera schema for point geometries."""

    geometry: GeoSeries[Geometry] = pa.Field(
        nullable=False, dtype_kwargs={"crs": "EPSG:4326"}
    )
    altitude: Series[float] | None = pa.Field(nullable=True)
    radius: Series[float] | None = pa.Field(nullable=True)
    size: Series[float] | None = pa.Field(nullable=True)
    color: Series[str] | None = pa.Field(nullable=True, coerce=False)
    label: Series[str] | None = pa.Field(nullable=True, coerce=False)

    class Config:
        coerce = True
        strict = False

    @pa.check("geometry", error="Geometry must be Points.")
    def _points_only(self, series: GeoSeries[Geometry]) -> Series[bool]:
        return series.geom_type == "Point"


class ArcsGeoDataFrameModel(pa.DataFrameModel):
    """Pandera schema for arcs layer data."""

    start_lat: Series[float] = pa.Field(in_range={"min_value": -90, "max_value": 90})
    start_lng: Series[float] = pa.Field(in_range={"min_value": -180, "max_value": 180})
    end_lat: Series[float] = pa.Field(in_range={"min_value": -90, "max_value": 90})
    end_lng: Series[float] = pa.Field(in_range={"min_value": -180, "max_value": 180})
    altitude: Series[float] | None = pa.Field(nullable=True)
    altitude_auto_scale: Series[float] | None = pa.Field(nullable=True)
    stroke: Series[float] | None = pa.Field(nullable=True)
    dash_length: Series[float] | None = pa.Field(nullable=True)
    dash_gap: Series[float] | None = pa.Field(nullable=True)
    dash_initial_gap: Series[float] | None = pa.Field(nullable=True)
    dash_animate_time: Series[float] | None = pa.Field(nullable=True)
    color: Series[str] | None = pa.Field(nullable=True, coerce=False)
    label: Series[str] | None = pa.Field(nullable=True, coerce=False)

    class Config:
        coerce = True
        strict = False


def _ensure_numeric(df: Any, column: str, context: str) -> None:
    series = df[column]
    coerced = pd.to_numeric(series, errors="coerce")
    if coerced.isna().ne(series.isna()).any():
        raise ValueError(f"{context} column '{column}' must be numeric.")


def _ensure_positive(df: Any, column: str, context: str) -> None:
    series = pd.to_numeric(df[column], errors="coerce")
    if series.dropna().le(0).any():
        raise ValueError(f"{context} column '{column}' must be positive.")


def _ensure_strings(df: Any, column: str, context: str) -> None:
    series = df[column].dropna()
    if not series.map(type).eq(str).all():
        raise ValueError(f"{context} column '{column}' must be strings.")


def _validate_optional_columns(
    df: Any,
    *,
    numeric_columns: Iterable[str],
    positive_columns: Iterable[str],
    string_columns: Iterable[str],
    context: str,
) -> None:
    for column in numeric_columns:
        if column in df.columns:
            _ensure_numeric(df, column, context)
    for column in positive_columns:
        if column in df.columns:
            _ensure_positive(df, column, context)
    for column in string_columns:
        if column in df.columns:
            _ensure_strings(df, column, context)


def _require_geopandas() -> None:
    try:
        import geopandas as gpd  # noqa: F401
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "GeoPandas is required for pyglobegl GeoDataFrame helpers. "
            "Install with `uv add pyglobegl[geopandas]`."
        ) from exc


def _handle_schema_error(exc: SchemaError, message: str) -> None:
    details = str(exc)
    raise ValueError(f"{message} ({details})") from exc


def points_from_gdf(
    gdf: gpd.GeoDataFrame,
    *,
    include_columns: Iterable[str] | None = None,
    geometry_column: str | None = None,
) -> list[dict[str, Any]]:
    """Convert a GeoDataFrame of point geometries into globe.gl point data.

    Args:
        gdf: GeoDataFrame containing point geometries.
        include_columns: Optional iterable of column names to copy onto each point.
        geometry_column: Optional name of the geometry column to use.

    Returns:
        A list of point dictionaries with ``lat`` and ``lng`` keys plus any
        requested attributes.

    Raises:
        ValueError: If the GeoDataFrame has no CRS or contains no point geometries.
    """
    _require_geopandas()

    if gdf.crs is None:
        raise ValueError("GeoDataFrame must have a CRS to convert to EPSG:4326.")

    resolved_geometry = (
        geometry_column if geometry_column is not None else gdf.geometry.name
    )
    geometry_name = str(resolved_geometry)
    gdf = gdf.set_geometry(geometry_name, inplace=False)
    if geometry_name != "geometry":
        gdf = gdf.rename(columns={geometry_name: "geometry"}).set_geometry(
            "geometry", inplace=False
        )
    gdf = gdf.to_crs(4326)
    _validate_optional_columns(
        gdf,
        numeric_columns=("altitude", "radius", "size"),
        positive_columns=("altitude", "radius", "size"),
        string_columns=("color", "label"),
        context="points_from_gdf",
    )
    try:
        gdf = PointsGeoDataFrameModel.validate(gdf)
    except SchemaError as exc:
        _handle_schema_error(exc, "GeoDataFrame failed point schema validation.")

    columns = list(include_columns) if include_columns is not None else []
    missing = [col for col in columns if col not in gdf.columns]
    if missing:
        raise ValueError(f"GeoDataFrame missing columns: {missing}")

    data = gdf[columns].copy() if columns else gdf.iloc[:, 0:0].copy()
    data["lat"] = gdf.geometry.y
    data["lng"] = gdf.geometry.x
    return data.to_dict("records")


def arcs_from_gdf(
    gdf: gpd.GeoDataFrame,
    *,
    start_lat: str = "start_lat",
    start_lng: str = "start_lng",
    end_lat: str = "end_lat",
    end_lng: str = "end_lng",
    include_columns: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Convert a GeoDataFrame into globe.gl arcs data.

    The start/end latitude/longitude columns are assumed to be in EPSG:4326.

    Args:
        gdf: GeoDataFrame containing arc columns.
        start_lat: Column name for start latitude.
        start_lng: Column name for start longitude.
        end_lat: Column name for end latitude.
        end_lng: Column name for end longitude.
        include_columns: Optional iterable of column names to copy onto each arc.

    Returns:
        A list of arc dictionaries with start/end coordinates plus any requested
        attributes.

    Raises:
        ValueError: If required columns are missing or schema validation fails.
    """
    _require_geopandas()

    required_columns = {start_lat, start_lng, end_lat, end_lng}
    missing = [col for col in required_columns if col not in gdf.columns]
    if missing:
        raise ValueError(f"GeoDataFrame missing columns: {sorted(missing)}")

    renamed = gdf.rename(
        columns={
            start_lat: "start_lat",
            start_lng: "start_lng",
            end_lat: "end_lat",
            end_lng: "end_lng",
        }
    )
    _validate_optional_columns(
        renamed,
        numeric_columns=(
            "altitude",
            "altitude_auto_scale",
            "stroke",
            "dash_length",
            "dash_gap",
            "dash_initial_gap",
            "dash_animate_time",
        ),
        positive_columns=(
            "altitude",
            "altitude_auto_scale",
            "stroke",
            "dash_length",
            "dash_gap",
            "dash_initial_gap",
            "dash_animate_time",
        ),
        string_columns=("color", "label"),
        context="arcs_from_gdf",
    )
    try:
        validated = ArcsGeoDataFrameModel.validate(renamed)
    except SchemaError as exc:
        _handle_schema_error(exc, "GeoDataFrame contains invalid arc coordinates.")

    columns = list(include_columns) if include_columns is not None else []
    missing_extra = [col for col in columns if col not in validated.columns]
    if missing_extra:
        raise ValueError(f"GeoDataFrame missing columns: {missing_extra}")

    data = validated[columns].copy() if columns else validated.iloc[:, 0:0].copy()
    data["startLat"] = validated["start_lat"]
    data["startLng"] = validated["start_lng"]
    data["endLat"] = validated["end_lat"]
    data["endLng"] = validated["end_lng"]
    return data.to_dict("records")
