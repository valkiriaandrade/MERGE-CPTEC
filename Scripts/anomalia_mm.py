import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geopandas as gpd
import numpy as np
import matplotlib.colors as mcolors
from shapely.vectorized import contains

with xr.open_dataset('anomalia_precipitacao_jul.nc') as ds:
    precip_anomalia = ds['anomalia_precipitacao'].load()
shapefile = 'BR_UF_2022.shp'
gdf = gpd.read_file(shapefile)
gdf = gdf.to_crs(epsg=4326)
unioned_shape = gdf.unary_union
lon, lat = np.meshgrid(precip_anomalia.lon.values, precip_anomalia.lat.values)
mask = contains(unioned_shape, lon, lat)
masked_precip_anomalia = np.where(mask, precip_anomalia.values, np.nan)
fig, ax = plt.subplots(figsize=(12, 10), subplot_kw={'projection': ccrs.PlateCarree()})
ax.set_extent([-75, -34, -35, 7], crs=ccrs.PlateCarree())
for shape in gdf.geometry:
    ax.add_geometries([shape], ccrs.PlateCarree(), edgecolor='black', facecolor='none')
levels = np.array([-400, -300, -200, -100, -75, -50, -25, -5, 0, 5, 25, 50, 75, 100, 200, 300, 400])
norm = mcolors.BoundaryNorm(levels, ncolors=256)
pcm = ax.pcolormesh(precip_anomalia.lon, precip_anomalia.lat, masked_precip_anomalia,
                    norm=norm, cmap='BrBG', transform=ccrs.PlateCarree())
cbar = plt.colorbar(pcm, ax=ax, shrink=0.9, aspect=20, extend='both', ticks=levels)
cbar.set_label('Anomalia de Precipitação (mm)')
ax.add_feature(cfeature.COASTLINE)
ax.add_feature(cfeature.BORDERS, linestyle=':')
plt.title('Anomalia de Precipitação - Julho 2024')
plt.savefig('anomalia_precipitacao_julho_2024.png', dpi=300, bbox_inches='tight')
plt.show()
