from fastapi import FastAPI, APIRouter, Body, Header, HTTPException
from fastapi.responses import JSONResponse
from bcrypt import checkpw

# Self-defined modules
from config import user_collection
from authorization import issue_jwt, verify_jwt
from models import LoginRequest

app = FastAPI(root_path="/auth")

router = APIRouter(
    tags=["auth"]
)

@app.on_event("startup")
def startup_event():
    from config import seed_users
    seed_users()

@router.get("/")
def root():
    data = {"message": "Hello from auth"}
    return JSONResponse(content=data, status_code=200)

@router.get("/users/all")
def getAllUsers() -> list[dict]:
    users = []
    for user in user_collection.find():
        users.append({
            "_id": str(user["_id"]),
            "username": user["username"]
        })
    return JSONResponse(content=users, status_code=200)

@router.get("/users/{username}")
def getUserByUsername(username: str) -> dict:
    user = user_collection.find_one({"username": username})
    if user is not None:
        data = {
            "_id": str(user["_id"]),
            "username": user["username"]
        }
        return JSONResponse(content=data, status_code=200)
    else:
        raise HTTPException(status_code=404, detail="User not found")

@router.post("/login")
async def verifyIdentity(input: LoginRequest = Body(...)) -> dict:
    resp = user_collection.find_one({"username": input.username})

    if not resp:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    elif not checkpw(input.password.encode("utf-8"), resp["password"].encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    user_id = str(resp["_id"])
    access_token = issue_jwt({"user_id": user_id})

    data = {"access_token": access_token, "token_type": "bearer"}
    return JSONResponse(content=data, status_code=200)

app.include_router(router)