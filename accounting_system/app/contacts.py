from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, auth
from app.enums import ContactType

router = APIRouter(prefix="/contacts", tags=["Contacts (Customers/Suppliers)"])

@router.post("/")
def create_contact(contact_in: schemas.ContactCreate, current_user: schemas.TokenPayload = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    new_contact = models.Contact(
        **contact_in.model_dump(),
        company_id=current_user.company_id
    )
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return new_contact

@router.get("/")
def get_contacts(type: ContactType = None, current_user: schemas.TokenPayload = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    query = db.query(models.Contact).filter(models.Contact.company_id == current_user.company_id)
    if type:
        query = query.filter(models.Contact.type == type)
    return query.all()