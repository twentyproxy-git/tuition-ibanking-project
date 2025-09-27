from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
import requests
import time

MONGO_URI = "mongodb://mongodb:27017"
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))

db = client["ibanking_db"]
profile_collection = db["profile_collection"]

AUTH_SERVICE_URL = "http://auth-service:8001"

def requestAllUsers(retries=5, delay=2) -> list[dict]:
    for i in range(retries):
        try:
            resp = requests.get(f"{AUTH_SERVICE_URL}/auth/users/all")
            if resp.status_code == 200:
                users = resp.json()
                return users
        except requests.exceptions.RequestException:
            pass
        print(f"Retry {i+1}/{retries} for requestAllUsers method")
        time.sleep(delay)
    return []

def seed_profiles():
    users = requestAllUsers()
    if not users:
        print("Failed to fetch user IDs from auth-service.")
        return
    else:
        for user in users: 
            if user.get("username") == "king_halo":
                    if profile_collection.count_documents({"user_id": ObjectId(user.get("_id"))}) == 0:
                        profile_collection.insert_one({
                            "full_name": "King Halo",
                            "mssv": "523H0096",
                            "email": "trangiathanh0205@gmail.com",
                            "phone": "0123456789",
                            "user_id": ObjectId(user.get("_id"))
                        })
            elif user.get("username") == "special_week":
                    if profile_collection.count_documents({"user_id": ObjectId(user.get("_id"))}) == 0:
                        profile_collection.insert_one({
                            "full_name": "Special Week",
                            "mssv": "523H0026",
                            "email": "giathanh2510@gmail.com",
                            "phone": "0987654321",
                            "user_id": ObjectId(user.get("_id"))
                        }) 
            else:
                print(f"No profile seed data for user: {user['username']}")