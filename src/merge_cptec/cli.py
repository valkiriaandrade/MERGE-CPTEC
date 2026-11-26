"""``merge-cptec`` command: precipitation accumulation, climatology and anomaly maps."""

from __future__ import annotations

import argparse
import calendar
import logging
from collections.abc import Sequence
from pathlib import Path

import xarray as xr

from .arguments import build_parser, execute
from .colour_scales import colour_scale
from .io import files_in, read_field, save_netcdf, spatial
from .labels import (
    SOURCE_CREDIT,
    dates_from_names,
    format_period,
    format_title,
    month_coverage_problem,
    month_from_name,
    units_label,
)
from .plotting import plot_map
from .processing import ANOMALY_VARIABLE, accumulate, anomaly
from .regions import ALIASES, REGIONS, normalize_region

logger = logging.getLogger(__name__)

PRODUCTS = ["accumulation", "anomaly-netcdf", "anomaly", "anomaly-spread", "climatology"]
#: Anomaly NetCDF files written before v0.2 use the original Portuguese variable name;
#: both names are accepted (the files in data/ now use the English one).
LEGACY_ANOMALY_VARIABLE = "anomalia_precipitacao"
#: Options that only change the map, so they mean nothing for anomaly-netcdf.
MAP_ONLY = ("title", "shapefile", "period")


def read_anomaly(path: str | Path) -> xr.DataArray:
    """Read an anomaly NetCDF written by ``anomaly-netcdf`` (current or legacy name)."""
    try:
        return read_field(path, ANOMALY_VARIABLE)
    except ValueError:
        return read_field(path, LEGACY_ANOMALY_VARIABLE)


def check_month(
    files: list[Path], climatology: str | Path | None, *, strict: bool, allow_partial: bool
) -> None:
    """Check that ``files`` are the days of one whole month, matching the climatology month.

    A partial or mixed period is an error when ``strict`` (an anomaly against a monthly
    climatology) unless ``allow_partial``; otherwise it is logged as a warning.

    Raises:
        ValueError: on a partial period (strict) or a climatology of another month.
    """
    dates = dates_from_names(files)
    problem = month_coverage_problem(dates)
    if problem and strict and not allow_partial:
        raise ValueError(
            f"{problem}; an anomaly compares a whole month with its monthly climatology "
            "(run `make data`, or pass --allow-partial to compute it anyway)"
        )
    if problem:
        logger.warning("Not a whole month: %s", problem)
    if climatology is None or not dates:
        return
    expected = month_from_name(climatology)
    months = sorted({calendar.month_name[d.month] for d in dates})
    if expected is None:
        logger.warning("Cannot tell the month of %s from its name; not checked", climatology)
    elif months != [expected]:
        raise ValueError(
            f"The daily files are from {' and '.join(months)} but the climatology "
            f"{Path(climatology).name} is for {expected}"
        )


def run(args: argparse.Namespace) -> None:
    """Build the product described by ``args``: a NetCDF file or a map."""
    if args.product == "anomaly-netcdf":
        if not args.climatology:
            raise ValueError("--product anomaly-netcdf needs --climatology FILE")
        ignored = [f"--{name}" for name in MAP_ONLY if getattr(args, name)]
        if ignored:
            logger.warning("%s only change maps; ignored for anomaly-netcdf", ", ".join(ignored))
        files = files_in(args.input, ".grib2")
        check_month(files, args.climatology, strict=True, allow_partial=args.allow_partial)
        save_netcdf(anomaly(files, args.climatology), args.output)
        return
    period = args.period
    if args.product == "accumulation":
        files = files_in(args.input, ".grib2")
        logger.info("Accumulating %d daily GRIB2 files from %s", len(files), args.input)
        check_month(files, None, strict=False, allow_partial=args.allow_partial)
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
    units = units_label("mm")
    scale = colour_scale(args.product, args.region)
    if args.product == "anomaly-spread":
        label = "Precipitation anomaly class (spatial mean ± k·σ)"
    elif is_anomaly:
        label = f"Precipitation anomaly ({units})"
    else:
        label = f"Precipitation ({units})"
    region = REGIONS[args.region]
    plot_map(
        values,
        lat,
        lon,
        args.output,
        # the spread classes have no unit
        title=args.title
        or format_title(
            args.product, period, region.label, "" if args.product == "anomaly-spread" else units
        ),
        label=label,
        levels=scale.levels,
        cmap=scale.cmap,
        extend=scale.extend,
        class_labels=scale.class_labels,
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
    for action in parser._actions:
        if action.dest == "output":
            action.help = "output PNG file (a NetCDF file for anomaly-netcdf)"
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
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="compute anomaly-netcdf even if the daily files are not one whole month",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Entry point of the ``merge-cptec`` command."""
    execute(build_cli(), run, argv)
