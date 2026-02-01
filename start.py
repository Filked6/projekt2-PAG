import json
from pathlib import Path
import geopandas as gpd
from redis_update_facilities import *
from redis_load_shp import *
from redis_explore import *

# Redis
REDIS_HOST = "localhost"
REDIS_PORT = 6379

# Folder z danymi
DATA_DIR = Path("Dane") # folder z danymi

SHP_FILES = {
    "woj": DATA_DIR / "woj.shp",
    "powiat": DATA_DIR / "powiaty.shp",
}
def redis_con(REDIS_HOST = "localhost", REDIS_PORT = 6379):
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True
    )

# Połączenie z bazami
r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

#load_all_shp(SHP_FILES, r)                  # wczytywanie danych shp do redisa ZAWSZE przed stacjami

#update_facilities_from_geojson(f"{DATA_DIR}/effacility.geojson", r, True) # wczytywanie stacji do redisa

geojson_woj = get_geojson(r, "woj")         # geojson z wszytkimi wojwództwami
geojson_powiat = get_geojson(r, "powiat")   # geojson z wszytkimi powiatami

a = list_facilities_by_powiat(r, "2411")        # geojson zawierający id == nazwie i wspólrzędne stacji wg. powiatu
b = list_orphan_facilities(r)                   # geojson zawierający id == nazwie i wspólrzędne stacji poza powiatami

#with open("podglad_powiatow.json", "w", encoding="utf-8") as f:
    #json.dump(geojson_powiat, f, indent=4, ensure_ascii=False)

#list_powiaty_by_woj(r, "02")                # geojson zawierający id, nazwie i granicę powiatu wg. województwa

#r.flushdb() # tego raczej nie dajemy do kodu ale jak chcesz wywalić wszystko z redisa to to
