from pymongo import MongoClient
import pandas as pd

# Funkcja do łączenia się z mongo
def connect_to_mongo_and_get_data(host, port):
    client = MongoClient(f"mongodb://{host}:{port}/")
    db = client["meteo"]
    return db

# Pobieramy miesiące dla których mamy dane
def get_available_months(db):
    available_months = {}
    all_collections = db.list_collection_names()
    for collection in all_collections:
        if "_" in collection:
            parts = collection.split("_")
            if len(parts) >= 2:
                month, year = parts[0], parts[1]
                if year not in available_months:
                    available_months[year] = []
                if month not in available_months[year]:
                    available_months[year].append(month)
    return available_months

def get_data_by_measurment(db, collection_name, measurment_code):
    collection = db[collection_name]
    parameter_filter = {"ParametrSh": measurment_code}

    wanted_values = {"Data": 1, "Wartosc": 1, "kodSh": 1, "Pora_czasu": 1, "_id": 0}

    data = collection.find(parameter_filter, wanted_values)
    data_list = list(data)

    df = pd.DataFrame(data_list)

    df['Data'] = pd.to_datetime(df['Data'], utc=True)
    df['Data'] = df['Data'].dt.tz_convert("Europe/Warsaw")
    df['Wartosc'] = pd.to_numeric(df['Wartosc'], errors='coerce')
    df = df.dropna(subset=['Wartosc'])
    df['Dzien_Data'] = df['Data'].dt.date

    overall_avg = df.groupby('Dzien_Data')['Wartosc'].mean().reset_index()
    overall_avg.columns = ['Dzien', 'Srednia']

    if 'Pora_czasu' in df.columns:
        day_df = df[df['Pora_czasu'] == 'Dzień']
        day_avg = day_df.groupby('Dzien_Data')['Wartosc'].mean().reset_index()
        day_avg.columns = ['Dzien', 'Srednia_Dzien']

        night_df = df[df['Pora_czasu'] == 'Noc']
        night_avg = night_df.groupby('Dzien_Data')['Wartosc'].mean().reset_index()
        night_avg.columns = ['Dzien', 'Srednia_Noc']
    else:
        day_avg = pd.DataFrame(columns=['Dzien', 'Srednia_Dzien'])
        night_avg = pd.DataFrame(columns=['Dzien', 'Srednia_Noc'])

    result = pd.merge(overall_avg, day_avg, on='Dzien', how='left')
    result = pd.merge(result, night_avg, on='Dzien', how='left')

    cols_to_round = ['Srednia', 'Srednia_Dzien', 'Srednia_Noc']
    result[cols_to_round] = result[cols_to_round].round(2)

    result = result.sort_values('Dzien')

    return result