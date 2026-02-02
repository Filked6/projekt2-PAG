import json
from pathlib import Path
import geopandas as gpd
from redis_update_facilities import *
from redis_load_shp import *
from redis_explore import *
from add_to_mongo import *

'''
Plik do jednorazowego uruchomienia i wczytania danych do baz danych.
Wymagane jest uprzednie uruchomienie baz odpowiednio na portach:
6379    dla Redisa
27017   dla MongoDB
'''

# Redis
REDIS_HOST = "localhost"
REDIS_PORT = 6379

# Mongo
MONGO_HOST = "localhost"
MONGO_PORT = 27017

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

path_meteo = r"Dane\Meteo"

import_data_to_mongo(path_meteo, MONGO_HOST, MONGO_PORT)            # import danych meteo 

load_all_shp(SHP_FILES, r)                  # wczytywanie danych shp do redisa ZAWSZE przed stacjami

update_facilities_from_geojson(f"{DATA_DIR}/effacility.geojson", r, True) # wczytywanie stacji do redisa

