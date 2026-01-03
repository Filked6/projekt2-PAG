import redis
from pathlib import Path
from read_administrative import *
from gui import *
import sys

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
    """
    for type, path in SHP_FILES.items():
        if path.exists():
            load_shapefile(path, type, r)
            print(f"Wczytano: {type}")
        else:
            print(f"Brak pliku: {path}")
    """
    app = QApplication(sys.argv)

    okno = MyApp()
    okno.show()

    sys.exit(app.exec())