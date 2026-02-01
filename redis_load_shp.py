import json
import redis
import geopandas as gpd
from pathlib import Path

def load_shapefile(path: Path, unit_type: str, r: redis):
    gdf = gpd.read_file(path).to_crs(epsg=4326)
    pipe = r.pipeline()

    for _, row in gdf.iterrows():
        id = row["national_c"]
        parent = row.get("national_c")[:2]
        if parent == id:
            parent = None
        feature = {
            "type": "Feature",
            "id": id,
            "properties": {
                "name": row.get("name"),
                "type": unit_type,
                "parent": parent,
            },
            "geometry": row.geometry.__geo_interface__,
        }

        pipe.set(f"admin:{id}", json.dumps(feature))
        pipe.sadd(f"admin:type:{unit_type}", id)

        if parent:
            pipe.sadd(f"admin:children:{parent}", id)

    pipe.execute()

def load_all_shp(FILES, r):
    for type, path in FILES.items():
        if path.exists():
            load_shapefile(path, type, r)
            print(f"Wczytano: {type}")
        else:
            print(f"Brak pliku: {path}")
