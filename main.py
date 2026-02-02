from redis_load_shp import *
from gui import *
import sys
from read_meteo import *

'''Konfig'''

# Redis
REDIS_HOST = "localhost"
REDIS_PORT = 6379

#Mongo
MONGO_HOST = "localhost"
MONGO_PORT = 27017

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

db = connect_to_mongo_and_get_data(MONGO_HOST, MONGO_PORT)

if __name__ == "__main__":

    app = QApplication(sys.argv)

    okno = MyApp(db, r)
    okno.show()

    sys.exit(app.exec())

