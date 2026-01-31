"""GeoPandas helpers for pyglobegl."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from pyglobegl.config import ArcDatum, PathDatum, PointDatum, PolygonDatum


if TYPE_CHECKING:
    import geopandas as gpd
    import pandas as pd
    import pandera.pandas as pa
    from pandera.typing import Series
    from pandera.typing.geopandas import Geometry, GeoSeries
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
        altitude: Series[float] | None = pa.Field(nullable=True, coerce=True)
        radius: Series[float] | None = pa.Field(nullable=True, coerce=True)
        color: Series[str] | None = pa.Field(nullable=True, coerce=False)
        label: Series[str] | None = pa.Field(nullable=True, coerce=False)

        class Config:
            coerce = False
            strict = False

        @pa.check("geometry", error="Geometry must be Points.")
        def _points_only(self, series: GeoSeries[Geometry]) -> Series[bool]:
            return series.geom_type == "Point"

        @pa.check("altitude", "radius", error="column must be numeric.")
        def _numeric_only(self, series: Series[float]) -> pd.Series:
            return _is_numeric_series(series)

        @pa.check("radius", error="column must be positive.")
        def _radius_positive(self, series: Series[float]) -> pd.Series:
            return _is_positive_series(series)

        @pa.check("altitude", error="column must be non-negative.")
        def _altitude_nonnegative(self, series: Series[float]) -> pd.Series:
            return _is_nonnegative_series(series)

        @pa.check("color", error="column must be strings.")
        def _color_strings(self, series: Series[str]) -> pd.Series:
            return _is_string_series(series)

        @pa.check("color", error="column must be valid CSS colors.")
        def _color_css(self, series: Series[str]) -> pd.Series:
            return _is_css_color_series(series)

        @pa.check("label", error="column must be strings.")
        def _label_strings(self, series: Series[str]) -> pd.Series:
            return _is_string_series(series)

    return PointsGeoDataFrameModel


def _build_arcs_schema() -> type[pa.DataFrameModel]:
    import pandera.pandas as pa
    from pandera.typing import Series

    globals().update({"Series": Series})

    class ArcsGeoDataFrameModel(pa.DataFrameModel):
        """Pandera schema for arcs layer data."""

        start_lat: Series[float] = pa.Field(
            in_range={"min_value": -90, "max_value": 90}, coerce=True
        )
        start_lng: Series[float] = pa.Field(
            in_range={"min_value": -180, "max_value": 180}, coerce=True
        )
        end_lat: Series[float] = pa.Field(
            in_range={"min_value": -90, "max_value": 90}, coerce=True
        )
        end_lng: Series[float] = pa.Field(
            in_range={"min_value": -180, "max_value": 180}, coerce=True
        )
        altitude: Series[float] | None = pa.Field(nullable=True, coerce=True)
        altitude_auto_scale: Series[float] | None = pa.Field(nullable=True, coerce=True)
        stroke: Series[float] | None = pa.Field(nullable=True, coerce=True)
        dash_length: Series[float] | None = pa.Field(nullable=True, coerce=True)
        dash_gap: Series[float] | None = pa.Field(nullable=True, coerce=True)
        dash_initial_gap: Series[float] | None = pa.Field(nullable=True, coerce=True)
        dash_animate_time: Series[float] | None = pa.Field(nullable=True, coerce=True)
        color: Series[str] | None = pa.Field(nullable=True, coerce=False)
        label: Series[str] | None = pa.Field(nullable=True, coerce=False)

        class Config:
            coerce = False
            strict = False

        @pa.check(
            "altitude",
            "altitude_auto_scale",
            "stroke",
            "dash_length",
            "dash_gap",
            "dash_initial_gap",
            "dash_animate_time",
            error="column must be numeric.",
        )
        def _numeric_only(self, series: Series[float]) -> pd.Series:
            return _is_numeric_series(series)

        @pa.check(
            "stroke",
            "dash_length",
            "dash_gap",
            "dash_initial_gap",
            "dash_animate_time",
            error="column must be positive.",
        )
        def _positive_only(self, series: Series[float]) -> pd.Series:
            return _is_positive_series(series)

        @pa.check(
            "altitude", "altitude_auto_scale", error="column must be non-negative."
        )
        def _nonnegative_only(self, series: Series[float]) -> pd.Series:
            return _is_nonnegative_series(series)

        @pa.check("color", error="column must be strings.")
        def _color_strings(self, series: Series[str]) -> pd.Series:
            return _is_string_series(series)

        @pa.check("color", error="column must be valid CSS colors.")
        def _color_css(self, series: Series[str]) -> pd.Series:
            return _is_css_color_series(series)

        @pa.check("label", error="column must be strings.")
        def _label_strings(self, series: Series[str]) -> pd.Series:
            return _is_string_series(series)

    return ArcsGeoDataFrameModel


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
        cap_color: Series[str] | None = pa.Field(nullable=True, coerce=False)
        side_color: Series[str] | None = pa.Field(nullable=True, coerce=False)
        stroke_color: Series[str] | None = pa.Field(nullable=True, coerce=False)
        altitude: Series[float] | None = pa.Field(nullable=True, ge=0, coerce=True)
        cap_curvature_resolution: Series[float] | None = pa.Field(
            nullable=True, gt=0, coerce=True
        )
        label: Series[str] | None = pa.Field(nullable=True, coerce=False)
        name: Series[str] | None = pa.Field(nullable=True, coerce=False)

        class Config:
            coerce = False
            strict = False

        @pa.check("geometry", error="Geometry must be Polygon or MultiPolygon.")
        def _polygon_only(self, series: GeoSeries[Geometry]) -> Series[bool]:
            return series.geom_type.isin(["Polygon", "MultiPolygon"])

        @pa.check(
            "cap_color",
            "side_color",
            "stroke_color",
            error="Color columns must be valid CSS colors.",
        )
        def _colors_valid(self, series: Series[str]) -> pd.Series:
            return _is_css_color_series(series)

        @pa.check(
            "cap_color",
            "side_color",
            "stroke_color",
            error="Color columns must be strings.",
        )
        def _colors_strings(self, series: Series[str]) -> pd.Series:
            return _is_string_series(series)

        @pa.check("label", "name", error="Column must be strings.")
        def _label_name_strings(self, series: Series[str]) -> pd.Series:
            return _is_string_series(series)

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
        dash_length: Series[float] | None = pa.Field(nullable=True, gt=0, coerce=True)
        dash_gap: Series[float] | None = pa.Field(nullable=True, gt=0, coerce=True)
        dash_initial_gap: Series[float] | None = pa.Field(
            nullable=True, gt=0, coerce=True
        )
        dash_animate_time: Series[float] | None = pa.Field(
            nullable=True, gt=0, coerce=True
        )
        color: Series[str] | None = pa.Field(nullable=True, coerce=False)
        label: Series[str] | None = pa.Field(nullable=True, coerce=False)
        name: Series[str] | None = pa.Field(nullable=True, coerce=False)

        class Config:
            coerce = False
            strict = False

        @pa.check("geometry", error="Geometry must be LineString or MultiLineString.")
        def _line_only(self, series: GeoSeries[Geometry]) -> Series[bool]:
            return series.geom_type.isin(["LineString", "MultiLineString"])

        @pa.check("color", error="Color column must be valid CSS colors.")
        def _colors_valid(self, series: Series[str]) -> pd.Series:
            return _is_css_color_series(series)

        @pa.check("color", error="Color column must be strings.")
        def _colors_strings(self, series: Series[str]) -> pd.Series:
            return _is_string_series(series)

        @pa.check("label", "name", error="Column must be strings.")
        def _label_name_strings(self, series: Series[str]) -> pd.Series:
            return _is_string_series(series)

    return PathsGeoDataFrameModel


def _css_color_names() -> set[str]:
    try:
        import webcolors
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "webcolors is required for color validation. "
            "Install with `uv add pyglobegl[geopandas]`."
        ) from exc
    return set(webcolors.names())


def _is_numeric_series(series: pd.Series) -> pd.Series:
    import numpy as np
    import pandas as pd

    coerced = pd.to_numeric(series, errors="coerce")
    return coerced.notna() & np.isfinite(coerced)


def _is_positive_series(series: pd.Series) -> pd.Series:
    import numpy as np
    import pandas as pd

    coerced = pd.to_numeric(series, errors="coerce")
    return coerced.notna() & np.isfinite(coerced) & (coerced > 0)


def _is_nonnegative_series(series: pd.Series) -> pd.Series:
    import numpy as np
    import pandas as pd

    coerced = pd.to_numeric(series, errors="coerce")
    return coerced.notna() & np.isfinite(coerced) & (coerced >= 0)


def _is_string_series(series: pd.Series) -> pd.Series:
    return series.isna() | series.map(lambda value: isinstance(value, str))


def _is_css_color_series(series: pd.Series) -> pd.Series:
    import pandas as pd

    valid = pd.Series(True, index=series.index)
    is_null = series.isna()
    valid[is_null] = True
    is_str = series.map(lambda value: isinstance(value, str))
    if is_str.any():
        str_series = series[is_str].astype(str)
        hex_match = str_series.str.match(
            r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$"
        )
        names = str_series.str.lower().isin(_css_color_names())
        valid.loc[is_str] = hex_match | names
    return valid


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
    try:
        validated = _build_arcs_schema().validate(renamed)
    except Exception as exc:
        _handle_schema_error(exc, "GeoDataFrame contains invalid arc coordinates.")

    columns = list(include_columns) if include_columns is not None else []
    missing_extra = [col for col in columns if col not in validated.columns]
    if missing_extra:
        raise ValueError(f"GeoDataFrame missing columns: {missing_extra}")

    data = validated[columns].copy() if columns else validated.iloc[:, 0:0].copy()
    data["start_lat"] = validated["start_lat"]
    data["start_lng"] = validated["start_lng"]
    data["end_lat"] = validated["end_lat"]
    data["end_lng"] = validated["end_lng"]
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

    data = gdf[columns].copy() if columns else gdf.iloc[:, 0:0].copy()
    data["path"] = [_to_path_coordinates(geom) for geom in gdf.geometry]
    return [PathDatum.model_validate(record) for record in data.to_dict("records")]


def _to_path_coordinates(
    geom: BaseGeometry,
) -> list[tuple[float, float] | tuple[float, float, float]]:
    if geom.geom_type == "LineString":
        return list(geom.coords)
    if geom.geom_type == "MultiLineString":
        return list(geom.geoms[0].coords)
    raise ValueError("Geometry must be LineString or MultiLineString.")
