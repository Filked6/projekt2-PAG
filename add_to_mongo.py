import pandas as pd
from pymongo import MongoClient
import os
from astral import LocationInfo
from astral.sun import sun
from astral_file import determine_day_night
from zoneinfo import ZoneInfo

def import_data_to_mongo(path, host, port):
    lat = 52.2297             # współrzędne  
    lon = 21.0122
    tz_name = "Europe/Warsaw" # strefa czasowa
    tz = ZoneInfo(tz_name)
    city = LocationInfo("Station", "Poland", tz_name, lat, lon)

    client = MongoClient(f"mongodb://{host}:{port}/")
    db = client["meteo"]

    print(f"Rozpoczynanie importu danych z folderu: {path}")
    chunk_size = 50000  # chumkowanie dla szybkości

    for folder_name in os.listdir(path): 
        full_path = os.path.join(path, folder_name) 

        if os.path.isdir(full_path) and folder_name.startswith("Meteo_"):   
            try:
                folder_name_parts = folder_name.split("_")  #format nazwy folderu: Meteo_{ROK}_{MIESIAC}
                year = folder_name_parts[1]
                month = folder_name_parts[2]

                collection_name = f"{month}_{year}"
                collection = db[collection_name]

                print(f"Wchodzę do folderu: {folder_name} (Kolekcja: {collection_name})")

                for filename in os.listdir(full_path):
                    if filename.endswith(".csv") and filename.startswith('B') : #pomijamy pliki takie jak kody stacji itp.

                        file_path = os.path.join(full_path, filename)
                        print(f"Przetwarzanie pliku: {filename}")
                        try:
                            rows_counter = 0
                            with pd.read_csv(
                                    file_path,
                                    header=None,
                                    names=['kodSh', 'ParametrSh', 'Data', 'Wartosc'],
                                    sep=';',
                                    chunksize=chunk_size
                            ) as reader:

                                for chunk in reader:
                                    chunk['Wartosc'] = pd.to_numeric(chunk['Wartosc'], errors='coerce')
                                    chunk = chunk.dropna(subset=['Wartosc'])
                                    chunk = chunk[chunk['Wartosc'] <= 1000]

                                    chunk['Data'] = pd.to_datetime(chunk['Data'])

                                    if chunk['Data'].dt.tz is None:
                                        chunk['Data'] = chunk['Data'].dt.tz_localize(tz)
                                    else:
                                        chunk['Data'] = chunk['Data'].dt.tz_convert(tz)

                                    unique_dates = chunk['Data'].dt.date.unique()
                                    sun_schedule = {}

                                    for single_date in unique_dates:
                                        try:
                                            s = sun(city.observer, date=single_date, tzinfo=tz)
                                            sun_schedule[single_date] = {
                                                'sunrise': s['sunrise'],
                                                'sunset': s['sunset']
                                            }
                                        except Exception:
                                            sun_schedule[single_date] = {
                                                'sunrise': None,
                                                'sunset': None
                                            }

                                    chunk['Pora_czasu'] = chunk.apply(determine_day_night, axis=1, args=(sun_schedule,))

                                    data_to_import = chunk.to_dict('records')

                                    if data_to_import:
                                        collection.insert_many(data_to_import)
                                        rows_counter += len(data_to_import)

                        except Exception as e:
                            print(f"Błąd przy pliku {filename}: {e}")

                    elif filename.endswith(".csv"):
                        print(f"Pominięto plik: {filename}")

            except IndexError:
                print(f"Folder o nietypowej nazwie: {folder_name}. Pomijanie.")

