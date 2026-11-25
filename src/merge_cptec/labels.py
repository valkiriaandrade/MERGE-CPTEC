"""Human-readable labels for map titles and colorbars."""

from __future__ import annotations

import calendar
import re
from collections.abc import Iterable
from datetime import date
from pathlib import Path

PRODUCT = "MERGE"
SOURCE_CREDIT = "Data: CPTEC/INPE MERGE"

PRODUCT_NAMES: dict[str, str] = {
    "accumulation": "accumulated precipitation",
    "anomaly": "precipitation anomaly",
    "anomaly-spread": "precipitation anomaly, spatial-spread classes",
    "climatology": "precipitation climatology",
}

#: GRIB/CF units that already mean millimetres of precipitation (1 kg m⁻² of water = 1 mm).
PRECIPITATION_MM_UNITS = frozenset({"kg m**-2", "kg m-2", "kg/m2", "kg/m^2", "mm"})

_UNIT_LABELS: dict[str, str] = {unit: "mm" for unit in PRECIPITATION_MM_UNITS}

_DATE_IN_NAME = re.compile(r"(?<!\d)(\d{4})(\d{2})(\d{2})(?!\d)")
_MONTH_IN_NAME = re.compile(
    r"(?:^|[_\-.])(" + "|".join(m.lower() for m in calendar.month_abbr[1:]) + r")(?:[_\-.]|$)"
)


def is_precipitation_mm(units: str | None) -> bool:
    """True if ``units`` is a precipitation amount equivalent to millimetres."""
    return bool(units) and units.strip().lower() in PRECIPITATION_MM_UNITS


def units_label(units: str | None) -> str:
    """Return a display label for ``units`` (``"kg m**-2"`` -> ``"mm"``).

    Unknown units are returned unchanged; missing units give an empty string.
    """
    if not units:
        return ""
    return _UNIT_LABELS.get(units.strip().lower(), units.strip())


def dates_from_names(paths: Iterable[str | Path]) -> list[date]:
    """Extract ``YYYYMMDD`` dates from file names such as ``MERGE_CPTEC_20240701.grib2``."""
    found = []
    for path in paths:
        match = _DATE_IN_NAME.search(Path(path).name)
        if match:
            year, month, day = map(int, match.groups())
            try:
                found.append(date(year, month, day))
            except ValueError:
                continue
    return sorted(found)


def month_from_name(path: str | Path) -> str | None:
    """Return the month name for files tagged ``_jul``, ``_oct``… (e.g. climatologies)."""
    match = _MONTH_IN_NAME.search(Path(path).stem.lower())
    if not match:
        return None
    index = [m.lower() for m in calendar.month_abbr].index(match.group(1))
    return calendar.month_name[index]


def format_period(dates: Iterable[date]) -> str | None:
    """Describe a list of dates: ``"July 2024"`` for one month, otherwise a date range."""
    dates = sorted(dates)
    if not dates:
        return None
    first, last = dates[0], dates[-1]
    if (first.year, first.month) == (last.year, last.month):
        return f"{calendar.month_name[first.month]} {first.year}"
    return f"{first:%d %b %Y} to {last:%d %b %Y}"


def format_title(
    product: str, period: str | None = None, region: str | None = None, units: str = "mm"
) -> str:
    """Build a map title with product name, quantity, region, period and units.

    >>> format_title("accumulation", "May 2024", "Brazil")
    'MERGE accumulated precipitation – Brazil, May 2024 (mm)'
    """
    quantity = PRODUCT_NAMES.get(product, product)
    where = ", ".join(part for part in (region, period) if part)
    title = f"{PRODUCT} {quantity}"
    if where:
        title += f" – {where}"
    if units:
        title += f" ({units})"
    return title
