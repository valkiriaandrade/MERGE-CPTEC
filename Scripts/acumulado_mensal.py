import os
import matplotlib.pyplot as plt
import geopandas as gpd
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
import pygrib
from shapely.geometry import Point
from shapely.prepared import prep
from matplotlib.patches import FancyArrowPatch


grib_folder = '/mai'
acumulado_precipitacao = None
arquivos_grib = [arquivo for arquivo in os.listdir(grib_folder) if arquivo.endswith('.grib2')]
br_shapefile = 'BR_UF_2022.shp'
brasil = gpd.read_file(br_shapefile)
brasil = brasil.to_crs(epsg=4326)
for arquivo_grib in arquivos_grib:
    # Abra o arquivo GRIB2 com pygrib
    grib_file = os.path.join(grib_folder, arquivo_grib)
    grbs = pygrib.open(grib_file)
    grb = grbs.select(name='Precipitation')[0]
    data = grb.values
    lats, lons = grb.latlons()
    lons = np.where(lons > 180, lons - 360, lons)
    grbs.close()
    if acumulado_precipitacao is None:
        acumulado_precipitacao = data
    else:
        acumulado_precipitacao += data
boundaries = [0, 20, 50, 80, 100, 150, 200, 300, 400, 500]
cbar_labels = ['0', '20', '50', '80', '100', '150', '200', '300', '400', '500']
cmap = plt.get_cmap('rainbow_r', len(boundaries) - 1)
fig, ax = plt.subplots(figsize=(12, 10))
x_min, y_min, x_max, y_max = brasil.total_bounds
ax.set_xlim(-75, -34)  # Ajuste para -75 na longitude mínima
ax.set_ylim(-35, 7)
ax.set_xticks([])
ax.set_yticks([])
ax.set_xticklabels([])
ax.set_yticklabels([])
def mask_inside_shapefile(shapefile, lons, lats):
    mask = np.zeros_like(lons, dtype=bool)
    prep_geometries = [prep(geom) for geom in shapefile.geometry]
    for i in range(lons.shape[0]):
        for j in range(lons.shape[1]):
            point = Point(lons[i, j], lats[i, j])
            
            
            if any(geom.contains(point) for geom in prep_geometries):
                mask[i, j] = True
                
    return mask
mask = mask_inside_shapefile(brasil, lons, lats)
acumulado_precipitacao = np.where(mask, acumulado_precipitacao, np.nan)
norm = BoundaryNorm(boundaries, cmap.N, clip=True)
cs = ax.pcolormesh(lons, lats, acumulado_precipitacao, cmap=cmap, norm=norm, shading='auto', zorder=2)
brasil.boundary.plot(ax=ax, color='black', linewidth=1, zorder=3)
cbar = fig.colorbar(cs, boundaries=boundaries, ticks=boundaries, orientation='vertical', extend='max', shrink=0.9, ax=ax, label='Acumulado de Precipitação (mm)')
cbar.ax.set_yticklabels(cbar_labels)
pcm = ax.contourf(lons, lats, acumulado_precipitacao, levels=boundaries, extend='max')
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_title('Acumulado de Precipitação - Maio 2024')
fig.savefig('Acum_PRP_Mai_2024.png', dpi=300, bbox_inches='tight')
plt.show()
