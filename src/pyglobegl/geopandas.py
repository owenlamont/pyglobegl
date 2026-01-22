"""GeoPandas helpers for pyglobegl."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, TYPE_CHECKING


if TYPE_CHECKING:
    import geopandas as gpd
    import pandas as pd
    import pandera.pandas as pa
    from pandera.typing import Series
    from pandera.typing.geopandas import Geometry, GeoSeries


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

    return PointsGeoDataFrameModel


def _build_arcs_schema() -> type[pa.DataFrameModel]:
    import pandera.pandas as pa
    from pandera.typing import Series

    globals().update({"Series": Series})

    class ArcsGeoDataFrameModel(pa.DataFrameModel):
        """Pandera schema for arcs layer data."""

        start_lat: Series[float] = pa.Field(
            in_range={"min_value": -90, "max_value": 90}
        )
        start_lng: Series[float] = pa.Field(
            in_range={"min_value": -180, "max_value": 180}
        )
        end_lat: Series[float] = pa.Field(in_range={"min_value": -90, "max_value": 90})
        end_lng: Series[float] = pa.Field(
            in_range={"min_value": -180, "max_value": 180}
        )
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

    return ArcsGeoDataFrameModel


def _ensure_numeric(df: pd.DataFrame, column: str, context: str) -> None:
    import pandas as pd

    series = df[column]
    coerced = pd.to_numeric(series, errors="coerce")
    if coerced.isna().ne(series.isna()).any():
        raise ValueError(f"{context} column '{column}' must be numeric.")


def _ensure_positive(df: pd.DataFrame, column: str, context: str) -> None:
    import pandas as pd

    series = pd.to_numeric(df[column], errors="coerce")
    if series.dropna().le(0).any():
        raise ValueError(f"{context} column '{column}' must be positive.")


def _ensure_nonnegative(df: pd.DataFrame, column: str, context: str) -> None:
    import pandas as pd

    series = pd.to_numeric(df[column], errors="coerce")
    if series.dropna().lt(0).any():
        raise ValueError(f"{context} column '{column}' must be non-negative.")


def _ensure_strings(df: pd.DataFrame, column: str, context: str) -> None:
    series = df[column].dropna()
    if not series.map(type).eq(str).all():
        raise ValueError(f"{context} column '{column}' must be strings.")


def _css_color_names() -> set[str]:
    try:
        import webcolors
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "webcolors is required for color validation. "
            "Install with `uv add pyglobegl[geopandas]`."
        ) from exc
    return set(webcolors.names())


def _ensure_css_colors(df: pd.DataFrame, column: str, context: str) -> None:
    series = df[column].dropna()
    if series.empty:
        return
    if not series.map(type).eq(str).all():
        raise ValueError(f"{context} column '{column}' must be strings.")
    hex_match = series.str.match(
        r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$"
    )
    names = series.str.lower().isin(_css_color_names())
    if not (hex_match | names).all():
        raise ValueError(f"{context} column '{column}' must be valid CSS colors.")


def _validate_optional_columns(
    df: pd.DataFrame,
    *,
    numeric_columns: Iterable[str],
    positive_columns: Iterable[str],
    nonnegative_columns: Iterable[str],
    color_columns: Iterable[str],
    string_columns: Iterable[str],
    context: str,
) -> None:
    for column in numeric_columns:
        if column in df.columns:
            _ensure_numeric(df, column, context)
    for column in positive_columns:
        if column in df.columns:
            _ensure_positive(df, column, context)
    for column in nonnegative_columns:
        if column in df.columns:
            _ensure_nonnegative(df, column, context)
    for column in color_columns:
        if column in df.columns:
            _ensure_css_colors(df, column, context)
    for column in string_columns:
        if column in df.columns:
            _ensure_strings(df, column, context)


def _handle_schema_error(exc: Exception, message: str) -> None:
    details = str(exc)
    raise ValueError(f"{message} ({details})") from exc


def points_from_gdf(
    gdf: gpd.GeoDataFrame,
    *,
    include_columns: Iterable[str] | None = None,
    point_geometry: str | None = None,
) -> list[dict[str, Any]]:
    """Convert a GeoDataFrame of point geometries into globe.gl point data.

    Args:
        gdf: GeoDataFrame containing point geometries.
        include_columns: Optional iterable of column names to copy onto each point.
        point_geometry: Optional name of the point geometry column to use.

    Returns:
        A list of point dictionaries with ``lat`` and ``lng`` keys plus any
        requested attributes.

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
    _validate_optional_columns(
        gdf,
        numeric_columns=("altitude", "radius", "size"),
        positive_columns=("radius", "size"),
        nonnegative_columns=("altitude",),
        color_columns=("color",),
        string_columns=("label",),
        context="points_from_gdf",
    )
    try:
        gdf = _build_points_schema().validate(gdf)
    except Exception as exc:
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
    start_geometry: str = "start",
    end_geometry: str = "end",
    include_columns: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Convert a GeoDataFrame into globe.gl arcs data.

    Geometry columns are reprojected to EPSG:4326 before extracting lat/lng.

    Args:
        gdf: GeoDataFrame containing arc columns.
        start_geometry: Column name for start point geometries.
        end_geometry: Column name for end point geometries.
        include_columns: Optional iterable of column names to copy onto each arc.

    Returns:
        A list of arc dictionaries with start/end coordinates plus any requested
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
            "stroke",
            "dash_length",
            "dash_gap",
            "dash_initial_gap",
            "dash_animate_time",
        ),
        nonnegative_columns=("altitude", "altitude_auto_scale"),
        color_columns=("color",),
        string_columns=("label",),
        context="arcs_from_gdf",
    )
    try:
        validated = _build_arcs_schema().validate(renamed)
    except Exception as exc:
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
