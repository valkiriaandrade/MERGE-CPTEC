import subprocess
import sys

import numpy as np
import pytest
import xarray as xr

from merge_cptec.io import files_in, read_field, save_netcdf, spatial


def test_empty_directory(tmp_path):
    with pytest.raises(ValueError, match="No .nc files"):
        files_in(tmp_path, ".nc")


def test_missing_variable_and_loaded_data(tmp_path):
    path = tmp_path / "sample.nc"
    xr.Dataset(
        {"t": (("lat", "lon"), [[1.0, 2.0], [3.0, 4.0]])}, coords={"lat": [0, 1], "lon": [10, 11]}
    ).to_netcdf(path, engine="h5netcdf")
    with pytest.raises(ValueError, match="missing"):
        read_field(path, "missing")
    field = read_field(path, "t")
    path.unlink()  # The file handle is already closed, also on Windows.
    np.testing.assert_array_equal(field, [[1, 2], [3, 4]])


def test_spatial_preserves_singleton_lat_and_rejects_ambiguous_time():
    field = xr.DataArray(np.ones((2, 1, 2)), dims=("time", "lat", "lon"))
    with pytest.raises(ValueError, match="single index"):
        spatial(field)
    assert spatial(field.isel(time=[0])).shape == (1, 2)


def test_import_has_no_output(tmp_path):
    # A fresh interpreter: in this test session the package is already imported.
    code = "import merge_cptec.cli, merge_cptec.plotting, sys; sys.exit('matplotlib.pyplot' in sys.modules)"
    subprocess.run([sys.executable, "-c", code], cwd=tmp_path, check=True)
    assert not list(tmp_path.iterdir())


def test_offline_map_and_figure_cleanup(tmp_path):
    import geopandas as gpd
    import matplotlib.pyplot as plt
    from shapely.geometry import box

    from merge_cptec.plotting import plot_map

    borders = tmp_path / "bounds.geojson"
    gpd.GeoDataFrame(geometry=[box(-2, -2, 2, 2)], crs=4326).to_file(borders)
    output = tmp_path / "maps" / "sample.png"
    plot_map(
        [[1, 2], [3, 4]],
        [-1, 1],
        [359, 1],
        output,
        title="Test",
        label="mm",
        levels=[0, 2, 5],
        cmap="BrBG",
        shapefile=borders,
    )
    assert output.read_bytes().startswith(b"\x89PNG")
    assert not plt.get_fignums()


def test_save_netcdf_stores_values_as_float32(tmp_path):
    lat = np.array([-10.05, -9.95])
    field = xr.DataArray(
        np.array([[1.25, np.nan], [-3.5, 400.123456]]),
        dims=("lat", "lon"),
        coords={"lat": lat, "lon": [-50.05, -49.95]},
        name="precipitation_anomaly",
    )
    output = tmp_path / "out" / "anomaly.nc"
    save_netcdf(field, output)
    with xr.open_dataset(output, engine="h5netcdf") as saved:
        values = saved["precipitation_anomaly"]
        assert values.encoding["dtype"] == np.float32
        assert saved.lat.dtype == np.float64 and np.array_equal(saved.lat, lat)
        np.testing.assert_allclose(values, field, rtol=1e-6)
        assert np.isnan(values[0, 1])
