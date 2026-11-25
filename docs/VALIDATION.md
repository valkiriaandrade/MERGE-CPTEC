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
