from fastapi import FastAPI, APIRouter, Body, Header, HTTPException
from fastapi.responses import JSONResponse
from bson import ObjectId

# Self-defined modules
from config import profile_collection
from authorization import verify_jwt, issue_jwt

app = FastAPI(root_path="/profile")

router = APIRouter(
    tags=["profile"]
)

@app.on_event("startup")
def startup_event():
    from config import seed_profiles
    seed_profiles()

@router.get("/")
def root():
    data = {"message": "Hello from profile"}
    return JSONResponse(content=data, status_code=200)

@router.get("/all")
async def getAllProfiles() -> list[dict]:
    profiles = []
    for profile in profile_collection.find():
        profiles.append({
            "_id": str(profile["_id"]),
            "full_name": profile.get("full_name"),
            "mssv": profile.get("mssv"),
            "email": profile.get("email"),
            "phone": profile.get("phone"),
            "user_id": str(profile["user_id"]),
        })
    return JSONResponse(content=profiles, status_code=200)

@router.get("/get-by-user/{user_id}")
async def getProfileByUserID(user_id: str) -> dict:
    profile = profile_collection.find_one({"user_id": ObjectId(user_id)})
    if profile is not None:
        data = {
            "_id": str(profile["_id"]),
            "full_name": profile.get("full_name"),
            "mssv": profile.get("mssv"),
            "email": profile.get("email"),
            "phone": profile.get("phone"),
            "user_id": str(profile["user_id"]),
        }
        return JSONResponse(content=data, status_code=200)
    else: 
        raise HTTPException(status_code=404, detail="Profile not found")

@router.get("/get-by-profile/{profile_id}")
async def getProfileByID(profile_id: str) -> dict:
    profile = profile_collection.find_one({"_id": ObjectId(profile_id)})
    if profile is not None:
        data = {
            "_id": str(profile["_id"]),
            "full_name": profile.get("full_name"),
            "mssv": profile.get("mssv"),
            "email": profile.get("email"),
            "phone": profile.get("phone"),
            "user_id": str(profile["user_id"]),
        }
        return JSONResponse(content=data, status_code=200)
    else:
        raise HTTPException(status_code=404, detail="Profile not found")

@router.get("/get-by-mssv/{mssv}")
async def getProfileByMSSV(mssv: str) -> dict:
    profile = profile_collection.find_one({"mssv": mssv}, collation={"locale": "en", "strength": 2})
    if profile is not None:
        data = {
            "_id": str(profile["_id"]),
            "full_name": profile.get("full_name"),
            "mssv": profile.get("mssv"),
            "email": profile.get("email"),
            "phone": profile.get("phone"),
            "user_id": str(profile["user_id"]),
        }
        return JSONResponse(content=data, status_code=200)
    else:
        raise HTTPException(status_code=404, detail="Profile not found")

@router.get("/get-by-email/{email}")
async def getProfileByEmail(email: str) -> dict:
    profile = profile_collection.find_one({"email": email})
    if profile is not None:
        data = {
            "_id": str(profile["_id"]),
            "full_name": profile.get("full_name"),
            "mssv": profile.get("mssv"),
            "email": profile.get("email"),
            "phone": profile.get("phone"),
            "user_id": str(profile["user_id"]),
        }
        return JSONResponse(content=data, status_code=200)
    else:
        raise HTTPException(status_code=404, detail="Profile not found")

@router.post("/request-profile")
async def getProfile(authorization: str = Header(..., alias="Authorization")) -> dict: 
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ")[1]
    payload = verify_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user_id = payload["user_id"]

    profile = profile_collection.find_one({"user_id": ObjectId(user_id)})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    data = {
        "_id": str(profile["_id"]),
        "full_name": profile.get("full_name"),
        "mssv": profile.get("mssv"),
        "email": profile.get("email"),
        "phone": profile.get("phone"),
        "user_id": str(profile["user_id"]),
    }
    return JSONResponse(content=data, status_code=200)

app.include_router(router)