"""MovingPandas helpers for pyglobegl."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from pyglobegl.config import PathDatum
from pyglobegl.geopandas import paths_from_gdf


def paths_from_mpd(
    obj: Any, *, include_columns: Iterable[str] | None = None
) -> list[PathDatum]:
    """Convert a MovingPandas Trajectory or TrajectoryCollection into path data models.

    Args:
        obj: MovingPandas Trajectory or TrajectoryCollection.
        include_columns: Optional iterable of column names to copy onto each path.

    Returns:
        A list of PathDatum models.

    Raises:
        ModuleNotFoundError: If movingpandas is not installed.
        TypeError: If obj is not a Trajectory or TrajectoryCollection.
    """
    try:
        import movingpandas as mpd
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "MovingPandas is required for paths_from_mpd. "
            "Install with `uv add pyglobegl[movingpandas]`."
        ) from exc

    if isinstance(obj, mpd.TrajectoryCollection):
        trajectories = obj.trajectories
    elif isinstance(obj, mpd.Trajectory):
        trajectories = [obj]
    else:
        raise TypeError("obj must be a Trajectory or TrajectoryCollection.")

    columns = list(include_columns) if include_columns is not None else []
    records = []
    crs = None

    for traj in trajectories:
        crs = crs or traj.crs
        line = traj.to_linestring()
        record = {"geometry": line}

        for col in columns:
            if col in traj.df.columns:
                record[col] = traj.df[col].iloc[0]
            elif hasattr(traj, col):
                record[col] = getattr(traj, col)

        records.append(record)

    import geopandas as gpd

    gdf = gpd.GeoDataFrame(records, geometry="geometry", crs=crs)
    return paths_from_gdf(gdf, include_columns=columns)
