import json, redis

r = redis.Redis(decode_responses=True)

woj_ids = r.smembers("admin:type:woj")

print("Województwa:")
for wid in woj_ids:
    woj = json.loads(r.get(f"admin:{wid}"))
    print(f"   {woj["properties"]["name"]}")

powiat_ids = r.smembers("admin:type:powiat")
print("Powiaty:")
for pid in powiat_ids:
    powiat = json.loads(r.get(f"admin:{pid}"))
    print(f"   {powiat["properties"]["name"]}")