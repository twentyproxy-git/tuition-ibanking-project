from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
from bson import ObjectId
import requests
import time

MONGO_URI = "mongodb://mongodb:27017"
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))

db = client["ibanking_db"]
balance_collection = db["balance_collection"]
trans_history_collection = db["transaction_history_collection"]

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

def seed_balances():
    users = requestAllUsers()
    if not users:
        print("Failed to fetch user IDs from auth-service.")
        return
    else:
        for user in users:
            if user.get("username") == "king_halo":
                    if balance_collection.count_documents({"user_id": ObjectId(user.get("_id"))}) == 0:
                        balance_collection.insert_one({
                            "amount": 50000000,
                            "user_id": ObjectId(user.get("_id"))
                        })
            elif user.get("username") == "special_week":
                    if balance_collection.count_documents({"user_id": ObjectId(user.get("_id"))}) == 0:
                        balance_collection.insert_one({
                            "amount": 20000000,
                            "user_id": ObjectId(user.get("_id"))
                        })

def seed_transaction_history():
    users = requestAllUsers()
    if not users:
        print("Failed to fetch user IDs from auth-service.")
        return
    else:
        for user in users:
            if user.get("username") == "king_halo":
                if trans_history_collection.count_documents({"user_id": ObjectId(user.get("_id"))}) == 0:
                    trans_history_collection.insert_many([{
                        "debit": 2000000,
                        "credit": 0,
                        "status": "success",
                        "created_at": datetime(2025, 9, 27, 10, 0, 0), # YYYY, MM, DD, HH, MM, SS
                        "updated_at": datetime(2025, 9, 27, 10, 0, 0),
                        "user_id": ObjectId(user.get("_id"))
                    }, {
                        "debit": 0,
                        "credit": 5000000,
                        "status": "success",
                        "created_at": datetime(2025, 9, 28, 14, 30, 0),
                        "updated_at": datetime(2025, 9, 28, 14, 30, 0),
                        "user_id": ObjectId(user.get("_id"))
                    }, {
                        "debit": 1000000,
                        "credit": 0,
                        "status": "success",
                        "created_at": datetime(2025, 9, 29, 9, 15, 0),
                        "updated_at": datetime(2025, 9, 29, 9, 15, 0),
                        "user_id": ObjectId(user.get("_id"))
                    }])
            elif user.get("username") == "special_week":
                if trans_history_collection.count_documents({"user_id": ObjectId(user.get("_id"))}) == 0:
                    trans_history_collection.insert_one({
                        "debit": 1000000,
                        "credit": 0,
                        "status": "success",
                        "created_at": datetime(2023, 10, 2, 11, 0, 0),
                        "updated_at": datetime(2025, 10, 2, 11, 0, 0),
                        "user_id": ObjectId(user.get("_id"))   
                    })