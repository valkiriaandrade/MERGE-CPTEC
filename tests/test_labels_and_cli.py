import argparse
from datetime import date

import numpy as np
import pytest
import xarray as xr

from merge_cptec.arguments import positive_int
from merge_cptec.cli import build_cli, read_anomaly
from merge_cptec.labels import (
    dates_from_names,
    format_period,
    format_title,
    is_precipitation_mm,
    month_from_name,
    units_label,
)
from merge_cptec.regions import REGIONS, normalize_region


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("brazil", "brazil"),
        ("north", "north"),
        ("brasil", "brazil"),
        ("norte", "north"),
        ("NORTE", "north"),
        (" North ", "north"),
    ],
)
def test_region_names_and_portuguese_aliases(value, expected):
    assert normalize_region(value) == expected


def test_unknown_region_lists_accepted_values():
    with pytest.raises(argparse.ArgumentTypeError, match="brazil, north, brasil, norte"):
        normalize_region("east")


@pytest.mark.parametrize("alias", ["norte", "north"])
def test_cli_accepts_region_alias(alias):
    args = build_cli().parse_args(["--input", "d", "--output", "o.png", "--region", alias])
    assert args.region == "north"
    assert "AM" in REGIONS[args.region].states


def test_cli_dpi_default_and_validation():
    base = ["--input", "d", "--output", "o.png"]
    assert build_cli().parse_args(base).dpi == 200
    assert build_cli().parse_args([*base, "--dpi", "300"]).dpi == 300
    with pytest.raises(argparse.ArgumentTypeError):
        positive_int("-5")


@pytest.mark.parametrize(
    ("units", "label", "is_mm"),
    [
        ("kg m**-2", "mm", True),
        ("kg m-2", "mm", True),
        ("mm", "mm", True),
        ("m", "m", False),
        ("kg m**-2 s**-1", "kg m**-2 s**-1", False),
        (None, "", False),
    ],
)
def test_precipitation_unit_conversion(units, label, is_mm):
    # 1 kg m⁻² of water over a square metre is a 1 mm layer, so no scaling is applied.
    assert units_label(units) == label
    assert is_precipitation_mm(units) is is_mm


def test_period_from_provider_file_names():
    names = [f"MERGE_CPTEC_202405{day:02d}.grib2" for day in (1, 15, 31)]
    assert dates_from_names(names)[-1] == date(2024, 5, 31)
    assert format_period(dates_from_names(names)) == "May 2024"
    assert format_period([]) is None
    assert month_from_name("data/MERGE_CPTEC_acum_oct.nc") == "October"
    assert month_from_name("precipitation_anomaly_jun.nc") == "June"
    assert month_from_name("climatology.nc") is None


def test_title_formatting():
    assert (
        format_title("accumulation", "July 2024", "Northern Brazil")
        == "MERGE accumulated precipitation – Northern Brazil, July 2024 (mm)"
    )
    assert (
        format_title("climatology", "October", "Brazil")
        == "MERGE precipitation climatology – Brazil, October (mm)"
    )
    assert format_title("anomaly") == "MERGE precipitation anomaly (mm)"


@pytest.mark.parametrize("name", ["precipitation_anomaly", "anomalia_precipitacao"])
def test_read_anomaly_current_and_legacy_variable(tmp_path, name):
    path = tmp_path / "anomaly.nc"
    xr.Dataset(
        {name: (("lat", "lon"), [[1.0, -2.0]])}, coords={"lat": [0], "lon": [0, 1]}
    ).to_netcdf(path, engine="h5netcdf")
    np.testing.assert_allclose(read_anomaly(path), [[1.0, -2.0]])
