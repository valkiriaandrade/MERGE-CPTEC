# MERGE-CPTEC

> **Project history.** This is the original README, kept for reference. Folder and file
> names have been updated to the current English layout; see the main [README](../README.md).

This repository contains scripts for visualising precipitation data from INPE/CPTEC's MERGE product. MERGE combines precipitation observations from several sources, such as satellites and rain gauges, to create a dataset with high spatial and temporal resolution.

## Description

The MERGE-CPTEC project focuses on visualising precipitation data using CPTEC/INPE's MERGE product.

## Repository structure

- `scripts/`: scripts used to process and analyse the data.
- `data/`: raw and processed data.
- `figures/`: figures generated from the data.

## Prerequisites

Before running the scripts, you will need to install the following Python libraries:

- numpy
- geopandas
- matplotlib
- pygrib
- cartopy
- xarray
- netCDF4

## Images

### Figure 1: Example of monthly accumulated precipitation

![Monthly accumulated precipitation](../figures/accumulated_precipitation_may_2024.png)

### Figure 2: Example of monthly accumulated precipitation - North region

![Monthly accumulated precipitation - North](../figures/accumulated_precipitation_jul_2024_north.png)

### Figure 3: Example of climatology - October

![Climatology](../figures/precipitation_climatology_oct.png)

### Figure 4: Example of monthly precipitation anomaly in mm

![Anomaly in mm](../figures/precipitation_anomaly_jul_2024.png)

### Figure 5: Example of monthly precipitation anomaly in standard deviations

![Anomaly in standard deviations](../figures/precipitation_anomaly_spread_jun_2024.png)

## How to use

1. Clone this repository:
    ```bash
    git clone https://github.com/valkiriaandrade/merge-rainfall-maps.git
    ```

2. Go to the project folder:
    ```bash
    cd merge-rainfall-maps
    ```

3. Run the scripts as needed.

## Contributing

Contributions are welcome! Feel free to open issues and pull requests.

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.
