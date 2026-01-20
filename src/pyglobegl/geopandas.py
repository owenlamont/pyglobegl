"""GeoPandas helpers for pyglobegl."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, TYPE_CHECKING


if TYPE_CHECKING:
    import geopandas as gpd


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
        ModuleNotFoundError: If GeoPandas is not installed.
        ValueError: If the GeoDataFrame has no CRS or contains no point geometries.
    """
    try:
        import geopandas as gpd  # noqa: F401
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "GeoPandas is required for points_from_gdf. "
            "Install with `uv add pyglobegl[geopandas]`."
        ) from exc

    if gdf.crs is None:
        raise ValueError("GeoDataFrame must have a CRS to convert to EPSG:4326.")

    resolved_geometry = (
        geometry_column if geometry_column is not None else gdf.geometry.name
    )
    geometry_name = str(resolved_geometry)
    gdf = gdf.set_geometry(geometry_name, inplace=False)
    gdf = gdf.to_crs(4326)

    point_mask = gdf.geometry.geom_type == "Point"
    gdf = gdf[point_mask]
    if gdf.empty:
        raise ValueError("GeoDataFrame contains no point geometries.")

    columns = list(include_columns) if include_columns is not None else []
    missing = [col for col in columns if col not in gdf.columns]
    if missing:
        raise ValueError(f"GeoDataFrame missing columns: {missing}")

    data = gdf[columns].copy() if columns else gdf.iloc[:, 0:0].copy()
    data["lat"] = gdf.geometry.y
    data["lng"] = gdf.geometry.x
    return data.to_dict("records")
