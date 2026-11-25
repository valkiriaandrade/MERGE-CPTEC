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
  translated. Calculations, palettes (`YlGnBu`, `BrBG`) and class levels are unchanged.
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
  The file was renamed to `precipitation_anomaly_jun.nc` (contents unchanged) and the
  figure to `precipitation_anomaly_spread_jun_2024.png`, titled June 2024.
- Server vintage: the daily files, climatologies and July anomaly committed in 2024 differ
  from the files on the server today (reprocessing). Committed files were kept unchanged;
  the 10 May file and the May climatology come from the current server version.
- Maps are drawn with filled contours (`contourf`) as in the original scripts.
