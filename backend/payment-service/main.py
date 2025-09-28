from fastapi import FastAPI, APIRouter, HTTPException, Header, Body
from fastapi.responses import JSONResponse
from datetime import datetime
from bson import ObjectId
import requests
import redis

# Self-defined modules
from config import balance_collection, trans_history_collection
from models import TuitionRequest, PaymentRequest
from authorization import verify_jwt

PROFILE_SERVICE_URL = "http://profile-service:8002"
TUITION_SERVICE_URL = "http://tuition-service:8003"
EMAIL_SERVICE_URL = "http://email-service:8005"
OTP_SERVICE_URL = "http://otp-service:8006"

redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

app = FastAPI(root_path="/payment")

router = APIRouter(
    tags=["payment"]
)

@app.on_event("startup")
def startup_event():
    from config import seed_balances, seed_transaction_history
    seed_balances()
    seed_transaction_history()

@router.get("/")
def root():
    return {"message": "Hello from payment"}

@router.get("/balance/all")
def getBalanceByUserID() -> list[dict]:
    balances = []
    for balance in balance_collection.find():
        resp_profile = requests.get(f"{PROFILE_SERVICE_URL}/profile/get-by-user/{str(balance['user_id'])}")
        if resp_profile.status_code == 200:
            profile = resp_profile.json()
            balances.append({
                "_id": str(balance["_id"]),
                "full_name": profile.get("full_name"),
                "mssv": profile.get("mssv"),
                "amount": balance.get("amount"),
                "user_id": str(balance["user_id"]),
            })
    return JSONResponse(content=balances, status_code=200)

@router.get("/balance/get-balance")
async def getBalanceById(authorization: str = Header(...)) -> dict: 
    # Authenticate user
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ")[1]
    payload = verify_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token") 
    user_id = payload["user_id"]

    # Retrieve balance from MongoDB
    balance_doc = balance_collection.find_one({"user_id": ObjectId(user_id)})
    if not balance_doc:
        raise HTTPException(status_code=404, detail="Balance not found")
    balance = balance_doc.get("amount", 0)

    return JSONResponse(content={"balance": balance}, status_code=200)

@router.get('/transaction/get-transaction')
async def getTransactionsById(authorization: str = Header(...)) -> list[dict]: 
    # Authenticate user
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ")[1]
    payload = verify_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user_id = payload["user_id"]

    # Retrieve transaction history from MongoDB
    trans_cursor = trans_history_collection.find({"user_id": ObjectId(user_id)})
    transactions = []

    # Convert cursor to list of dicts and serialize ObjectId and datetime fields
    for doc in trans_cursor:
        doc["_id"] = str(doc["_id"])
        doc["user_id"] = str(doc["user_id"])
        # Convert all datetime fields to string
        for k, v in doc.items():
            if hasattr(v, "isoformat"):
                doc[k] = v.isoformat()
        transactions.append(doc)

    # If no transactions found, return 404
    if not transactions:
        raise HTTPException(status_code=404, detail="Transaction history not found")
    return JSONResponse(content=transactions, status_code=200)

