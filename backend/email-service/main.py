from fastapi import FastAPI, APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
from bson import ObjectId
import requests
import redis
import random

# Self-defined modules
from send_email import send_otp_email
from models import EmailRequest

PROFILE_SERVICE_URL = "http://profile-service:8002"
OTP_SERVICE_URL = "http://otp-service:8006"

redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

app = FastAPI(root_path="/email")

router = APIRouter(
    tags=["email"]
)

@router.get("/")
def root():
    data = {"message": "Hello from email"}
    return JSONResponse(content=data, status_code=200)

@router.post("/send-otp")
def sendOTP(input: EmailRequest = Body(...)) -> dict:
    resp = requests.get(f"{PROFILE_SERVICE_URL}/profile/get-by-email/{input.email}")
    if resp.status_code != 200:
        raise HTTPException(status_code=404, detail="Email not found in profiles")
    user_id = resp.json().get("user_id")


    if send_otp_email(input.email, input.otp, resp.json().get("full_name")):
        data = {"message": f"OTP sent to {input.email}"}
        return JSONResponse(content=data, status_code=200)
    else:
        raise HTTPException(status_code=500, detail="Failed to send OTP email")

app.include_router(router)