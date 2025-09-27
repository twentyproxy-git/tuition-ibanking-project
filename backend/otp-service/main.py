from fastapi import FastAPI, APIRouter, HTTPException, Header, Body
from fastapi.responses import JSONResponse
import redis
import random
import requests

from models import OTPRequest

app = FastAPI(root_path="/otp")

router = APIRouter(
    tags=["otp"]
)

redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

@router.get("/")
def root():
    data = {"message": "Hello from otp"}
    return JSONResponse(content=data, status_code=200)

@router.post("/issue-otp")
async def generateOTP(input: OTPRequest = Body(...)) -> dict:    
    otp = str(random.randint(100000, 999999))
    redis_client.setex(f"otp:{input.user_id}", 300, otp)
    data = {"otp": otp, "expires_in": 300}
    return JSONResponse(content=data, status_code=200)

app.include_router(router)