from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas, auth
from app.enums import UserRole

router = APIRouter(prefix="/users", tags=["Users Management"])

@router.post("/", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def create_staff(user_in: schemas.UserCreate, current_user: schemas.TokenPayload = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    # التحقق من أن المستخدم الحالي هو المالك (Owner)
    if current_user.role != UserRole.OWNER.value:
        raise HTTPException(status_code=403, detail="Only owners can manage staff")
    
    # التأكد من إضافة المستخدم لنفس شركة المالك
    if user_in.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Cannot add users to other companies")

    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = models.User(email=user_in.email, hashed_password=auth.get_password_hash(user_in.password), role=user_in.role, company_id=user_in.company_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/", response_model=List[schemas.UserOut])
def get_staff_list(current_user: schemas.TokenPayload = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    # التحقق من أن المستخدم الحالي هو المالك
    if current_user.role != models.UserRole.OWNER.value:
        raise HTTPException(status_code=403, detail="Only owners can view staff list")
    
    return db.query(models.User).filter(models.User.company_id == current_user.company_id).all()