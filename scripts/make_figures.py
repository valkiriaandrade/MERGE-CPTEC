"""Regenerate every figure in ``figures/`` from the data in ``data/``.

Usage::

    python scripts/make_figures.py [--data-dir data] [--figures-dir figures] [--dpi 200]

Figures whose source data is not in the repository are skipped with a warning and
the existing image is kept.
"""

from __future__ import annotations

import argparse
import logging
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
        "precipitation_anomaly_spread_may_2024.png",
        "anomaly-spread",
        "precipitation_anomaly_may.nc",
        period="May 2024",
    ),
    Figure(
        "precipitation_climatology_oct.png",
        "climatology",
        "MERGE_CPTEC_acum_oct.nc",
        period="October",
    ),
]


def build(data_dir: Path, figures_dir: Path, dpi: int) -> list[str]:
    """Rebuild all figures with available data; return the names that were skipped."""
    skipped = []
    shapefile = data_dir / "BR_UF_2022" / "BR_UF_2022.zip"
    for figure in FIGURES:
        source = data_dir / figure.source
        if not source.exists():
            logger.warning("Skipping %s (kept existing image): missing %s", figure.output, source)
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
        merge_cptec(args)
    return skipped


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--figures-dir", type=Path, default=ROOT / "figures")
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    skipped = build(args.data_dir, args.figures_dir, args.dpi)
    built = len(FIGURES) - len(skipped)
    logger.info("Done: %d figure(s) regenerated, %d kept as-is", built, len(skipped))


if __name__ == "__main__":
    main()
