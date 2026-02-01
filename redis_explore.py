import json
import redis

def get_geojson(r: redis, type: str):
    ids = r.smembers(f"admin:type:{type}")

    features = []

    for id in ids:
        key = f"admin:{id}"
        data = r.get(key)
        if data:
            features.append(json.loads(data))

    return {
        "type": "FeatureCollection",
        "features": features
    }


def list_facilities_by_powiat(r: redis.Redis, powiat_id: str):
    """Zwraca listę pełnych obiektów stacji (JSON) dla danego powiatu."""
    ids = r.smembers(f"facility:by_powiat:{powiat_id}")
    facilities = []
    for fid in ids:
        data = r.get(f"facility:{fid}")
        if data:
            facilities.append(json.loads(data))
    return facilities


def list_facilities_by_woj(r: redis.Redis, woj_id: str):
    powiat_ids = r.smembers(f"admin:children:{woj_id}")

    pipe = r.pipeline()
    for pid in powiat_ids:
        pipe.smembers(f"facility:by_powiat:{pid}")

    results = pipe.execute()

    all_station_ids = set()
    for station_set in results:
        all_station_ids.update(station_set)

    if not all_station_ids:
        return []

    pipe = r.pipeline()
    for fid in all_station_ids:
        pipe.get(f"facility:{fid}")

    json_results = pipe.execute()

    return [json.loads(data) for data in json_results if data]


def list_all_facilities(r: redis.Redis):
    woj_codes = ["02", "04", "06", "08", "10", "12", "14", "16",
                 "18", "20", "22", "24", "26", "28", "30", "32"]

    print("Pobieranie listy ID stacji...")
    pipe = r.pipeline()

    for woj in woj_codes:
        powiat_ids = r.smembers(f"admin:children:{woj}")
        for pid in powiat_ids:
            pipe.smembers(f"facility:by_powiat:{pid}")

    results = pipe.execute()

    all_station_ids = set()
    for station_set in results:
        all_station_ids.update(station_set)

    if not all_station_ids:
        return []

    print(f"Pobieranie danych JSON dla {len(all_station_ids)} stacji...")

    pipe = r.pipeline()
    for fid in all_station_ids:
        pipe.get(f"facility:{fid}")

    json_results = pipe.execute()

    all_facilities = [json.loads(data) for data in json_results if data]

    return all_facilities


def list_orphan_facilities(r):
    all_ids = r.smembers("facility:all")
    result = []

    for fid in all_ids:
        f = json.loads(r.get(f"facility:{fid}"))
        if not f["properties"].get("powiat_id"):
            result.append(f)

    return result

def list_powiaty_by_woj(r, woj_id):
    ids = r.smembers(f"admin:children:{woj_id}")
    return [
        json.loads(r.get(f"admin:{pid}"))
        for pid in ids
        if r.exists(f"admin:{pid}")
    ]