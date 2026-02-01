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

def list_facilities_by_powiat(r, powiat_id):
    ids = r.smembers(f"facility:by_powiat:{powiat_id}")
    return [
        json.loads(r.get(f"facility:{fid}"))
        for fid in ids
        if r.exists(f"facility:{fid}")
    ]

def list_facilities_by_woj(r, woj_id):
    if woj_id == "00":
        powiat_id = "0202"
    else:
        powiat_id = f"{woj_id}02"
    ids = r.smembers(f"facility:by_powiat:{powiat_id}")
    return [
        json.loads(r.get(f"facility:{fid}"))
        for fid in ids
        if r.exists(f"facility:{fid}")
    ]


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