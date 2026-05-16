from datetime import datetime, timedelta
import os

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet

from app.database import get_db
from app import models, schemas


SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480


ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY is missing in .env")

try:
    cipher_suite = Fernet(ENCRYPTION_KEY.encode())
except Exception:
    raise ValueError("Invalid ENCRYPTION_KEY. Generate using Fernet.generate_key().")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

router = APIRouter(tags=["auth"])


def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        return schemas.TokenPayload(
            sub=payload.get("sub"),
            company_id=payload.get("company_id"),
            role=payload.get("role"),
            exp=datetime.fromtimestamp(payload.get("exp")),
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/login", response_model=schemas.Token)
def login(db: Session = Depends(get_db), form: OAuth2PasswordRequestForm = Depends()):
    user = db.query(models.User).filter(models.User.email == form.username).first()

    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": user.email,
        "company_id": user.company_id,
        "role": user.role.value
    })

    return {"access_token": token, "token_type": "bearer"}