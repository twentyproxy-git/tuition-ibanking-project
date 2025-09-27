from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
import requests
import time

MONGO_URI = "mongodb://mongodb:27017"
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))

db = client["ibanking_db"]
tuition_collection = db["tuition_collection"]

AUTH_SERVICE_URL = "http://auth-service:8001"
PROFILE_SERVICE_URL = "http://profile-service:8002"

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

def requestAllProfiles(retries=5, delay=2) -> list[dict]:
    for i in range(retries):
        try:
            resp = requests.get(f"{PROFILE_SERVICE_URL}/profile/all")
            if resp.status_code == 200:
                profiles = resp.json()
                return profiles
        except requests.exceptions.RequestException:
            pass
        print(f"Retry {i+1}/{retries} for requestAllProfiles method")
        time.sleep(delay)
    return []

def seed_tuitions():
    users = requestAllUsers()
    profiles = requestAllProfiles()
    if not users:
        print("Failed to fetch user IDs from auth-service.")
        return
    else:
        for user in users: 
            if user.get("username") == "king_halo":
                    if tuition_collection.count_documents({"user_id": ObjectId(user.get("_id")), "profile_id": ObjectId(profiles[0].get("_id"))}) == 0:
                        tuition_collection.insert_one({
                            "amount": 15000000,
                            "status": "unpaid",
                            "user_id": ObjectId(user.get("_id")),
                            "profile_id": ObjectId(profiles[0].get("_id"))
                        })
            elif user.get("username") == "special_week":
                    if tuition_collection.count_documents({"user_id": ObjectId(user.get("_id")), "profile_id": ObjectId(profiles[1].get("_id"))}) == 0:
                        tuition_collection.insert_one({
                            "amount": 20000000,
                            "status": "unpaid",
                            "user_id": ObjectId(user.get("_id")),
                            "profile_id": ObjectId(profiles[1].get("_id"))
                        }) 
            else:
                print(f"No tuition seed data for user: {user['username']}")