from fastapi import APIRouter, HTTPException, status, Depends
from backend.schemas import UserRegister, UserLogin, TokenResponse, UserProfile
from backend.database import db
from backend.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
async def register(req: UserRegister):
    # Check if user already exists
    existing = db.get_user_by_email(req.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    # Validate role (only 'student' or 'warden')
    role = req.role.lower()
    if role not in ["student", "warden"]:
        role = "student"

    hashed_pwd = hash_password(req.password)
    new_user = db.create_user(
        email=req.email,
        hashed_password=hashed_pwd,
        full_name=req.full_name,
        room_number=req.room_number,
        role=role
    )

    token_data = {
        "id": new_user["id"],
        "email": new_user["email"],
        "role": new_user["role"],
        "name": new_user["full_name"],
        "room": new_user.get("room_number", "")
    }
    access_token = create_access_token(token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": token_data
    }

@router.post("/login", response_model=TokenResponse)
async def login(req: UserLogin):
    user = db.get_user_by_email(req.email)
    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    token_data = {
        "id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "name": user["full_name"],
        "room": user.get("room_number", "")
    }
    access_token = create_access_token(token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": token_data
    }

@router.get("/me", response_model=UserProfile)
async def get_me(current_user: dict = Depends(get_current_user)):
    user = db.get_user_by_id(current_user["id"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "room_number": user.get("room_number", ""),
        "role": user["role"]
    }
