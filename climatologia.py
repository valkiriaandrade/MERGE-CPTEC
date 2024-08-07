import numpy as np
import matplotlib.pyplot as plt
from netCDF4 import Dataset
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.colors import ListedColormap, BoundaryNorm
import shapely.geometry as sgeom
import cartopy.io.shapereader as shpreader

ncfile = 'MERGE_CPTEC_acum_oct.nc'
ds = Dataset(ncfile)
lon = ds.variables['lon'][:]
lat = ds.variables['lat'][:]
precacum = ds.variables['precacum'][:, :, :]
lon, lat = np.meshgrid(lon, lat)
fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': ccrs.PlateCarree()})
ax.set_xlim(-74.5, -34.5)
ax.set_ylim(-34, 5.5)
ax.add_feature(cfeature.COASTLINE, linestyle='-', linewidth=1)
ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=1)
levels = [0, 10, 20, 30, 40, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500]
colors = ['#14CAFA', '#007CAF', '#011495', '#00FC15', '#00A20B', '#006606', '#FAFB00', '#FFDF66', '#F99901', '#FB0400', '#AE0001', '#810003', '#F203FC', '#814AE7']
cmap = ListedColormap(colors)
norm = BoundaryNorm(levels, ncolors=cmap.N, clip=True)
pcm = ax.contourf(lon, lat, precacum[0, :, :], levels=levels, cmap=cmap, norm=norm, extend='max')
cbar = plt.colorbar(pcm, boundaries=levels, ticks=levels, shrink=0.7)
cbar.set_label('Precipitação (mm)')
shpfilename = shpreader.natural_earth(resolution='10m', category='cultural', name='admin_0_countries')
reader = shpreader.Reader(shpfilename)
brazil = [country.geometry for country in reader.records() if country.attributes['NAME_LONG'] == 'Brazil'][0]
mask_outside_brazil = sgeom.box(minx=-180, miny=-90, maxx=180, maxy=90).difference(brazil)
ax.add_geometries([mask_outside_brazil], ccrs.PlateCarree(), facecolor='white', alpha=1, edgecolor='none')
states = cfeature.NaturalEarthFeature(category='cultural', name='admin_1_states_provinces_lines', scale='50m', facecolor='none')
ax.add_feature(states, linestyle='-', linewidth=1, edgecolor='black')
for spine in ax.spines.values():
    spine.set_visible(False)
plt.title('Climatologia de Precipitação - Junho')
plt.savefig('climatologia_PRP_outubro.png', dpi=300, bbox_inches='tight')
plt.show()
