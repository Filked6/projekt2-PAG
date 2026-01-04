import pandas as pd
from pymongo import MongoClient
import os

def import_data_to_mongo(path):
    # łączenie się z baza danych (jeżeli macie inny port to zmieńcie to tu)
    client = MongoClient("mongodb://localhost:27017/")
    db = client["meteo"]

    print(f"Rozpoczynanie importu danych z folderu: {path}")
    #Ilość ładowanych danych jednocześnie, aby nie obciążyć procesu
    chunk_size = 50000

    #iteracja po folderach
    for folder_name in os.listdir(path):
        full_path = os.path.join(path, folder_name)

        #sprawdzamy czy to folder Meteo_YYYY_MM
        if os.path.isdir(full_path) and folder_name.startswith("Meteo_"):
            try:
                folder_name_parts = folder_name.split("_")
                year = folder_name_parts[1]
                month = folder_name_parts[2]

                #Tworzymy kolekcję tak, aby było wiadomo co gdzie jest
                collection_name = f"{month}_{year}"
                collection = db[collection_name]

                print(f"Wchodzę do folderu: {folder_name} (Kolekcja: {collection_name})")

                #Iteracja po plikach w folderze
                for filename in os.listdir(full_path):
                    if filename.endswith(".csv") and filename.startswith(('A', 'B', 'S')):

                        file_path = os.path.join(full_path, filename)
                        print(f"Przetwarzanie pliku: {filename}")
                        try:
                            with pd.read_csv(
                                    file_path,
                                    header=None,
                                    names=['kodSh', 'ParametrSh', 'Data', 'Wartosc'],
                                    sep=';',
                                    chunksize=chunk_size
                            ) as reader:
                                #Usuwanie błędnych danych
                                chunk['Wartosc'] = pd.to_numeric(chunk['Wartosc'], errors='coerce')
                                chunk = chunk.dropna(subset=['Wartosc'])
                                chunk = chunk[chunk['Wartosc'] <= 1000]

                                #tylko informacja ile danych dodajemy
                                rows_counter = 0
                                for chunk in reader:
                                    #Konwersja do słownika (aby zapisać wszystko na raz) i zapis
                                    data_to_import = chunk.to_dict('records')

                                    if data_to_import:
                                        collection.insert_many(data_to_import)
                                        rows_counter += len(data_to_import)

                                print(f"Dodano {rows_counter} wierszy.")

                        #Obsługa błędów na wrazie w
                        except Exception as e:
                            print(f"Błąd przy pliku {filename}: {e}")

                    elif filename.endswith(".csv"):
                        print(f"Pominięto plik: {filename}")

            except IndexError:
                print(f"Folder o nietypowej nazwie: {folder_name}. Pomijanie.")

# Ścieżka do folderu z meteo, w którym znajdują się foldery miesięczne meteo z oryginalna nazwą Meteo_rok_miesiac (np. 08)
# w tym folderze następnie znajdują się pliki csv
path = r"C:\Studia\Sezon_3\Programowania_aplikacji_geoinformacyjnych\Projektcik2\Dane\Meteo"

import_data_to_mongo(path)