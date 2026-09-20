import numpy as np
import pytest
import xarray as xr

from merge_cptec import processing


def test_accumulation_and_missing(monkeypatch):
    lat, lon = np.meshgrid([0.0, 1.0], [0.0, 1.0])
    monkeypatch.setattr(
        processing,
        "read_grib",
        lambda path, name: (np.array([[2.0, np.nan], [4.0, 6.0]]), lat, lon, ""),
    )
    total, _, _ = processing.accumulate(["a", "b"])
    np.testing.assert_allclose(total, [[4, np.nan], [8, 12]])


def test_grid_mismatch(monkeypatch):
    monkeypatch.setattr(
        processing,
        "read_grib",
        lambda path, name: (np.ones((2, 2)), np.ones((2, 2)) * path, np.zeros((2, 2)), ""),
    )
    with pytest.raises(ValueError, match="Grades"):
        processing.accumulate([1, 2])


def test_empty():
    with pytest.raises(ValueError):
        processing.accumulate([])


def test_repository_grib_parameter_alias():
    from pathlib import Path

    pytest.importorskip("eccodes")
    path = Path(__file__).parents[1] / "Dados/mai/MERGE_CPTEC_20240501.grib2"
    total, lat, lon = processing.accumulate([path])
    assert total.shape == lat.shape == lon.shape == (924, 1001)
    assert np.nanmin(total) >= 0


def test_spread_requires_geographic_mask(tmp_path):
    from merge_cptec.plotting import plot_map

    with pytest.raises(ValueError, match="shapefile"):
        plot_map(
            [[1.0, 2.0], [3.0, 4.0]],
            [0, 1],
            [0, 1],
            tmp_path / "map.png",
            title="Teste",
            label="mm",
            levels=[0, 5],
            cmap="BrBG",
            spatial_spread=True,
        )


def test_anomaly_single_time_and_longitude_conversion(tmp_path, monkeypatch):
    lon, lat = np.meshgrid([-1.0, 0.0], [0.0, 1.0])
    monkeypatch.setattr(processing, "accumulate", lambda files: (np.ones((2, 2)) * 12, lat, lon))
    path = tmp_path / "clim.nc"
    xr.Dataset(
        {"precacum": (("time", "lat", "lon"), np.ones((1, 2, 2)) * 10)},
        coords={"time": [0], "lat": [0.0, 1.0], "lon": [359.0, 0.0]},
    ).to_netcdf(path, engine="h5netcdf")
    result = processing.anomaly(["a"], path)
    np.testing.assert_allclose(result, 2.0)
    assert result.dims == ("lat", "lon")
