import os
import matplotlib.pyplot as plt
import geopandas as gpd
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
import pygrib
from shapely.geometry import Point
from shapely.prepared import prep
from matplotlib.patches import FancyArrowPatch

grib_folder = 'jul'
acumulado_precipitacao = None
arquivos_grib = [arquivo for arquivo in os.listdir(grib_folder) if arquivo.endswith('.grib2')]
br_shapefile = 'BR_UF_2022.shp'
brasil_norte = gpd.read_file(br_shapefile)
brasil_norte = brasil_norte.to_crs(epsg=4326)
 do Brasil
estados_norte = ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO']  
brasil_norte = brasil_norte[brasil_norte['SIGLA_UF'].isin(estados_norte)]
for arquivo_grib in arquivos_grib:
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
boundaries = [0, 10, 20, 30, 40, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500]
colors = ['#14CAFA', '#007CAF', '#011495', '#00FC15', '#00A20B', '#006606', '#FAFB00', '#FFDF66', '#F99901', '#FB0400', '#AE0001', '#810003', '#F203FC', '#814AE7']
cmap = ListedColormap(colors)
norm = BoundaryNorm(boundaries, len(boundaries) - 1)
fig, ax = plt.subplots(figsize=(12, 10))
x_min, y_min, x_max, y_max = brasil_norte.total_bounds
ax.set_xlim(x_min, x_max)
ax.set_ylim(y_min, y_max)
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
mask = mask_inside_shapefile(brasil_norte, lons, lats)
acumulado_precipitacao = np.where(mask, acumulado_precipitacao, np.nan)
brasil_norte.boundary.plot(ax=ax, color='black', linewidth=1, zorder=3)
cs = ax.contourf(lons, lats, acumulado_precipitacao, cmap=cmap, norm=norm, levels=boundaries, extend='max', zorder=2)
cbar_labels = ['0', '10', '20', '30', '40', '50', '100', '150', '200', '250', '300', '350', '400', '450', '500']
cbar = fig.colorbar(cs, boundaries=boundaries, ticks=boundaries, orientation='vertical', extend='max', shrink=0.6, ax=ax, label='Acumulado de Precipitação (mm)')
cbar.ax.set_yticklabels(cbar_labels)
line1, = ax.plot([], [], linestyle='-', color='black', label='Região Norte')
ax.legend(loc='upper left', handles=[line1])
ax.set_title('Acumulado de Precipitação - Julho 2024')
fig.savefig('Acum_PRP_Jul_2024_Norte.png', dpi=300, bbox_inches='tight')
plt.show()
