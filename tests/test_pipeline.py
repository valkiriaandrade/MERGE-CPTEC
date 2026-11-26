"""The merge-cptec command run end to end on tiny GRIB2 / NetCDF files (offline)."""

import calendar
import sys
from types import SimpleNamespace

import numpy as np
import pytest
import xarray as xr
from conftest import ROOT, load_script

from merge_cptec import cli, colour_scales, processing
from merge_cptec.io import read_grib

ec = pytest.importorskip("eccodes")

#: Source grid of the tiny daily files: 0.5° steps, 32–28° S, 60–56° W.
LATS = np.arange(-32.0, -27.9, 0.5)
LONS = np.arange(-60.0, -55.9, 0.5)


def rain(lat, lon):
    """Daily rain that varies differently with latitude and longitude (mm)."""
    return 10.0 + 2.0 * (lat + 32.0) + 0.5 * (lon + 60.0)


@pytest.fixture(scope="module")
def template():
    """One real MERGE GRIB2 message (committed July 2024 sample), used as a template."""
    path = next((ROOT / "data" / "merge_daily_jul_2024").glob("*.grib2"))
    with path.open("rb") as stream:
        message = ec.codes_grib_new_from_file(stream)
    try:
        return ec.codes_get_message(message)
    finally:
        ec.codes_release(message)


@pytest.fixture
def month_folder(tmp_path, template):
    """Write ``MERGE_CPTEC_YYYYMMDD.grib2`` files for the given days on the tiny grid."""

    def make(year, month, days=None, name=None):
        days = days or range(1, calendar.monthrange(year, month)[1] + 1)
        folder = tmp_path / (name or f"merge_daily_{calendar.month_abbr[month].lower()}_{year}")
        folder.mkdir()
        lon2d, lat2d = np.meshgrid(LONS, LATS)
        for day in days:
            message = ec.codes_new_from_message(template)
            try:
                ec.codes_set_long(message, "Ni", LONS.size)
                ec.codes_set_long(message, "Nj", LATS.size)
                ec.codes_set(message, "latitudeOfFirstGridPointInDegrees", LATS[0])
                ec.codes_set(message, "latitudeOfLastGridPointInDegrees", LATS[-1])
                ec.codes_set(message, "longitudeOfFirstGridPointInDegrees", LONS[0] + 360)
                ec.codes_set(message, "longitudeOfLastGridPointInDegrees", LONS[-1] + 360)
                ec.codes_set(message, "iDirectionIncrementInDegrees", 0.5)
                ec.codes_set(message, "jDirectionIncrementInDegrees", 0.5)
                ec.codes_set(message, "dataDate", int(f"{year}{month:02d}{day:02d}"))
                ec.codes_set_values(message, rain(lat2d, lon2d).ravel())
                path = folder / f"MERGE_CPTEC_{year}{month:02d}{day:02d}.grib2"
                path.write_bytes(ec.codes_get_message(message))
            finally:
                ec.codes_release(message)
        return folder

    return make


def climatology(path, value=100.0):
    """A ``precacum`` file on a 1° grid offset from the daily grid (lon in 0–360)."""
    lat, lon = np.array([-31.5, -30.5, -29.5, -26.0]), np.array([300.25, 301.75, 303.25])
    xr.Dataset(
        {"precacum": (("time", "lat", "lon"), np.full((1, lat.size, lon.size), value))},
        coords={"time": [0], "lat": lat, "lon": lon},
    ).to_netcdf(path, engine="h5netcdf")
    return path


@pytest.fixture
def drawn(monkeypatch):
    """What the CLI passes to plot_map (nothing is drawn)."""
    calls = []
    monkeypatch.setattr(
        cli,
        "plot_map",
        lambda values, lat, lon, output, **kw: calls.append(
            SimpleNamespace(values=values, lat=lat, lon=lon, **kw)
        ),
    )
    return calls


