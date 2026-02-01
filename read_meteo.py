from pymongo import MongoClient
import pandas as pd
from scipy.stats import trim_mean

def connect_to_mongo_and_get_data(host, port):
    client = MongoClient(f"mongodb://{host}:{port}/")
    db = client["meteo"]
    return db

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


def get_data_by_measurment(db, collection_name, measurment_code, station_ids=None):
    collection = db[collection_name]
    parameter_filter = {"ParametrSh": measurment_code}

    if station_ids is not None:
        if not station_ids:
            return None, None
        parameter_filter["kodSh"] = {"$in": station_ids}

    wanted_values = {"Data": 1, "Wartosc": 1, "kodSh": 1, "Pora_czasu": 1, "_id": 0}

    data = collection.find(parameter_filter, wanted_values)
    data_list = list(data)

    result = pd.DataFrame(data_list)
    if result.empty:
        return None, None

    result['Wartosc'] = pd.to_numeric(result['Wartosc'], errors='coerce')
    result = result.dropna(subset=['Wartosc'])

    try:
        parts = collection_name.split('_')
        target_month = int(parts[0])
        target_year = int(parts[1])
        result = result[
            (result['Data'].dt.month == target_month) &
            (result['Data'].dt.year == target_year)
            ]
        if result.empty:
            return None, None
    except Exception as e:
        print(f"Ostrzeżenie daty: {e}")

    result['Dzien_Data'] = result['Data'].dt.date

    station_stats = result.groupby('kodSh')['Wartosc'].mean().to_dict()

    def calculate_stats(grouped_df, suffix):
        stats = grouped_df.groupby('Dzien_Data')['Wartosc'].agg(
            ['mean', 'median', lambda x: trim_mean(x, 0.1)]
        ).reset_index()
        stats.columns = ['Dzien', f'Srednia_{suffix}', f'Mediana_{suffix}', f'Srednia_Obcinana_{suffix}']
        return stats

    if 'Pora_czasu' in result.columns:
        day_df = result[result['Pora_czasu'] == 'Dzień']
        day_stats = calculate_stats(day_df, "Dzien")
        night_df = result[result['Pora_czasu'] == 'Noc']
        night_stats = calculate_stats(night_df, "Noc")
    else:
        empty_cols = ['Dzien', 'Srednia_Dzien', 'Mediana_Dzien', 'Srednia_Obcinana_Dzien']
        day_stats = pd.DataFrame(columns=empty_cols)
        empty_cols_night = ['Dzien', 'Srednia_Noc', 'Mediana_Noc', 'Srednia_Obcinana_Noc']
        night_stats = pd.DataFrame(columns=empty_cols_night)

    if not day_stats.empty and not night_stats.empty:
        final_stats = pd.merge(day_stats, night_stats, on='Dzien', how='outer')
    elif not day_stats.empty:
        final_stats = day_stats
        for col in ['Srednia_Noc', 'Mediana_Noc', 'Srednia_Obcinana_Noc']:
            final_stats[col] = pd.NA
    elif not night_stats.empty:
        final_stats = night_stats
        for col in ['Srednia_Dzien', 'Mediana_Dzien', 'Srednia_Obcinana_Dzien']:
            final_stats[col] = pd.NA
    else:
        return None, None

    final_stats = final_stats.sort_values('Dzien')

    return final_stats, station_stats