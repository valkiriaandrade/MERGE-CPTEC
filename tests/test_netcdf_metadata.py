"""CF metadata of the anomaly NetCDF files: period, climatology base period and source."""

import pytest
import xarray as xr
from conftest import ROOT
from test_pipeline import climatology, month_folder, template  # noqa: F401  (fixtures)

from merge_cptec import cli
from merge_cptec.labels import CLIMATOLOGY_PERIOD

DOI = "https://doi.org/10.1175/2010WAF2222325.1"


def check_metadata(path, period, start, end, month, days):
    """Assert the CF / ACDD attributes that every anomaly file must carry."""
    with xr.open_dataset(path, engine="h5netcdf") as dataset:
        attrs = dataset.attrs
        variable = dataset["precipitation_anomaly"]
        assert attrs["Conventions"] == "CF-1.8"
        # period mapped
        assert (
            attrs["period"] == period and attrs["title"] == f"MERGE precipitation anomaly, {period}"
        )
        assert (attrs["time_coverage_start"], attrs["time_coverage_end"]) == (start, end)
        # climatology base period, as in CPTEC's read-me
        assert attrs["climatology_period"] == CLIMATOLOGY_PERIOD == "1998-2024"
        assert attrs["climatology_month"] == month
        assert attrs["climatology_file"] == f"MERGE_CPTEC_acum_{month[:3].lower()}.nc"
        assert "1998-2024" in attrs["comment"] and "read-me" in attrs["comment"]
        # data source and reference
        assert "CPTEC/INPE MERGE" in attrs["source"] and "CPTEC/INPE" in attrs["institution"]
        assert attrs["references"].startswith("Rozante, J. R.") and "(2010)" in attrs["references"]
        assert DOI in attrs["references"]
        # variable: CF long_name and units
        assert variable.attrs["units"] == "mm"
        assert variable.attrs["long_name"] == (
            f"precipitation anomaly: {period} total minus the 1998-2024 {month} mean"
        )
        assert variable.attrs["source_file_count"] == days
        assert dataset.lat.attrs["standard_name"] == "latitude"
        assert dataset.lat.attrs["units"] == "degrees_north"
        assert dataset.lon.attrs["standard_name"] == "longitude"
        assert dataset.lon.attrs["units"] == "degrees_east"
        assert "date_created" not in attrs  # no timestamp: rebuilding gives the same bytes


@pytest.mark.parametrize(
    ("name", "period", "start", "end", "month", "days"),
    [
        ("precipitation_anomaly_jul.nc", "July 2024", "2024-07-01", "2024-07-31", "July", 31),
        ("precipitation_anomaly_jun.nc", "June 2024", "2024-06-01", "2024-06-30", "June", 30),
    ],
)
def test_committed_anomaly_files_carry_their_metadata(name, period, start, end, month, days):
    check_metadata(ROOT / "data" / name, period, start, end, month, days)


def test_anomaly_netcdf_command_writes_the_metadata_reproducibly(month_folder, tmp_path):  # noqa: F811
    folder = month_folder(2024, 7)
    clim = climatology(tmp_path / "MERGE_CPTEC_acum_jul.nc")
    outputs = [tmp_path / "a.nc", tmp_path / "b.nc"]
    for output in outputs:
        cli.main(
            ["--product", "anomaly-netcdf", "--input", str(folder), "--climatology", str(clim)]
            + ["--output", str(output)]
        )
    check_metadata(outputs[0], "July 2024", "2024-07-01", "2024-07-31", "July", 31)
    assert outputs[0].read_bytes() == outputs[1].read_bytes()
