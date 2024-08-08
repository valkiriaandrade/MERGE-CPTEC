import os
import numpy as np
import pygrib
import netCDF4 as nc
from scipy.interpolate import griddata

grib_folder = 'jul'
climatology_file = 'MERGE_CPTEC_acum_jul.nc'
ds = nc.Dataset(climatology_file)
climatology_prec = ds.variables['precacum'][:]
lats_climatology = ds.variables['lat'][:]
lons_climatology = ds.variables['lon'][:]
ds.close()
lons_reg, lats_reg = np.meshgrid(lons_climatology, lats_climatology)
acumulado_precipitacao = np.zeros_like(climatology_prec)
file_info = []
arquivos_grib = [arquivo for arquivo in os.listdir(grib_folder) if arquivo.endswith('.grib2')]
for arquivo_grib in arquivos_grib:
    grib_file = os.path.join(grib_folder, arquivo_grib)
    grbs = pygrib.open(grib_file)
    grb = grbs.select(name='Precipitation')[0]
    data = grb.values
    lats, lons = grb.latlons()
    lons = np.where(lons > 180, lons - 360, lons)
    grbs.close()
    data_interpolated = griddata((lons.flatten(), lats.flatten()), data.flatten(), (lons_reg, lats_reg), method='linear')
    acumulado_precipitacao += data_interpolated
anomalia_precipitacao = acumulado_precipitacao - climatology_prec
with nc.Dataset('anomalia_precipitacao_jul.nc', 'w', format='NETCDF4') as ds:
    lat_dim = ds.createDimension('lat', len(lats_climatology))
    lon_dim = ds.createDimension('lon', len(lons_climatology))
    latitudes = ds.createVariable('lat', np.float32, ('lat',))
    longitudes = ds.createVariable('lon', np.float32, ('lon',))
    latitudes[:] = lats_climatology
    longitudes[:] = lons_climatology
    anomalia = ds.createVariable('anomalia_precipitacao', np.float32, ('lat','lon',))
    anomalia[:,:] = anomalia_precipitacao
    ds.description = 'Anomalia de Precipitação - Julho 2024'
    latitudes.units = 'graus_norte'
    longitudes.units = 'graus_leste'
    anomalia.units = 'mm'
print("Dados de anomalia de precipitação salvos como 'anomalia_precipitacao_jul.nc'")
