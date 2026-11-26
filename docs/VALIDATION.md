# Refactoring validation

- Python 3.11 on Windows: tests for accumulation, grids, missing values,
  interpolation, coordinates, file closing and offline map rendering.
- Real precipitation read: 924 × 1001 grid; ecCodes identifies the parameter in the
  provided files as `Precipitation from radar`, in kg/m² (= mm).
- Produced the May accumulation, the existing July anomaly map and a new July anomaly
  NetCDF from the original files and the repository climatology.
- Editable install of the package and Ruff checks executed.

Only files on the same grid can be summed. The sum is interpolated once, by linear
triangulation, to the climatology grid. NaNs propagate; outside the source grid
coverage the result stays missing. Missing days are not filled in. The input directory
must contain exactly the desired period. `anomaly-spread` computes the spatial spread
after the geographic mask; it is not a historical standard deviation or a climate
probability.

## English translation and figure regeneration (v0.2.0)

- Folders and files renamed to English; code, CLI help, messages, titles and labels
  translated. Calculations are unchanged. (This first English version used `YlGnBu` and
  `BrBG`; commit 8680cb1 ("Restore the original colour scales") brought back the palettes and class
  levels of the original scripts, listed in `src/merge_cptec/colour_scales.py`.)
- New anomaly NetCDF files use the variable name `precipitation_anomaly`; the bundled
  sample files keep their original name and are still read.
- All five figures in `figures/` regenerated with `make figures`.

## Data download, file check and smooth contours (v0.3.0)

- `scripts/download_data.py` (`make data`) downloads the daily GRIB2 files and monthly
  climatologies from the public CPTEC/INPE server
  (https://ftp.cptec.inpe.br/modelos/tempo/MERGE/GPM/); downloaded files are git-ignored.
- The committed May 2024 folder was missing **10 May**; `make data` adds it, so the May
  accumulation now covers the full month. `make figures` refuses incomplete months.
- **The anomaly file formerly called `precipitation_anomaly_may.nc` holds June 2024**
  (its metadata already said "Junho 2024"). Evidence, recomputing with this package from
  the MERGE data currently on the server:
  - correlation with June 2024: 0.67; with May 2024: 0.21. For reference, the stored July
    file against July recomputed from today's server files: 0.83 (CPTEC has reprocessed
    MERGE since 2024, so exact equality is not possible);
  - mean anomaly over Rio Grande do Sul: stored file +12 mm, June 2024 +18 mm, May 2024
    +245 mm (the May 2024 flood). A May map without the flood signal cannot be May.
  The file was renamed to `precipitation_anomaly_jun.nc` (contents unchanged at that step) and the
  figure to `precipitation_anomaly_spread_jun_2024.png`, titled June 2024.
- Server vintage: CPTEC has reprocessed MERGE since 2024. All raw MERGE files in the
  repository were switched to the current server versions with
  `python scripts/download_data.py --months 2024-05 2024-07 --climatology oct --overwrite`
  (61 daily GRIB2 files and the July/October climatologies), and the accumulation and
  climatology figures were regenerated. The October climatology changed visibly (drier over
  much of the Amazon and the north-east). The two anomaly NetCDF files are derived
  products, not server files; see the next point.
- The anomaly NetCDF files are now rebuilt from the raw data. `make data` also downloads
  June 2024 (30 daily files) and the June climatology, and `make figures` first runs
  `merge-cptec --product anomaly-netcdf` for July (`merge_daily_jul_2024` +
  `MERGE_CPTEC_acum_jul.nc`) and June (`merge_daily_jun_2024` + `MERGE_CPTEC_acum_jun.nc`),
  then draws the maps. Without those inputs it keeps the committed files.
  - Same calculation: run on the July 2024 files as committed before the server switch, the
    command reproduces the previous `precipitation_anomaly_jul.nc` to within 0.00002 mm
    (float rounding).
  - With the current server files the fields change: correlation with the previous files
    0.83 (July) and 0.67 (June); mean over the grid −29 → −19 mm (July) and −24 → +5 mm
    (June). The largest change is over the Amazon, where the dry anomalies are much weaker
    (Amazonas mean, July −47 → −18 mm; June −60 → −22 mm). The southern pattern stays.
  - The July anomaly and June categories maps were regenerated. The rebuilt files use the
    variable name `precipitation_anomaly`; the old name is still read.
  - `anomaly-netcdf` stores the values as 32-bit floats, like the original files (coordinates
    unchanged). Against a 64-bit write the values differ by at most 0.00003 mm, the maps are
    byte-identical, and each file is 1.5 MB instead of 3.1 MB.
- Maps are drawn with filled contours (`contourf`) as in the original scripts.

## Code review fixes (v0.3.0, 2026-11-26)

- The `merge-cptec` command now checks the period itself, not only `make figures`:
  `anomaly-netcdf` refuses daily files that are not one whole month (`--allow-partial`
  overrides) or a climatology of another month (read from its `_jul`/`_jun` file name). An
  accumulation of a partial month is still drawn, with a warning, and its title gives the
  dates instead of the month name.
- The categories map title no longer says "(mm)": the classes have no unit.
- The read-me link in the README and the data terms pointed to `READ_ME-MERGE.pdf`, which
  now returns 404; the current file is `MERGE_READ-ME.pdf`.
- Climatology period: CPTEC's read-me for `CLIMATOLOGY/MONTHLY_ACCUMULATED` gives 1998–2024,
  which includes the 2024 months mapped here; now stated in the README.
- `make figures` rebuilt both anomaly NetCDF files byte-identical.
- Categories map (`anomaly-spread`), approved change of the class bounds: the original script
  used m + k·σ with k = −2…3, so "near average" was m to m + σ (entirely above the mean) and
  "well below" started at m − σ while "well above" needed m + 2σ. The classes are now symmetric
  about the mean: < m − 2σ, m − 2σ to m − σ, m ± σ, m + σ to m + 2σ, > m + 2σ, with the same
  five colours; the colorbar labels give the bounds. `figures/precipitation_anomaly_spread_jun_2024.png`
  regenerated: most of the country is now "near average"; the extremes are a dry area over
  southern Paraná and Santa Catarina and wet areas over northern Rio Grande do Sul and Roraima.