# ---------------------------------------------------------------- reading and accumulation
def test_tiny_grib_is_read_on_the_right_grid(month_folder):
    folder = month_folder(2024, 7, [1])
    values, lat, lon, valid = read_grib(next(folder.iterdir()), "Precipitation")
    assert lat[0, 0] == -32.0 and lat[-1, 0] == -28.0 and lon[0, 0] == -60.0 and lon[0, -1] == -56.0
    assert values[0, 0] == pytest.approx(10.0) and values[-1, 0] == pytest.approx(18.0)
    assert values[0, -1] == pytest.approx(12.0) and valid.startswith("2024-07-01")


def test_accumulation_command_sums_every_day(month_folder, drawn):
    folder = month_folder(2024, 7)
    cli.main(["--input", str(folder), "--output", "unused.png"])
    [call] = drawn
    lon2d, lat2d = np.meshgrid(LONS, LATS)
    np.testing.assert_allclose(call.values, 31 * rain(lat2d, lon2d), rtol=1e-5)
    assert call.title == "MERGE accumulated precipitation – Brazil, July 2024 (mm)"


def test_partial_month_accumulation_is_titled_with_its_dates(month_folder, drawn, caplog):
    folder = month_folder(2024, 7, range(1, 16))
    cli.main(["--input", str(folder), "--output", "unused.png"])
    assert drawn[0].title.endswith("Brazil, 01 Jul 2024 to 15 Jul 2024 (mm)")
    assert "16 of 31 days of July 2024 missing" in caplog.text


# ---------------------------------------------------------------- anomaly NetCDF
def test_anomaly_is_interpolated_to_the_climatology_grid(month_folder, tmp_path):
    folder = month_folder(2024, 7)
    clim = climatology(tmp_path / "MERGE_CPTEC_acum_jul.nc")
    result = processing.anomaly(sorted(folder.glob("*.grib2")), clim)
    assert result.dims == ("lat", "lon") and result.lon.values.tolist() == [300.25, 301.75, 303.25]
    # rain() is linear, so linear interpolation is exact at every inside point
    for i, lat in enumerate(result.lat.values[:3]):
        for j, lon in enumerate(result.lon.values - 360):
            assert float(result[i, j]) == pytest.approx(31 * rain(lat, lon) - 100, rel=1e-5)
    assert np.isnan(result.values[3]).all()  # 26° S is outside the daily grid: stays missing


def test_anomaly_netcdf_command_and_its_checks(month_folder, tmp_path, capsys):
    folder = month_folder(2024, 7)
    output = tmp_path / "anomaly.nc"
    clim_jul = climatology(tmp_path / "MERGE_CPTEC_acum_jul.nc")
    clim_jun = climatology(tmp_path / "MERGE_CPTEC_acum_jun.nc")
    args = ["--product", "anomaly-netcdf", "--input", str(folder), "--output", str(output)]
    cli.main([*args, "--climatology", str(clim_jul)])
    saved = cli.read_anomaly(output)
    assert saved.dtype == np.float32 and saved.attrs["source_file_count"] == 31

    with pytest.raises(SystemExit):  # climatology of another month
        cli.main([*args, "--climatology", str(clim_jun)])
    assert "the climatology MERGE_CPTEC_acum_jun.nc is for June" in capsys.readouterr().err


def test_anomaly_netcdf_refuses_a_partial_month_unless_allowed(month_folder, tmp_path, capsys):
    folder = month_folder(2024, 7, [d for d in range(1, 32) if d != 10])
    clim = climatology(tmp_path / "MERGE_CPTEC_acum_jul.nc")
    output = tmp_path / "anomaly.nc"
    args = ["--product", "anomaly-netcdf", "--input", str(folder), "--climatology", str(clim)]
    with pytest.raises(SystemExit):
        cli.main([*args, "--output", str(output)])
    assert "1 of 31 days of July 2024 missing (10 Jul)" in capsys.readouterr().err
    assert not output.exists()
    cli.main([*args, "--output", str(output), "--allow-partial"])
    assert cli.read_anomaly(output).attrs["source_file_count"] == 30


