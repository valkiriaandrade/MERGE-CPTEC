"""Precipitation accumulation and anomaly computation."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np
import xarray as xr

from .io import read_field, read_grib, spatial

#: Name of the anomaly variable written by ``--product anomaly-netcdf``.
ANOMALY_VARIABLE = "precipitation_anomaly"


def accumulate(files: Sequence[str | Path]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sum daily MERGE GRIB2 precipitation (mm) over ``files``.

    Missing values propagate per grid cell; days are never filled in.

    Returns:
        ``(total, lat, lon)`` as 2D arrays on the GRIB grid.

    Raises:
        ValueError: if no files are given or grids differ between files.
    """
    if not files:
        raise ValueError("No GRIB2 files given; pass a directory with the daily MERGE files")
    total = lat = lon = None
    for path in files:
        values, current_lat, current_lon, _ = read_grib(path, "Precipitation")
        if total is None:
            total, lat, lon = values.copy(), current_lat, current_lon
        else:
            if (
                values.shape != total.shape
                or not np.array_equal(lat, current_lat)
                or not np.array_equal(lon, current_lon)
            ):
                raise ValueError(
                    f"Grid mismatch in {path}; all daily files must share the same grid"
                )
            total += values
    return total, lat, lon


def anomaly(files: Sequence[str | Path], climatology: str | Path) -> xr.DataArray:
    """Accumulated precipitation over ``files`` minus the ``precacum`` climatology (mm).

    The accumulation is interpolated once (linear triangulation) to the climatology
    grid; points outside the source grid stay missing.
    """
    from scipy.interpolate import griddata

    total, lat, lon = accumulate(files)
    reference = spatial(read_field(climatology, "precacum"))
    target_lon, target_lat = np.meshgrid(
        (reference.lon.values + 180) % 360 - 180, reference.lat.values
    )
    interpolated = griddata(
        (lon.ravel(), lat.ravel()), total.ravel(), (target_lon, target_lat), method="linear"
    )
    result = xr.DataArray(
        interpolated - reference.values,
        dims=("lat", "lon"),
        coords={"lat": reference.lat, "lon": reference.lon},
        name=ANOMALY_VARIABLE,
        attrs={
            "units": "mm",
            "source_file_count": len(files),
            "interpolation": "linear",
            "missing_data_policy": "propagate",
        },
    )
    result.lat.attrs["units"] = "degrees_north"
    result.lon.attrs["units"] = "degrees_east"
    return result
