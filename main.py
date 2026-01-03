import redis
from pathlib import Path
from load_shp import *

'''Konfig'''

# Redis
REDIS_HOST = "localhost" # 
REDIS_PORT = 6379

# Folder z danymi
DATA_DIR = Path("Dane") # folder z danymi

SHP_FILES = {
    "woj": DATA_DIR / "woj.shp",
    "powiat": DATA_DIR / "powiaty.shp",
}

# Połączenie z bazami
r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

if __name__ == "__main__":
    load_all(SHP_FILES, r)