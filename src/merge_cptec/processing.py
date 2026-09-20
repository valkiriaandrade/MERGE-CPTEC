import numpy as np
import xarray as xr

from .io import read_field, read_grib, spatial


def accumulate(files):
    if not files:
        raise ValueError("Nenhum GRIB informado")
    total = lat = lon = None
    for path in files:
        values, current_lat, current_lon, _ = read_grib(path, "Precipitation")
        if total is None:
            total, lat, lon = values.copy(), current_lat, current_lon
        else:
            if (
                values.shape != total.shape
                or not np.array_equal(lat, current_lat)
                or not np.array_equal(lon, current_lon)
            ):
                raise ValueError(f"Grades incompatíveis em {path}")
            total += values
    return total, lat, lon


def anomaly(files, climatology):
    from scipy.interpolate import griddata

    total, lat, lon = accumulate(files)
    reference = spatial(read_field(climatology, "precacum"))
    target_lon, target_lat = np.meshgrid(
        (reference.lon.values + 180) % 360 - 180, reference.lat.values
    )
    interpolated = griddata(
        (lon.ravel(), lat.ravel()), total.ravel(), (target_lon, target_lat), method="linear"
    )
    result = xr.DataArray(
        interpolated - reference.values,
        dims=("lat", "lon"),
        coords={"lat": reference.lat, "lon": reference.lon},
        name="anomalia_precipitacao",
        attrs={
            "units": "mm",
            "source_file_count": len(files),
            "interpolation": "linear",
            "missing_data_policy": "propagate",
        },
    )
    result.lat.attrs["units"] = "degrees_north"
    result.lon.attrs["units"] = "degrees_east"
    return result
