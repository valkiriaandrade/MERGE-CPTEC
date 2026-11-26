"""Regenerate every figure in ``figures/`` from the data in ``data/``.

Usage::

    python scripts/make_figures.py [--data-dir data] [--figures-dir figures] [--dpi 200]

The anomaly NetCDF files are rebuilt first from the daily GRIB2 files and the monthly
climatology (``merge-cptec --product anomaly-netcdf``), so the anomaly maps always follow
the raw data. If those inputs are missing or incomplete (run ``make data``), the existing
NetCDF file is kept. Figures whose source data is missing are skipped with a warning and
the existing image is kept. A figure that fails does not stop the others. The exit status
is 1 if any figure was skipped or failed.
"""

from __future__ import annotations

import argparse
import calendar
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from merge_cptec.cli import main as merge_cptec

ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger("make_figures")


@dataclass(frozen=True)
class Figure:
    """One published figure and the inputs needed to rebuild it."""

    output: str
    product: str
    source: str
    region: str = "brazil"
    period: str | None = None


@dataclass(frozen=True)
class AnomalyFile:
    """An anomaly NetCDF file and the raw inputs it is computed from."""

    output: str
    daily: str
    climatology: str


ANOMALY_FILES = [
    AnomalyFile("precipitation_anomaly_jul.nc", "merge_daily_jul_2024", "MERGE_CPTEC_acum_jul.nc"),
    AnomalyFile("precipitation_anomaly_jun.nc", "merge_daily_jun_2024", "MERGE_CPTEC_acum_jun.nc"),
]

FIGURES = [
    Figure("accumulated_precipitation_may_2024.png", "accumulation", "merge_daily_may_2024"),
    Figure(
        "accumulated_precipitation_jul_2024_north.png",
        "accumulation",
        "merge_daily_jul_2024",
        region="north",
    ),
    Figure(
        "precipitation_anomaly_jul_2024.png",
        "anomaly",
        "precipitation_anomaly_jul.nc",
        period="July 2024",
    ),
    Figure(
        "precipitation_anomaly_spread_jun_2024.png",
        "anomaly-spread",
        "precipitation_anomaly_jun.nc",
        period="June 2024",
    ),
    Figure(
        "precipitation_climatology_oct.png",
        "climatology",
        "MERGE_CPTEC_acum_oct.nc",
        period="October",
    ),
]


def incomplete_month(folder: Path) -> str | None:
    """Describe a daily folder that does not hold every day of its month, else None."""
    match = re.search(r"_([a-z]{3})_(\d{4})$", folder.name)
    if not match or not folder.is_dir():
        return None
    month = [m.lower() for m in calendar.month_abbr].index(match.group(1))
    expected = calendar.monthrange(int(match.group(2)), month)[1]
    found = len(list(folder.glob("*.grib2")))
    if found != expected:
        return f"{folder.name} has {found} of {expected} daily files"
    return None


def build_anomalies(data_dir: Path) -> list[str]:
    """Recompute each anomaly NetCDF from its raw inputs; return the ones kept as they were."""
    kept = []
    for anomaly in ANOMALY_FILES:
        daily, climatology = data_dir / anomaly.daily, data_dir / anomaly.climatology
        missing = [str(path) for path in (daily, climatology) if not path.exists()]
        problem = f"missing {', '.join(missing)}" if missing else incomplete_month(daily)
        if problem:
            logger.warning(
                "Keeping existing %s: %s; run `make data` to rebuild it", anomaly.output, problem
            )
            kept.append(anomaly.output)
            continue
        logger.info("Computing %s from %s and %s", anomaly.output, daily.name, climatology.name)
        args = [
            "--input", str(daily),
            "--product", "anomaly-netcdf",
            "--climatology", str(climatology),
            "--output", str(data_dir / anomaly.output),
        ]  # fmt: skip
        if not call(merge_cptec, args, anomaly.output):
            kept.append(anomaly.output)
    return kept


def call(command, args: list[str], name: str) -> bool:
    """Run a CLI entry point; log and return False if it fails (the others still run)."""
    try:
        command(args)
    except SystemExit as error:  # the CLI reports expected errors with exit status 2
        if not error.code:
            return True
        logger.error("Failed: %s", name)
    except Exception:
        logger.exception("Failed: %s", name)
    else:
        return True
    return False


def build(data_dir: Path, figures_dir: Path, dpi: int) -> tuple[list[str], list[str]]:
    """Rebuild all figures with available data; return the names skipped and failed."""
    build_anomalies(data_dir)
    skipped, failed = [], []
    shapefile = data_dir / "BR_UF_2022" / "BR_UF_2022.zip"
    for figure in FIGURES:
        source = data_dir / figure.source
        if not source.exists():
            logger.warning("Skipping %s (kept existing image): missing %s", figure.output, source)
            skipped.append(figure.output)
            continue
        problem = incomplete_month(source)
        if problem:
            logger.error("Skipping %s: %s; run `make data` first", figure.output, problem)
            skipped.append(figure.output)
            continue
        logger.info("Building %s", figure.output)
        args = [
            "--input", str(source),
            "--product", figure.product,
            "--region", figure.region,
            "--shapefile", str(shapefile),
            "--dpi", str(dpi),
            "--output", str(figures_dir / figure.output),
        ]  # fmt: skip
        if figure.period:
            args += ["--period", figure.period]
        if not call(merge_cptec, args, figure.output):
            failed.append(figure.output)
    return skipped, failed


def main() -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--figures-dir", type=Path, default=ROOT / "figures")
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    skipped, failed = build(args.data_dir, args.figures_dir, args.dpi)
    built = len(FIGURES) - len(skipped) - len(failed)
    logger.info(
        "Done: %d figure(s) regenerated, %d skipped, %d failed", built, len(skipped), len(failed)
    )
    return 1 if skipped or failed else 0


if __name__ == "__main__":
    sys.exit(main())
