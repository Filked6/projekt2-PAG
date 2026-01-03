import json
import redis
import geopandas as gpd
from shapely.geometry import shape


def update_facilities_from_geojson(
    geojson_path: str,
    redis_host: str = "localhost",
    redis_port: int = 6379,
    reset: bool = False,
):
    """
    Aktualizuje dane facility w Redisie na podstawie pliku GeoJSON.
    Relacje przestrzenne (powiat) wyznaczane są na podstawie geometrii
    zapisanej wcześniej w Redisie (bez użycia plików SHP).

    :param geojson_path: ścieżka do effacility.geojson
    :param reset: jeśli True – czyści stare facility
    """

    r = redis.Redis(
        host=redis_host,
        port=redis_port,
        decode_responses=True
    )

    # =====================
    # (1) Pobranie powiatów z Redisa
    # =====================
    powiat_ids = r.smembers("admin:type:powiat")
    if not powiat_ids:
        raise RuntimeError(
            "Brak powiatów w Redisie (admin:type:powiat). "
            "Najpierw załaduj dane administracyjne."
        )

    powiat_records = []

    for pid in powiat_ids:
        raw = r.get(f"admin:{pid}")
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

    # =====================
    # (2) Wczytanie GeoJSON facility
    # =====================
    fac_gdf = gpd.read_file(geojson_path)

    if fac_gdf.crs is None:
        fac_gdf = fac_gdf.set_crs(epsg=4326)
    elif fac_gdf.crs.to_epsg() != 4326:
        fac_gdf = fac_gdf.to_crs(epsg=4326)

    # =====================
    # (3) Spatial join (punkt → powiat)
    # =====================
    joined = gpd.sjoin(
        fac_gdf,
        powiaty_gdf,
        how="left",
        predicate="within"
    )

    # =====================
    # (4) Reset starej bazy facility (opcjonalnie)
    # =====================
    if reset:
        for key in r.scan_iter("facility:*"):
            r.delete(key)

    # =====================
    # (5) Zapis / aktualizacja w Redisie
    # =====================
    pipe = r.pipeline()
    count = 0

    for _, row in joined.iterrows():
        fid = (
            row.get("id")
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

    print(f"✅ Zaktualizowano {count} obiektów facility")