@router.post("/transaction/request-payment")
async def requestPayment(authorization: str = Header(...), input: TuitionRequest = Body(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ")[1]
    payload = verify_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user_id = payload["user_id"]

    balance_doc = balance_collection.find_one({"user_id": ObjectId(user_id)})
    if not balance_doc:
        raise HTTPException(status_code=404, detail="Balance not found")
    balance = int(balance_doc.get("amount", 0))

    tuition_resp = requests.post(f"{TUITION_SERVICE_URL}/tuition/request-tuition", json={"mssv": input.mssv})
    if tuition_resp.status_code != 200:
        raise HTTPException(status_code=404, detail="Tuition not found")
    tuition_doc = tuition_resp.json()
    fee = int(tuition_doc.get("amount", 0))

    # -- Check if tuition is already paid --
    if tuition_doc.get("status") == "paid":
        return JSONResponse(content={
            "status": "paid",
            "message": "Tuition fee already paid for this mssv."
        }, status_code=200)

    if balance >= fee:
        profile_resp = requests.get(f"{PROFILE_SERVICE_URL}/profile/get-by-user/{user_id}")
        if profile_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Email not found")
        profile = profile_resp.json()
        email = profile.get("email")
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")

        # -- Generate OTP --
        otp_service_resp = requests.post(f"{OTP_SERVICE_URL}/otp/issue-otp", json={"user_id": user_id})
        if otp_service_resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to generate OTP")

        otp_data = otp_service_resp.json()
        otp = otp_data.get("otp")
        if not otp:
            raise HTTPException(status_code=500, detail="OTP not found in Redis")

        # -- Save mssv to Redis for verification step --
        mssv_key = f"mssv:{user_id}"
        redis_client.set(mssv_key, input.mssv, ex=300)  # 5 phút

        # -- Send OTP via Email --
        email_payload = {"email": email, "otp": otp}
        email_service_resp = requests.post(f"{EMAIL_SERVICE_URL}/email/send-otp", json=email_payload)
        if email_service_resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to send OTP email")

        # -- Return Pending Response --
        data = {
            "status": "pending",
            "message": "OTP sent, please check your email",
        }
        return JSONResponse(content=data, status_code=200)
    else:
        raise HTTPException(status_code=400, detail="Insufficient balance")

@router.post("/transaction/verify-payment")
async def verifyPayment(authorization: str = Header(...), input: PaymentRequest = Body(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ")[1]
    payload = verify_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user_id = payload["user_id"]

    lock_key = f"lock:payment:{user_id}"
    got_lock = redis_client.set(lock_key, "1", nx=True, ex=10)
    if not got_lock:
        raise HTTPException(status_code=429, detail="Payment already in progress, please try again later")

    try:
        otp_key = f"otp:{user_id}"
        stored_otp = redis_client.get(otp_key)
        if not stored_otp:
            raise HTTPException(status_code=400, detail="OTP expired or not found")
        if stored_otp != input.otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        # -- Check mssv matches the one used in request-payment --
        mssv_key = f"mssv:{user_id}"
        stored_mssv = redis_client.get(mssv_key)
        if not stored_mssv:
            raise HTTPException(status_code=400, detail="MSSV expired or not found. Please request payment again.")
        if stored_mssv != input.mssv:
            raise HTTPException(status_code=400, detail=f"MSSV does not match. Please use the same MSSV as in request-payment. MSSV requested: {stored_mssv}, MSSV provided: {input.mssv}")

        balance_doc = balance_collection.find_one({"user_id": ObjectId(user_id)})
        if not balance_doc:
            raise HTTPException(status_code=404, detail="Balance not found")
        balance = int(balance_doc.get("amount", 0))

        tuition_resp = requests.post(f"{TUITION_SERVICE_URL}/tuition/request-tuition", json={"mssv": input.mssv})
        if tuition_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Tuition not found")
        tuition_doc = tuition_resp.json()

        profile_resp = requests.get(f"{PROFILE_SERVICE_URL}/profile/get-by-user/{user_id}")
        if profile_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Email not found")
        profile = profile_resp.json()

        # Proceed with payment
        fee = int(tuition_doc.get("amount", 0))
        if balance < fee:
            raise HTTPException(status_code=400, detail="Insufficient balance")

        new_balance = balance - fee
        balance_collection.update_one(
            {"user_id": ObjectId(user_id)},
            {"$set": {"amount": new_balance}}
        )

        tuition_resp = requests.post(f"{TUITION_SERVICE_URL}/tuition/update-status", json={"tuition_id": str(tuition_doc.get("_id")), "status": "paid"})
        if tuition_resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to update tuition status")

        trans_history_collection.insert_one({
            "debit": fee,
            "credit": 0,
            "status": "success",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "user_id": ObjectId(user_id)
        })

        # -- Send OTP via Email --
        email_payload = {"email": profile.get("email"), "full_name": profile.get("full_name"), "debit": str(fee), "content": f"Payment for tuition of Student ID {input.mssv}"}
        email_service_resp = requests.post(f"{EMAIL_SERVICE_URL}/email/send-transaction", json=email_payload)
        if email_service_resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to send transaction email")

        redis_client.delete(otp_key)

        data = {
            "status": "success",
            "message": f"Payment for {input.mssv} successful",
            "remaining_balance": new_balance
        }

        return JSONResponse(content=data, status_code=200)
    finally:
        redis_client.delete(lock_key)

app.include_router(router)