# ---------------------------------------------------------------- maps from NetCDF files
@pytest.fixture
def anomaly_file(tmp_path):
    """An anomaly field on a 1° grid over southern Brazil: west half dry, east half wet."""
    lat, lon = np.arange(-34.0, -21.9, 1.0), np.arange(-58.0, -47.9, 1.0)
    values = np.where(lon[None, :] < -53, -50.0, 80.0) + 0 * lat[:, None]
    path = tmp_path / "precipitation_anomaly_jun.nc"
    xr.DataArray(
        values.astype("float32"),
        dims=("lat", "lon"),
        coords={"lat": lat, "lon": lon},
        name="precipitation_anomaly",
    ).to_netcdf(path, engine="h5netcdf")
    return path


@pytest.fixture
def south_shapefile(tmp_path):
    import geopandas as gpd
    from shapely.geometry import box

    path = tmp_path / "states.geojson"
    gpd.GeoDataFrame(
        {"SIGLA_UF": ["RS", "SC"]},
        geometry=[box(-57.5, -33.5, -49.5, -27.2), box(-53.8, -29.3, -48.3, -25.9)],
        crs=4326,
    ).to_file(path)
    return path


def test_anomaly_and_climatology_maps(anomaly_file, tmp_path, drawn):
    cli.main(["--product", "anomaly", "--input", str(anomaly_file), "--output", "a.png"])
    clim = climatology(tmp_path / "MERGE_CPTEC_acum_oct.nc", value=120.0)
    cli.main(["--product", "climatology", "--input", str(clim), "--output", "c.png"])
    anomaly_map, clim_map = drawn
    assert anomaly_map.title == "MERGE precipitation anomaly – Brazil, June (mm)"
    assert anomaly_map.levels == colour_scales.ANOMALY_LEVELS and anomaly_map.cmap == "BrBG"
    assert clim_map.title == "MERGE precipitation climatology – Brazil, October (mm)"
    assert clim_map.levels == colour_scales.RAINFALL_LEVELS and np.all(clim_map.values == 120)


def test_categories_map_uses_the_masked_area_and_symmetric_classes(
    anomaly_file, south_shapefile, tmp_path, monkeypatch
):
    seen = []
    real = colour_scales.spread_levels
    monkeypatch.setattr(colour_scales, "spread_levels", lambda v: seen.append(v) or real(v))
    output = tmp_path / "spread.png"
    cli.main(
        ["--product", "anomaly-spread", "--input", str(anomaly_file), "--period", "June 2024"]
        + ["--shapefile", str(south_shapefile), "--output", str(output)]
    )
    assert output.read_bytes().startswith(b"\x89PNG")
    [masked] = seen
    field = cli.read_anomaly(anomaly_file)
    lon2d, lat2d = np.meshgrid(field.lon.values, field.lat.values)
    outside = (lat2d > -25.9) | (lon2d < -57.5)
    assert np.isnan(masked[outside]).all() and np.isfinite(masked[~outside]).any()


def test_spread_classes_are_symmetric_about_the_mean():
    from matplotlib.colors import BoundaryNorm

    values = np.array([-3.0, -1.0, 1.0, 3.0, np.nan])  # mean 0, σ = √5
    levels = colour_scales.spread_levels(values)
    sigma = np.sqrt(5)
    np.testing.assert_allclose(levels, np.array([-3, -2, -1, 1, 2, 3]) * sigma)
    colours = len(colour_scales.SPREAD_COLOURS)
    norm = BoundaryNorm(levels, colours)
    # beyond ±3σ: under/over, drawn with the end colours (open-ended "well below/above")
    classes = np.clip(
        norm(np.array([-0.9, 0.9, -1.5, 1.5, -2.5, 2.5, -9, 9]) * sigma), 0, colours - 1
    )
    labels = [colour_scales.SPREAD_LABELS[c].split("\n")[0] for c in classes]
    assert labels[:2] == ["Near average", "Near average"]  # ±0.9σ: both near average
    assert labels[2:] == ["Below", "Above", "Well below", "Well above", "Well below", "Well above"]
    with pytest.raises(ValueError, match="constant"):
        colour_scales.spread_levels(np.ones(4))


def test_categories_title_has_no_unit(anomaly_file, south_shapefile, drawn):
    cli.main(
        ["--product", "anomaly-spread", "--input", str(anomaly_file)]
        + ["--shapefile", str(south_shapefile), "--output", "s.png"]
    )
    assert drawn[0].title == "MERGE precipitation anomaly, spatial-spread classes – Brazil, June"


