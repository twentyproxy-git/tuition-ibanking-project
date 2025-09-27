from fastapi import FastAPI, APIRouter, HTTPException, Body, Header
from fastapi.responses import JSONResponse
from bson import ObjectId
import requests

# Self-defined modules
from config import tuition_collection
from models import TuitionRequest, TuitionUpdate

app = FastAPI(root_path="/tuition")

router = APIRouter(
    tags=["tuition"]
)

PROFILE_SERVICE_URL = "http://profile-service:8002"

@app.on_event("startup")
def startup_event():
    from config import seed_tuitions
    seed_tuitions()

@router.get("/")
def root():
    data = {"message": "Hello from tuition"}
    return JSONResponse(content=data, status_code=200)

@router.get("/all")
def getAllTuitions() -> list[dict]:
    tuitions = []
    for tuition in tuition_collection.find():
        profile_id = str(tuition.get("profile_id"))
        profile_resp = requests.get(f"{PROFILE_SERVICE_URL}/profile/get-by-profile/{profile_id}")
        if profile_resp.status_code == 200:
            profile = profile_resp.json()
            tuitions.append({
                "_id": str(tuition["_id"]),
                "mssv": profile.get("mssv"),
                "full_name": profile.get("full_name"),
                "amount": tuition["amount"],
                "status": tuition["status"],
                "user_id": str(tuition["user_id"])
            })
        else: 
            raise HTTPException(status_code=500, detail="Failed to fetch profile data")
    return JSONResponse(content=tuitions, status_code=200)

@router.post("/request-tuition")
async def getTuition(input: TuitionRequest = Body(...)) -> dict:
    
    profile_resp = requests.get(f"{PROFILE_SERVICE_URL}/profile/get-by-mssv/{input.mssv}")
    if profile_resp.status_code != 200:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile = profile_resp.json()
    profile_id = profile.get("_id")
    
    tuition = tuition_collection.find_one({"profile_id": ObjectId(profile_id)})
    if tuition is None:
        raise HTTPException(status_code=404, detail="Tuition not found")
    data = {
        "_id": str(tuition["_id"]),
        "amount": tuition["amount"],
        "status": tuition["status"],
        "mssv": profile.get("mssv"),
        "full_name": profile.get("full_name"),
        "user_id": str(tuition["user_id"])
    }
    return JSONResponse(content=data, status_code=200)

@router.post("/update-status")
async def updateTuitionStatus(input: TuitionUpdate) -> dict:
    result = tuition_collection.update_one(
        {"_id": ObjectId(input.tuition_id)},
        {"$set": {"status": input.status}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Tuition not found")
    else:
        return JSONResponse(content={"message": "Tuition status updated successfully"}, status_code=200)

app.include_router(router)
