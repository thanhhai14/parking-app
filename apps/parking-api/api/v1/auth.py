from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
from pydantic import BaseModel, ConfigDict

from core.database import get_db_session
from core.security import verify_password, create_access_token
from api.deps import get_current_user
from models.user import User, Role

router = APIRouter()

class Token(BaseModel):
    access_token: str
    token_type: str

class UserMe(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    username: str
    full_name: str
    role_code: str

@router.post("/login", response_model=Token)
async def login(
    db: AsyncSession = Depends(get_db_session),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    # Search for user by username
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
        
    # Generate access token
    access_token = create_access_token(subject=user.username)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserMe)
async def read_users_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    # Fetch role code
    result = await db.execute(select(Role).where(Role.id == current_user.role_id))
    role = result.scalars().first()
    role_code = role.code if role else "unknown"
    
    return UserMe(
        id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        role_code=role_code
    )
