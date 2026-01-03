import json
import redis
import geopandas as gpd
from pathlib import Path

def load_shapefile(path: Path, unit_type: str, r: redis):
    gdf = gpd.read_file(path).to_crs(epsg=4326)
    pipe = r.pipeline()

    for _, row in gdf.iterrows():
        gmlid = row["gmlid"]
        parent = row.get("id_upper_l")

        feature = {
            "type": "Feature",
            "id": gmlid,
            "properties": {
                "name": row.get("name"),
                "type": unit_type,
                "parent": parent,
            },
            "geometry": row.geometry.__geo_interface__,
        }

        pipe.set(f"admin:{gmlid}", json.dumps(feature))
        pipe.sadd(f"admin:type:{unit_type}", gmlid)

        if parent:
            pipe.sadd(f"admin:children:{parent}", gmlid)

    pipe.execute()


