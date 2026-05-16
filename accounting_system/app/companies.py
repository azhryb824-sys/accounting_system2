from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, auth
from app.enums import AccountType, UserRole

router = APIRouter(prefix="/companies", tags=["Companies & Onboarding"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_company(company_in: schemas.CompanyCreate, owner_email: str, owner_password: str, db: Session = Depends(get_db)):
    # 1. التحقق من عدم وجود الشركة أو المستخدم مسبقاً
    if db.query(models.Company).filter(models.Company.vat_number == company_in.vat_number).first():
        raise HTTPException(status_code=400, detail="VAT number already registered")
    if db.query(models.User).filter(models.User.email == owner_email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. إنشاء الشركة
    new_company = models.Company(**company_in.model_dump())
    db.add(new_company)
    db.flush() # للحصول على id الشركة

    # 3. إنشاء المستخدم المالك
    hashed_pwd = auth.get_password_hash(owner_password) # Assuming auth.py is imported correctly
    new_owner = models.User(
        email=owner_email,
        hashed_password=hashed_pwd,
        role=UserRole.OWNER,
        company_id=new_company.id
    )
    db.add(new_owner)

    # 4. تهيئة شجرة الحسابات الأساسية (مثال: نقدية، مبيعات، ضريبة)
    initial_accounts = [
        {"code": "1101", "name_ar": "نقدية في الصندوق", "type": AccountType.ASSET},
        {"code": "1201", "name_ar": "حسابات العملاء (مدينون)", "type": AccountType.ASSET},
        {"code": "4101", "name_ar": "إيرادات المبيعات", "type": AccountType.REVENUE},
        {"code": "2101", "name_ar": "ضريبة القيمة المضافة المستحقة", "type": AccountType.LIABILITY},
        {"code": "2201", "name_ar": "حسابات الموردين (دائنون)", "type": AccountType.LIABILITY},
        {"code": "5101", "name_ar": "مصاريف عامة", "type": AccountType.EXPENSE},
    ]
    for acc in initial_accounts:
        db.add(models.Account(company_id=new_company.id, **acc))

    db.commit()
    return {"message": "Company and owner registered successfully with initial COA"}