"""Colour scales of each product, restored from the original project scripts.

The palettes, class boundaries and colorbar extensions below are the ones used by the
original ``Scripts/*.py`` (before the package refactor), so the maps keep their
historical look while sharing the common figure style.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

#: 14-colour rainfall scale of the original ``acumulado_mensal_norte.py`` and
#: ``climatologia.py`` (light blue → blue → green → yellow → red → magenta → purple).
RAINFALL_COLOURS = (
    "#14CAFA", "#007CAF", "#011495", "#00FC15", "#00A20B", "#006606", "#FAFB00",
    "#FFDF66", "#F99901", "#FB0400", "#AE0001", "#810003", "#F203FC", "#814AE7",
)  # fmt: skip
RAINFALL_LEVELS = (0, 10, 20, 30, 40, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500)

#: Original ``acumulado_mensal.py`` (Brazil): 9 classes of the reversed rainbow.
BRAZIL_ACCUMULATION_LEVELS = (0, 20, 50, 80, 100, 150, 200, 300, 400, 500)

#: Original ``anomalia_mm.py``.
ANOMALY_LEVELS = (-400, -300, -200, -100, -75, -50, -25, -5, 0, 5, 25, 50, 75, 100, 200, 300, 400)

#: Five classes of the field's spatial mean m ± k standard deviations σ (colours of the
#: original ``anomalia_desvio.py``). The classes are symmetric about the mean: below
#: m − 2σ, m − 2σ to m − σ, m ± σ, m + σ to m + 2σ, above m + 2σ. (The original script
#: used m + k·σ with k = −2…3, so "near average" was m to m + σ, entirely above the mean.)
SPREAD_COLOURS = ("#E73B29", "#CADF00", "#00D03F", "#00B9DD", "#4E54D7")
SPREAD_LABELS = (
    "Well below\n(< −2σ)",
    "Below\n(−2σ to −σ)",
    "Near average\n(±σ)",
    "Above\n(σ to 2σ)",
    "Well above\n(> 2σ)",
)
#: Class boundaries in units of σ around the mean. The outer ±3 only close the end classes
#: for drawing: values beyond them keep the end colours ("well below/above" are open-ended).
SPREAD_K = (-3.0, -2.0, -1.0, 1.0, 2.0, 3.0)


def spread_levels(values) -> np.ndarray:
    """Class boundaries ``m + k·σ`` (k in :data:`SPREAD_K`) of the finite ``values``.

    ``values`` must already be masked to the region (NaN outside), so the mean and the
    standard deviation describe the mapped area only.

    >>> spread_levels(np.array([1.0, 3.0, np.nan])).tolist()
    [-1.0, 0.0, 1.0, 3.0, 4.0, 5.0]

    Raises:
        ValueError: if the field is constant (σ = 0).
    """
    mean, std = np.nanmean(values), np.nanstd(values)
    if std == 0:
        raise ValueError("Spatial spread is zero: the field is constant over the region")
    return mean + np.asarray(SPREAD_K) * std


@dataclass(frozen=True)
class ColourScale:
    """Palette, class boundaries and colorbar settings for one map."""

    levels: tuple[float, ...]
    cmap: object
    extend: str = "both"
    class_labels: tuple[str, ...] | None = None


def colour_scale(product: str, region: str = "brazil") -> ColourScale:
    """Return the original colour scale for ``product`` (and ``region`` for accumulations).

    For ``anomaly-spread`` the levels are placeholders: the plot replaces them with the
    field's spatial mean + k·std for k in :data:`SPREAD_K`.
    """
    from matplotlib import colormaps
    from matplotlib.colors import ListedColormap

    if product == "anomaly":
        return ColourScale(ANOMALY_LEVELS, "BrBG", "both")
    if product == "anomaly-spread":
        return ColourScale(ANOMALY_LEVELS, ListedColormap(SPREAD_COLOURS), "both", SPREAD_LABELS)
    if product == "climatology" or (product == "accumulation" and region == "north"):
        return ColourScale(RAINFALL_LEVELS, ListedColormap(RAINFALL_COLOURS), "max")
    if product == "accumulation":
        classes = len(BRAZIL_ACCUMULATION_LEVELS) - 1
        return ColourScale(
            BRAZIL_ACCUMULATION_LEVELS, colormaps["rainbow_r"].resampled(classes), "max"
        )
    raise ValueError(f"No colour scale for product {product!r}")
