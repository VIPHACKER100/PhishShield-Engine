from fastapi import APIRouter, HTTPException
from src.api.schemas import RegisterRequest, LoginRequest
from src.api.auth import register_user, authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
async def register(body: RegisterRequest):
    try:
        result = register_user(body.username, body.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/login")
async def login(body: LoginRequest):
    result = authenticate_user(body.username, body.password)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return result