# ---------------------------------------------------------------- read_grib checks
class FakeGrib:
    """Stand-in for ecCodes: messages are dicts of keys."""

    def __init__(self, *messages):
        self.messages, self.released = list(messages), []

    def codes_grib_new_from_file(self, stream):
        return self.messages.pop(0) if self.messages else None

    def codes_get(self, message, key):
        return message[key]

    def codes_get_values(self, message):
        return np.asarray(message["values"], dtype=float)

    def codes_get_array(self, message, key):
        return np.asarray(message[key])

    def codes_release(self, message):
        self.released.append(message)


def _rain_message(**changes):
    message = {
        "name": "Precipitation from radar",
        "units": "kg m**-2",
        "Ni": 2,
        "Nj": 3,
        "values": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "bitmapPresent": 0,
        "latitudes": [-30.0, -30.0, -29.0, -29.0, -28.0, -28.0],
        "longitudes": [300.0, 301.0, 300.0, 301.0, 300.0, 301.0],
        "jPointsAreConsecutive": 0,
        "validityDate": 20240701,
        "validityTime": 1200,
    }
    return {**message, **changes}


@pytest.fixture
def fake_grib(monkeypatch, tmp_path):
    path = tmp_path / "fake.grib2"
    path.touch()

    def install(*messages):
        fake = FakeGrib(*messages)
        monkeypatch.setitem(sys.modules, "eccodes", fake)
        return fake

    return path, install


def test_read_grib_bitmap_scanning_order_and_longitudes(fake_grib):
    path, install = fake_grib
    install(_rain_message(bitmapPresent=1, bitmap=[1, 1, 1, 0, 1, 1]))
    values, lat, lon, _ = read_grib(path, "Precipitation")
    assert values.shape == (3, 2) and np.isnan(values[1, 1]) and values[2, 0] == 5.0
    assert lat[:, 0].tolist() == [-30, -29, -28] and lon[0].tolist() == [-60, -59]
    install(
        _rain_message(
            jPointsAreConsecutive=1,
            Ni=3,
            Nj=2,
            latitudes=[-30.0, -29.0, -28.0, -30.0, -29.0, -28.0],
            longitudes=[300.0, 300.0, 300.0, 301.0, 301.0, 301.0],
        )
    )
    values, lat, lon, _ = read_grib(path, "Precipitation")
    assert values.shape == (3, 2) and lat[0].tolist() == [-30, -29]  # column-major files keep order


@pytest.mark.parametrize(
    ("messages", "error"),
    [
        ([_rain_message(units="m")], "expected kg m\\*\\*-2 or mm"),
        ([_rain_message(), _rain_message()], "More than one"),
        ([_rain_message(Ni=4)], "regular rectangular grids"),
        ([{"name": "Temperature"}], "not found"),
    ],
)
def test_read_grib_rejects_wrong_fields(fake_grib, messages, error):
    path, install = fake_grib
    fake = install(*messages)
    with pytest.raises(ValueError, match=error):
        read_grib(path, "Precipitation")
    assert len(fake.released) == len(messages)  # every handle released


# ---------------------------------------------------------------- make figures
def test_make_figures_reports_skipped_and_failed(tmp_path, monkeypatch):
    make_figures = load_script("make_figures")
    monkeypatch.setattr(sys, "argv", ["make_figures", "--data-dir", str(tmp_path)])
    assert make_figures.main() == 1  # no data: every figure skipped
    (tmp_path / "bad.nc").write_bytes(b"not netcdf")
    figure = make_figures.FIGURES[-1]
    monkeypatch.setattr(
        make_figures,
        "FIGURES",
        [
            type(figure)(**{**figure.__dict__, "output": "a.png", "source": "bad.nc"}),
            type(figure)(**{**figure.__dict__, "output": "b.png", "source": "absent.nc"}),
            type(figure)(**{**figure.__dict__, "output": "c.png", "source": "bad.nc"}),
        ],
    )
    skipped, failed = make_figures.build(tmp_path, tmp_path / "figures", 50)
    assert skipped == ["b.png"] and failed == ["a.png", "c.png"]
