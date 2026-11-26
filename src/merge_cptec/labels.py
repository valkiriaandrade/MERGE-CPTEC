"""Human-readable labels for map titles and colorbars."""

from __future__ import annotations

import calendar
import re
from collections.abc import Iterable, Sequence
from datetime import date
from pathlib import Path

PRODUCT = "MERGE"
SOURCE_CREDIT = "Data: CPTEC/INPE MERGE"
#: Base period of CPTEC's MERGE monthly climatologies (``CLIMATOLOGY/MONTHLY_ACCUMULATED``
#: read-me); it includes 2024, the year of the anomalies in this repository.
CLIMATOLOGY_PERIOD = "1998-2024"
#: Reference paper of the MERGE product.
MERGE_REFERENCE = (
    "Rozante, J. R., Moreira, D. S., de Goncalves, L. G. G. and Vila, D. A. (2010). "
    "Combining TRMM and surface observations of precipitation: technique and validation "
    "over South America. Weather and Forecasting, 25(3), 885-894. "
    "https://doi.org/10.1175/2010WAF2222325.1"
)

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


def month_coverage_problem(dates: Sequence[date]) -> str | None:
    """Why ``dates`` are not exactly the days of one calendar month; ``None`` if they are.

    >>> from datetime import timedelta
    >>> july = [date(2024, 7, 1) + timedelta(days=n) for n in range(31)]
    >>> month_coverage_problem(july) is None
    True
    >>> month_coverage_problem(july[:10] + july[11:])
    '1 of 31 days of July 2024 missing (11 Jul)'
    """
    if not dates:
        return "no dated daily files (names must contain YYYYMMDD)"
    months = sorted({(d.year, d.month) for d in dates})
    if len(months) > 1:
        (y0, m0), (y1, m1) = months[0], months[-1]
        return f"the files span {len(months)} months ({y0}-{m0:02d} to {y1}-{m1:02d})"
    year, month = months[0]
    days = calendar.monthrange(year, month)[1]
    missing = sorted({date(year, month, d) for d in range(1, days + 1)} - set(dates))
    if missing:
        shown = ", ".join(f"{d:%d %b}" for d in missing[:5]) + (", …" if len(missing) > 5 else "")
        return (
            f"{len(missing)} of {days} days of {calendar.month_name[month]} {year} missing "
            f"({shown})"
        )
    if len(dates) != len(set(dates)):
        return f"{len(dates) - len(set(dates))} day(s) appear in more than one file"
    return None


def format_period(dates: Iterable[date]) -> str | None:
    """Describe a list of dates: ``"July 2024"`` for a whole month, otherwise a date range.

    A month with missing days is shown as the range of days present, so a partial month
    is never titled as the whole month.
    """
    dates = sorted(dates)
    if not dates:
        return None
    first, last = dates[0], dates[-1]
    if month_coverage_problem(dates) is None:
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
