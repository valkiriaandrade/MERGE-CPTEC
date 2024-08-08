import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import geopandas as gpd
import numpy as np
import matplotlib.colors as mcolors
from shapely.vectorized import contains

with xr.open_dataset('anomalia_precipitacao_mai.nc') as ds:
    precip_anomalia = ds['anomalia_precipitacao'].load()
shapefile = 'BR_UF_2022.shp'
gdf = gpd.read_file(shapefile)
if gdf.crs is None:
    gdf.set_crs(epsg=4326, inplace=True)
gdf = gdf.to_crs(epsg=4326)
estados_centro_oeste = ['SP', 'MS', 'GO', 'MG', 'AM', 'RR', 'RO', 'AC', 'AP', 'DF', 'PA', 'TO', 'MA', 'CE', 'PI', 'RN', 'PB', 'PE', 'AL', 'SE', 'BA', 'ES', 'RJ', 'MT', 'PR', 'SC', 'RS']
gdf_centro_oeste = gdf[gdf['SIGLA_UF'].isin(estados_centro_oeste)]
gdf_centro_oeste['geometry'] = gdf_centro_oeste.geometry.simplify(0.01)
unioned_shape = gdf_centro_oeste.unary_union
lon, lat = np.meshgrid(precip_anomalia.lon.values, precip_anomalia.lat.values)
mask = contains(unioned_shape, lon, lat)
masked_precip_anomalia = np.where(mask, precip_anomalia.values, np.nan)
mean_precip = np.nanmean(masked_precip_anomalia)
std_precip = np.nanstd(masked_precip_anomalia)
levels = [mean_precip - 2 * std_precip, mean_precip - std_precip, mean_precip, mean_precip + std_precip, mean_precip + 2 * std_precip]
bounds = [mean_precip - 2 * std_precip, mean_precip - std_precip, mean_precip, mean_precip + std_precip, mean_precip + 2 * std_precip, mean_precip + 3 * std_precip] 
colors = ['#E73B29', '#CADF00', '#00D03F', '#00B9DD', '#4E54D7']
cmap = mcolors.ListedColormap(colors)
norm = mcolors.BoundaryNorm(bounds, ncolors=len(colors))
fig, ax = plt.subplots(figsize=(12, 10), subplot_kw={'projection': ccrs.PlateCarree()})
ax.set_extent([-75, -34, -34, 6], crs=ccrs.PlateCarree())  
for shape in gdf_centro_oeste.geometry:
    ax.add_geometries([shape], ccrs.PlateCarree(), edgecolor='black', facecolor='none')
cs = ax.contourf(lon, lat, masked_precip_anomalia, levels=bounds, norm=norm, cmap=cmap, extend='both', transform=ccrs.PlateCarree())
cbar = plt.colorbar(cs, ax=ax, shrink=0.7, aspect=20, extend='both')
cbar.set_label('Anomalia de Precipitação (mm)')
cbar.set_ticks([(b1 + b2) / 2 for b1, b2 in zip(bounds[:-1], bounds[1:])])  
cbar.set_ticklabels(['Muito abaixo', 'Abaixo', 'Média', 'Acima', 'Muito acima'])  
plt.title('Anomalia de Precipitação - Maio 2024')
ax.legend(loc='upper right', handles=[line1])
fig.savefig('brasil_anom_mai2.png', dpi=300, bbox_inches='tight')
plt.show()
