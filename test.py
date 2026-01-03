import json
import geopandas as gpd
from update_facilities import *

gdf = gpd.read_file("Dane/effacility.geojson")
print(gdf.head())
print(gdf.geometry.type.unique())

print(gdf.crs)
gdf = gdf.to_crs(epsg=4326)

update_facilities_from_geojson(
    "Dane/effacility.geojson",
    reset=True
)