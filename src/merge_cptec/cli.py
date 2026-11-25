"""``merge-cptec`` command: precipitation accumulation, climatology and anomaly maps."""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence
from pathlib import Path

import xarray as xr

from .arguments import build_parser, execute
from .io import files_in, read_field, save_netcdf, spatial
from .labels import (
    SOURCE_CREDIT,
    dates_from_names,
    format_period,
    format_title,
    month_from_name,
    units_label,
)
from .plotting import plot_map
from .processing import ANOMALY_VARIABLE, accumulate, anomaly
from .regions import ALIASES, REGIONS, normalize_region

logger = logging.getLogger(__name__)

PRODUCTS = ["accumulation", "anomaly-netcdf", "anomaly", "anomaly-spread", "climatology"]
ANOMALY_LEVELS = [-400, -300, -200, -100, -75, -50, -25, -5, 0, 5, 25, 50, 75, 100, 200, 300, 400]
AMOUNT_LEVELS = [0, 20, 50, 80, 100, 150, 200, 300, 400, 500]
#: Anomaly NetCDF files bundled with the repository were written before v0.2 and
#: use the original Portuguese variable name; both names are accepted.
LEGACY_ANOMALY_VARIABLE = "anomalia_precipitacao"


def read_anomaly(path: str | Path) -> xr.DataArray:
    """Read an anomaly NetCDF written by ``anomaly-netcdf`` (current or legacy name)."""
    try:
        return read_field(path, ANOMALY_VARIABLE)
    except ValueError:
        return read_field(path, LEGACY_ANOMALY_VARIABLE)


def run(args: argparse.Namespace) -> None:
    """Build the product described by ``args``: a NetCDF file or a map."""
    if args.product == "anomaly-netcdf":
        if not args.climatology:
            raise ValueError("--product anomaly-netcdf needs --climatology FILE")
        save_netcdf(anomaly(files_in(args.input, ".grib2"), args.climatology), args.output)
        return
    period = args.period
    if args.product == "accumulation":
        files = files_in(args.input, ".grib2")
        logger.info("Accumulating %d daily GRIB2 files from %s", len(files), args.input)
        values, lat, lon = accumulate(files)
        period = period or format_period(dates_from_names(files))
    else:
        field = (
            read_field(args.input, "precacum")
            if args.product == "climatology"
            else read_anomaly(args.input)
        )
        field = spatial(field)
        values, lat, lon = field.values, field.lat.values, field.lon.values
        period = period or month_from_name(args.input)
    is_anomaly = args.product.startswith("anomaly")
    region = REGIONS[args.region]
    units = units_label("mm")
    plot_map(
        values,
        lat,
        lon,
        args.output,
        title=args.title or format_title(args.product, period, region.label, units),
        label=f"Precipitation anomaly ({units})" if is_anomaly else f"Precipitation ({units})",
        levels=ANOMALY_LEVELS if is_anomaly else AMOUNT_LEVELS,
        cmap="BrBG" if is_anomaly else "YlGnBu",
        shapefile=args.shapefile,
        spatial_spread=args.product == "anomaly-spread",
        states=list(region.states) if region.states else None,
        extent=list(region.extent),
        credit=SOURCE_CREDIT,
        dpi=args.dpi,
    )


def build_cli() -> argparse.ArgumentParser:
    """Return the parser for the ``merge-cptec`` command."""
    parser = build_parser(
        "MERGE precipitation products. The accumulation sums every daily GRIB2 file in "
        "--input, so the folder must contain exactly the desired period."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="directory of daily GRIB2 files (accumulation, anomaly-netcdf) or a NetCDF "
        "file (anomaly, anomaly-spread, climatology)",
    )
    parser.add_argument(
        "--climatology", help="precacum climatology NetCDF (required by anomaly-netcdf)"
    )
    parser.add_argument(
        "--region",
        type=normalize_region,
        choices=list(REGIONS),
        default="brazil",
        help=f"map domain (Portuguese aliases accepted: {', '.join(ALIASES)})",
    )
    parser.add_argument(
        "--product",
        choices=PRODUCTS,
        default="accumulation",
        help="accumulation: sum of daily files; anomaly-netcdf: accumulation minus "
        "climatology saved as NetCDF; anomaly: map of that NetCDF; anomaly-spread: anomaly "
        "in classes of the field's spatial mean ± standard deviation; climatology: map of "
        "a precacum file",
    )
    parser.add_argument(
        "--period",
        help='period shown in the title, e.g. "May 2024" (default: from file names)',
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Entry point of the ``merge-cptec`` command."""
    execute(build_cli(), run, argv)
