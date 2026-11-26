"""Precipitation accumulation and anomaly computation."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np
import xarray as xr

from . import __version__
from .io import read_field, read_grib, spatial
from .labels import (
    CLIMATOLOGY_PERIOD,
    MERGE_REFERENCE,
    dates_from_names,
    format_period,
    month_from_name,
)

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
    grid; points outside the source grid stay missing. The variable carries the CF
    ``long_name`` and ``units``; the file attributes come from
    :func:`anomaly_global_attributes`.
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
            "long_name": anomaly_long_name(files, climatology),
            "units": "mm",
            "source_file_count": len(files),
            "interpolation": "linear",
            "missing_data_policy": "propagate",
        },
    )
    result.lat.attrs.update(standard_name="latitude", units="degrees_north")
    result.lon.attrs.update(standard_name="longitude", units="degrees_east")
    return result


def _period(files: Sequence[str | Path]) -> tuple[str, str, str]:
    """``(period, first ISO date, last ISO date)`` of the daily files; the dates are empty
    when no file name carries one."""
    dates = dates_from_names(files)
    if not dates:
        return "unknown period", "", ""
    return format_period(dates), dates[0].isoformat(), dates[-1].isoformat()


def _coverage_note(files: Sequence[str | Path]) -> str:
    """A sentence on days missing from the period (only ``--allow-partial`` lets them in).

    >>> _coverage_note(["MERGE_CPTEC_20240701.grib2", "MERGE_CPTEC_20240703.grib2"])
    ' Only 2 of the 3 days from 01 Jul 2024 to 03 Jul 2024 are present.'
    >>> _coverage_note(["daily.grib2"])
    ' The daily file names carry no dates, so the period is unknown.'
    """
    dates = dates_from_names(files)
    if not dates:
        return " The daily file names carry no dates, so the period is unknown."
    span = (dates[-1] - dates[0]).days + 1
    if len(set(dates)) == span:
        return ""
    return (
        f" Only {len(set(dates))} of the {span} days from {dates[0]:%d %b %Y} to "
        f"{dates[-1]:%d %b %Y} are present."
    )


def anomaly_long_name(files: Sequence[str | Path], climatology: str | Path) -> str:
    """CF ``long_name``: what is subtracted from what.

    >>> anomaly_long_name(["MERGE_CPTEC_20240701.grib2"], "MERGE_CPTEC_acum_jul.nc")
    'precipitation anomaly: 01 Jul 2024 to 01 Jul 2024 total minus the 1998-2024 July mean'
    """
    month = month_from_name(climatology) or "monthly"
    return (
        f"precipitation anomaly: {_period(files)[0]} total minus the "
        f"{CLIMATOLOGY_PERIOD} {month} mean"
    )


def anomaly_global_attributes(
    files: Sequence[str | Path], climatology: str | Path
) -> dict[str, str | int]:
    """CF / ACDD file attributes of an anomaly NetCDF: period, climatology, source.

    No creation time is written, so rebuilding the file from the same inputs gives the
    same bytes.
    """
    period, start, end = _period(files)
    climatology = Path(climatology)
    month = month_from_name(climatology)
    attrs: dict[str, str | int] = {
        "Conventions": "CF-1.8",
        "title": f"MERGE precipitation anomaly, {period}",
        "institution": "CPTEC/INPE (Centro de Previsão de Tempo e Estudos Climáticos)",
        "source": (
            "CPTEC/INPE MERGE daily precipitation (rain gauges merged with GPM IMERG, 0.1 degree), "
            f"summed over {period}, minus the CPTEC MERGE monthly accumulated climatology"
        ),
        "references": MERGE_REFERENCE,
        "period": period,
        "time_coverage_start": start,
        "time_coverage_end": end,
        "climatology_period": CLIMATOLOGY_PERIOD,
        "climatology_month": month or "unknown",
        "climatology_file": climatology.name,
        "comment": (
            f"Climatology base period {CLIMATOLOGY_PERIOD} (27 years), from CPTEC's read-me "
            "https://ftp.cptec.inpe.br/modelos/tempo/MERGE/GPM/CLIMATOLOGY/MONTHLY_ACCUMULATED/"
            "read-me.txt; it includes 2024. "
            "Daily totals are summed on the MERGE grid and interpolated linearly to the "
            "climatology grid; missing values propagate." + _coverage_note(files)
        ),
        "history": (
            f"merge-cptec {__version__} --product anomaly-netcdf: {len(files)} daily files, "
            f"climatology {climatology.name}"
        ),
    }
    if month is None:
        attrs.pop("climatology_month")
    if not start:
        attrs.pop("time_coverage_start")
        attrs.pop("time_coverage_end")
    return attrs
