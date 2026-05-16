from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, auth
from datetime import datetime

router = APIRouter(prefix="/expenses", tags=["Expenses"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_expense(expense_in: schemas.ExpenseCreate, current_user: schemas.TokenPayload = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    company_id = current_user.company_id
    
    # 1. التأكد من وجود الحسابات المطلوبة للشركة
    account_codes = [expense_in.expense_account_code, expense_in.payment_account_code]
    accounts = {acc.code: acc.id for acc in db.query(models.Account).filter(
        models.Account.company_id == company_id,
        models.Account.code.in_(account_codes)
    ).all()}

    if expense_in.expense_account_code not in accounts or expense_in.payment_account_code not in accounts:
        raise HTTPException(status_code=400, detail="One or both account codes are invalid for this company")

    # 2. إنشاء القيد المحاسبي (Journal Entry)
    entry_date = expense_in.date or datetime.utcnow()
    entry = models.JournalEntry(
        company_id=company_id,
        description=expense_in.description,
        entry_date=entry_date
    )
    db.add(entry)
    db.flush()

    # 3. إضافة سطور القيد (Double Entry)
    # مدين: حساب المصروف (الزيادة في المصاريف مدينة)
    db.add(models.JournalLine(
        entry_id=entry.id, 
        account_id=accounts[expense_in.expense_account_code], 
        debit=expense_in.amount, 
        credit=0
    ))
    # دائن: حساب الدفع (النقص في الأصول دائن)
    db.add(models.JournalLine(
        entry_id=entry.id, 
        account_id=accounts[expense_in.payment_account_code], 
        debit=0, 
        credit=expense_in.amount
    ))

    db.commit()
    return {"message": "Expense recorded successfully", "entry_id": entry.id}