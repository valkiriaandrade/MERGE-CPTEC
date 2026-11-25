# MERGE-CPTEC

Weather data processing and visualisation project by Valkiria Andrade.
The code is organised as a Python package with a command-line interface,
regression tests and automated checks on GitHub Actions.

<img src="Figuras/Acum_PRP_Mai_2024.png" alt="Accumulated rainfall map for Brazil, May 2024" width="480"/>

## Installation

Python 3.10 or later. From this repository's folder:

```bash
python -m venv .venv
# Windows PowerShell: .venv/Scripts/Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[dev]"
```

WRF and MERGE also need ecCodes: `python -m pip install -e ".[grib]"`.
The ecCodes package ships binaries for Windows, Linux and macOS. NetCDF, calculations and
maps do not depend on this extra. GRIB files are read directly with ecCodes, replacing pygrib.

## Usage

Example (check your files' names and metadata):

```bash
merge-cptec --input Dados/mai --product accumulation --title "Accumulated rainfall — May 2024" --output output/accumulation.png
merge-cptec --help
```

The accumulation sums the daily files in the folder: keep only the desired period, with no duplicates. `--product anomaly-netcdf` requires `--climatology` and saves a NetCDF; `--product anomaly` reads that NetCDF to draw the map. `--product climatology` reads `precacum`. `--region norte` crops northern Brazil (use `--shapefile` for a state mask). `anomaly-spread` uses the field's spatial spread, not a climatological standard deviation or probabilistic categories.

`--shapefile path/BR_UF_2022.shp` applies a mask and local boundaries; the file
must come with its auxiliary files and CRS. ZIP files must be extracted first.
Without a shapefile, Cartopy may download Natural Earth cartography on first use.
`--title` sets the title and `--verbose` shows error details.
Maps are saved without opening windows. The output folder is created automatically.

## Architecture and maintenance

- `src/merge_cptec/io.py`: reading, resource cleanup and grid validation.
- `src/merge_cptec/cli.py`: arguments and processing coordination.
- `src/merge_cptec/plotting.py`: rendering and geographic masking.
- `Scripts/`: entry points with the historical names, using the installed package.
- `tests/`: synthetic data and regression tests independent of external services.
- `Dados/` and `Figuras/`: original data and figures, preserved.

The historical entry points now require the same arguments as the CLI. Paths,
dates and files that used to be hard-coded must be passed explicitly.
Palettes and resolution were standardised; figures are not pixel-perfect copies
of the old versions. Missing values are not converted to zero.

```bash
pytest -q
ruff check src Scripts tests
```

CI runs the tests on Python 3.10 and 3.12. Tests use small synthetic data
and local cartography; scientific interpretation and period coverage should be
checked against operational data.

History, scientific background and images: [original README](docs/README-original.md).
