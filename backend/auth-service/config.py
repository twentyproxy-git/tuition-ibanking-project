# auth-service/config.py
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bcrypt import hashpw, gensalt

MONGO_URI = "mongodb://mongodb:27017"
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))

db = client["ibanking_db"]
user_collection = db["user_collection"]

def seed_users():
    if user_collection.count_documents({}) == 0:
        hashed_pw = hashpw("kh11010".encode("utf-8"), gensalt())
        hashed_pw_2 = hashpw("carrot26".encode("utf-8"), gensalt())
        data = user_collection.insert_many([
            {"username": "king_halo", "password": hashed_pw.decode("utf-8")},
            {"username": "special_week", "password": hashed_pw_2.decode("utf-8")}
        ])
