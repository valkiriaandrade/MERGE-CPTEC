"""Download MERGE data from the public CPTEC/INPE server into ``data/``.

Source: https://ftp.cptec.inpe.br/modelos/tempo/MERGE/GPM/ (CPTEC/INPE). Daily rainfall
comes from ``DAILY/<YYYY>/<MM>/MERGE_CPTEC_<YYYYMMDD>.grib2`` and monthly accumulated
climatologies from ``CLIMATOLOGY/MONTHLY_ACCUMULATED/MERGE_CPTEC_acum_<mon>.nc``.

Usage::

    python scripts/download_data.py                       # everything `make figures` needs
    python scripts/download_data.py --months 2024-06 2024-08
    python scripts/download_data.py --climatology oct      # one climatology only
    python scripts/download_data.py --dry-run             # only list the URLs

Files that already exist are skipped (use ``--overwrite`` to fetch them again).
"""

from __future__ import annotations

import argparse
import calendar
import logging
import shutil
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

BASE_URL = "https://ftp.cptec.inpe.br/modelos/tempo/MERGE/GPM"
ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "merge-cptec-data-download"
#: Months whose daily files the figures and README examples use.
FIGURE_MONTHS = ["2024-05", "2024-07"]
#: Extra climatologies used directly by a figure (October climatology map).
FIGURE_CLIMATOLOGIES = ["oct"]
MONTH_ABBR = [m.lower() for m in calendar.month_abbr[1:]]

logger = logging.getLogger("download_data")


class DownloadError(RuntimeError):
    """A file could not be downloaded."""


@dataclass(frozen=True)
class Item:
    """One file to download: source URL and destination relative to the data folder."""

    url: str
    path: Path


def parse_month(value: str) -> date:
    """Parse ``YYYY-MM`` (argparse type)."""
    try:
        year, month = map(int, value.split("-"))
        return date(year, month, 1)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"invalid month {value!r}; use YYYY-MM") from error


def climatology_item(month: int) -> Item:
    """Monthly accumulated-precipitation climatology for calendar ``month``."""
    name = f"MERGE_CPTEC_acum_{calendar.month_abbr[month].lower()}.nc"
    return Item(f"{BASE_URL}/CLIMATOLOGY/MONTHLY_ACCUMULATED/{name}", Path(name))


def plan(month: date) -> list[Item]:
    """Daily GRIB2 files of ``month`` plus its monthly climatology."""
    abbr = calendar.month_abbr[month.month].lower()
    folder = Path(f"merge_daily_{abbr}_{month.year}")
    days = calendar.monthrange(month.year, month.month)[1]
    items = []
    for day in range(1, days + 1):
        name = f"MERGE_CPTEC_{month:%Y%m}{day:02d}.grib2"
        items.append(Item(f"{BASE_URL}/DAILY/{month:%Y/%m}/{name}", folder / name))
    items.append(climatology_item(month.month))
    return items


def fetch(
    url: str,
    dest: Path,
    *,
    overwrite: bool = False,
    retries: int = 3,
    timeout: float = 120,
    opener: Callable = urllib.request.urlopen,
) -> bool:
    """Download ``url`` to ``dest``; return False if it was skipped because it exists.

    The file is written to ``<dest>.part`` first and renamed when complete, so an
    interrupted download never leaves a truncated file behind.

    Raises:
        DownloadError: if the file does not exist on the server or every attempt fails.
    """
    if dest.exists() and dest.stat().st_size > 0 and not overwrite:
        logger.debug("Already present: %s", dest)
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name + ".part")
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with opener(request, timeout=timeout) as response, partial.open("wb") as out:
                shutil.copyfileobj(response, out)
            partial.replace(dest)
            return True
        except urllib.error.HTTPError as error:
            partial.unlink(missing_ok=True)
            if error.code == 404:
                raise DownloadError(
                    f"Not found on the server: {url} (check the date; the file may not exist)"
                ) from error
            last_error = error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            partial.unlink(missing_ok=True)
            last_error = error
        if attempt < retries:
            time.sleep(2 * attempt)
    raise DownloadError(f"Could not download {url} after {retries} attempts: {last_error}")


def download(items: Iterable[Item], data_dir: Path, *, overwrite: bool = False) -> list[str]:
    """Download every item; return the error messages of the ones that failed."""
    errors, fetched, skipped = [], 0, 0
    for item in items:
        try:
            if fetch(item.url, data_dir / item.path, overwrite=overwrite):
                fetched += 1
                logger.info("Downloaded %s", item.path)
            else:
                skipped += 1
        except DownloadError as error:
            errors.append(str(error))
            logger.error("%s", error)
    logger.info("%d downloaded, %d already present, %d failed", fetched, skipped, len(errors))
    return errors


def build_parser() -> argparse.ArgumentParser:
    """Command-line options."""
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--months",
        nargs="+",
        type=parse_month,
        metavar="YYYY-MM",
        help="months of daily files (each also brings its climatology)",
    )
    parser.add_argument(
        "--climatology",
        nargs="+",
        choices=MONTH_ABBR,
        metavar="MON",
        help="extra monthly climatologies, e.g. oct",
    )
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--overwrite", action="store_true", help="download existing files again")
    parser.add_argument("--dry-run", action="store_true", help="only list the URLs")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point; returns the process exit status."""
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if args.months or args.climatology:
        months, extra = args.months or [], args.climatology or []
    else:
        months = [parse_month(m) for m in FIGURE_MONTHS]
        extra = FIGURE_CLIMATOLOGIES
    items = [item for month in months for item in plan(month)]
    items += [climatology_item(MONTH_ABBR.index(mon) + 1) for mon in extra]
    items = list(dict.fromkeys(items))
    if args.dry_run:
        for item in items:
            print(f"{item.url} -> {args.data_dir / item.path}")
        return 0
    errors = download(items, args.data_dir, overwrite=args.overwrite)
    if errors:
        logger.error("%d file(s) could not be downloaded:\n  %s", len(errors), "\n  ".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
