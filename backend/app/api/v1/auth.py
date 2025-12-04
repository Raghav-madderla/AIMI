from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.core.database import get_sync_db
from app.models import User
from app.utils.auth import create_access_token, verify_token, generate_user_id

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
security = HTTPBearer()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_sync_db)
) -> User:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_sync_db)):
    """Register a new user"""
    # Check if user already exists
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user = User(
        user_id=generate_user_id(),
        email=request.email,
        name=request.name
    )
    user.set_password(request.password)
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create access token
    token = create_access_token(data={"sub": user.user_id})
    
    return AuthResponse(
        token=token,
        user=UserResponse(user_id=user.user_id, email=user.email, name=user.name)
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: Session = Depends(get_sync_db)):
    """Login user and return JWT token"""
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user or not user.check_password(request.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create access token
    token = create_access_token(data={"sub": user.user_id})
    
    return AuthResponse(
        token=token,
        user=UserResponse(user_id=user.user_id, email=user.email, name=user.name)
    )

