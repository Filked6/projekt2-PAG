import os
from pymongo import MongoClient


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
            if len(parts) == 2:
                month, year = parts[0], parts[1]
                if year not in available_months:
                    available_months[year] = []
                if month not in available_months[year]:
                    available_months[year].append(month)
    return available_months

def get_data_by_measurment(db, collection):
    collection.find({""})