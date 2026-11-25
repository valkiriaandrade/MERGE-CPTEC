import io
import socket
import urllib.error
from datetime import date

import pytest


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_plan_daily_grib_and_climatology(download_module):
    items = download_module.plan(date(2024, 6, 1))
    assert len(items) == 31  # 30 days + climatology
    first, clim = items[0], items[-1]
    assert first.url.endswith("/MERGE/GPM/DAILY/2024/06/MERGE_CPTEC_20240601.grib2")
    assert first.path.as_posix() == "merge_daily_jun_2024/MERGE_CPTEC_20240601.grib2"
    assert clim.url.endswith("/CLIMATOLOGY/MONTHLY_ACCUMULATED/MERGE_CPTEC_acum_jun.nc")
    assert clim.path.as_posix() == "MERGE_CPTEC_acum_jun.nc"


def test_default_plan_covers_make_figures(download_module):
    from conftest import load_script

    make_figures = load_script("make_figures")
    planned = set()
    for month in download_module.FIGURE_MONTHS:
        for item in download_module.plan(download_module.parse_month(month)):
            planned.add(item.path.parts[0])
    for mon in download_module.FIGURE_CLIMATOLOGIES:
        index = download_module.MONTH_ABBR.index(mon) + 1
        planned.add(download_module.climatology_item(index).path.name)
    derived = {"precipitation_anomaly_jul.nc", "precipitation_anomaly_jun.nc"}
    needed = {f.source for f in make_figures.FIGURES} - derived
    assert needed <= planned


def test_fetch_downloads_then_skips(tmp_path, download_module):
    calls = []

    def opener(request, timeout):
        calls.append(request.full_url)
        return FakeResponse(b"GRIB")

    dest = tmp_path / "day.grib2"
    assert download_module.fetch("https://x/day.grib2", dest, opener=opener) is True
    assert download_module.fetch("https://x/day.grib2", dest, opener=opener) is False
    assert dest.read_bytes() == b"GRIB" and calls == ["https://x/day.grib2"]


def test_missing_file_gives_clear_error(tmp_path, download_module):
    def opener(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 404, "Not Found", {}, None)

    with pytest.raises(download_module.DownloadError, match="Not found on the server"):
        download_module.fetch("https://x/missing.grib2", tmp_path / "m.grib2", opener=opener)


def test_main_dry_run(capsys, download_module):
    assert download_module.main(["--dry-run", "--climatology", "oct"]) == 0
    assert capsys.readouterr().out.strip().endswith("MERGE_CPTEC_acum_oct.nc")
    with pytest.raises(SystemExit):
        download_module.main(["--months", "May 2024"])


def test_network_is_blocked_in_tests():
    with pytest.raises(RuntimeError, match="must not use the network"):
        socket.create_connection(("ftp.cptec.inpe.br", 443))


def test_make_figures_refuses_incomplete_month(tmp_path):
    from conftest import load_script

    make_figures = load_script("make_figures")
    folder = tmp_path / "merge_daily_feb_2024"
    folder.mkdir()
    for day in range(1, 29):
        (folder / f"MERGE_CPTEC_202402{day:02d}.grib2").touch()
    assert make_figures.incomplete_month(folder) == "merge_daily_feb_2024 has 28 of 29 daily files"
    (folder / "MERGE_CPTEC_20240229.grib2").touch()
    assert make_figures.incomplete_month(folder) is None
    assert make_figures.incomplete_month(tmp_path / "precipitation_anomaly_jun.nc") is None
