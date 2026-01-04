from pymongo import MongoClient
import pandas as pd

#Funkcja do łączenia się z mongo
def connect_to_mongo_and_get_data(host, port):
    client = MongoClient(f"mongodb://{host}:{port}/")
    db = client["meteo"]
    return db

#Pobieramy miesiące dla których mamy dane
def get_available_months(db):
    available_months = {}
    #pobieramy dostępne miesiące
    all_collections = db.list_collection_names()
    for collection in all_collections:
        if "_" in collection:
            #Dzielimy to wszystko tak aby można było ładnie dodać do słownika available_months
            parts = collection.split("_")
            month, year = parts[0], parts[1]
            if year not in available_months:
                available_months[year] = []
            if month not in available_months[year]:
                available_months[year].append(month)
    return available_months

def get_data_by_measurment(db, collection_name, measurment_code):
    collection = db[collection_name]

    #pobieramy dane za pomocą tego jaki mają kod aby nie pobierać wszystkiego
    parameter_filter = {"ParametrSh": measurment_code}
    #Nie pobieramy id bo nam nie potrzebne, dodałem kodSh tak o, ale najprawdopodobniej gdy się zaimplementuje wojewodztwa i powiaty to
    #będziemy filtrować także z tego w linijce wyżej
    wanted_values = {"Data": 1, "Wartosc": 1, "kodSh": 1, "_id": 0}

    #Szukamy danych w bazie na podstawie powyższych parametrów
    data = collection.find(parameter_filter, wanted_values)
    data_list = list(data)

    #Robimy tabelę z danych, aby móc z nich łatwiej korzystać i przekształcać
    df = pd.DataFrame(data_list)

    #Zamieniamy stringi na konkretne typy, teraz pandas będzie wiedział co jest datą oraz że wartość jest numerem
    df['Data'] = pd.to_datetime(df['Data'])
    df['Wartosc'] = pd.to_numeric(df['Wartosc'])

    #Robimy nową kolumnę, która wycina godzinę, gdyż nie jest już to potrzebne, mamy robić tylko średnią dzienną więc godziny nas nie interesują
    df['Dzien_Data'] = df['Data'].dt.date

    #Grupujemy dane na podstawie tego z jakiego są dnia i obliczamy z nich średnią
    result = df.groupby('Dzien_Data')['Wartosc'].mean().reset_index()

    #Zmiana nazw kolumn dla czytelności
    result.columns = ['Dzien', 'Srednia']

    #Zaokrąglenie średniej do 2 miejsc po przecinku
    result['Srednia'] = result['Srednia'].round(2)

    #Sortowanie po dacie (od pierwszego dnia)
    result = result.sort_values('Dzien')

    return result