import os
from pymongo import MongoClient


def connect_to_mongo_and_get_data(host, port):
    client = MongoClient(f"mongodb://{host}:{port}/")
    db = client["meteo"]

    return db

def get_available_months(db):
    available_data = {}

    all_collections = db.list_collection_names()

    for collection in all_collections:
        collection_parts = collection.split("_")

        if len(collection_parts) == 2:
            month = collection_parts[0]
            year = collection_parts[1]

            if year not in available_data:
                available_data[year] = []

            if month not in available_data[year]:
                available_data[year].append(month)

            available_data[year].sort()

    return available_data

db = connect_to_mongo_and_get_data("localhost", 27017)
get_available_months(db)