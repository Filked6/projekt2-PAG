import json
import redis
import geopandas as gpd
from shapely.geometry import shape


def update_facilities_from_geojson(
    geojson_path: str,
    redis_connection: redis,
    reset: bool = False,
):

    powiat_ids = redis_connection.smembers("admin:type:powiat")
    if not powiat_ids:
        raise RuntimeError(
            "Brak powiatów w Redisie (admin:type:powiat). "
            "Najpierw załaduj dane administracyjne."
        )

    powiat_records = []

    for pid in powiat_ids:
        raw = redis_connection.get(f"admin:{pid}")
        if not raw:
            continue

        feat = json.loads(raw)

        powiat_records.append({
            "powiat_id": pid,
            "geometry": shape(feat["geometry"])
        })

    powiaty_gdf = gpd.GeoDataFrame(
        powiat_records,
        geometry="geometry",
        crs="EPSG:4326"
    )

    fac_gdf = gpd.read_file(geojson_path)

    if fac_gdf.crs is None:
        fac_gdf = fac_gdf.set_crs(epsg=4326)
    elif fac_gdf.crs.to_epsg() != 4326:
        fac_gdf = fac_gdf.to_crs(epsg=4326)

    joined = gpd.sjoin(
        fac_gdf,
        powiaty_gdf,
        how="left",
        predicate="within"
    )

    if reset:
        for key in redis_connection.scan_iter("facility:*"):
            redis_connection.delete(key)

    pipe = redis_connection.pipeline()
    count = 0

    for _, row in joined.iterrows():
        fid = (
            row.get("ifcid")
            or row.get("id")
            or row.get("gmlid")
            or f"facility_{count}"
        )

        feature = {
            "type": "Feature",
            "id": fid,
            "properties": {
                "name": row.get("name"),
                "powiat_id": row.get("powiat_id"),
            },
            "geometry": row.geometry.__geo_interface__,
        }

        pipe.set(f"facility:{fid}", json.dumps(feature))
        pipe.sadd("facility:all", fid)

        if row.get("powiat_id"):
            pipe.sadd(
                f"facility:by_powiat:{row['powiat_id']}",
                fid
            )

        count += 1

    pipe.execute()

    print(f"Zaktualizowano {count} obiektów facility")