from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from app.services.auth_service import register_user, login_user, get_user_by_id
from app.utils.security import decode_access_token

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "student"

class LoginRequest(BaseModel):
    email: str
    password: str

async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user_id = payload.get("sub")
    user = await get_user_by_id(user_id)
    if not user:
        # Construct fallback payload if database restarted
        return {
            "id": user_id,
            "name": payload.get("name", "User"),
            "email": payload.get("email", ""),
            "role": payload.get("role", "student")
        }
    return user

@router.post("/register")
async def register(req: RegisterRequest):
    try:
        res = await register_user(req.name, req.email, req.password, req.role)
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login")
async def login(req: LoginRequest):
    try:
        res = await login_user(req.email, req.password)
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return user
