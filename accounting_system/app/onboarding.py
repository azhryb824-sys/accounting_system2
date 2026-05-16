import json
import base64
import os
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, auth, zatca

router = APIRouter(prefix="/onboarding", tags=["ZATCA Onboarding (Phase 2)"])

@router.post("/generate-csr", response_model=schemas.OnboardingCSRResponse)
def generate_csr_endpoint(current_user: schemas.TokenPayload = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    # جلب بيانات الشركة
    company = db.query(models.Company).filter(models.Company.id == current_user.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # توليد الـ CSR
    # الـ Serial Number عادة يكون بتنسيق: 1-DeviceName|2-AppVersion|3-UUID
    serial_number = f"1-AccountingApp|2-1.0|3-{company.id}"
    
    csr, private_key = zatca.ZatcaEncoder.generate_csr(
        company_name=company.name_ar,
        vat_number=company.vat_number,
        serial_number=serial_number
    )

    return {"csr": csr, "private_key": private_key}

@router.post("/issue-compliance-csid")
async def issue_compliance_csid(
    payload: schemas.OnboardingComplianceRequest,
    current_user: schemas.TokenPayload = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # 1. جلب الشركة والتحقق من وجود CSR مولد مسبقاً (يفترض أنك قمت بحفظه)
    company = db.query(models.Company).filter(models.Company.id == current_user.company_id).first()
    
    # ملاحظة: في تطبيق حقيقي، يجب توليد الـ CSR والـ PK وحفظهما في الـ DB قبل هذه الخطوة
    # هنا سنقوم بتوليدهما مباشرة للتبسيط
    serial_number = f"1-AccountingApp|2-1.0|3-{company.id}"
    csr_pem, private_key_pem = zatca.ZatcaEncoder.generate_csr(company.name_ar, company.vat_number, serial_number)

    # 2. إرسال الطلب إلى بوابة ZATCA Sandbox
    zatca_url = "https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal/api/v2/compliance"
    
    headers = {
        "Accept-Language": "en",
        "Accept-Version": "V2",
        "OTP": payload.otp,
        "Content-Type": "application/json"
    }
    
    body = {"csr": base64.b64encode(csr_pem.encode()).decode()}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(zatca_url, json=body, headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.json())
            
            res_data = response.json()
            
            # 3. تخزين بيانات الشهادة والسر في قاعدة البيانات
            raw_onboarding_data = json.dumps({
                "private_key": private_key_pem,
                "binary_security_token": res_data['binarySecurityToken'],
                "secret": res_data['secret'],
                "request_id": res_data['requestID']
            })
            company.onboarding_data = auth.encrypt_data(raw_onboarding_data)
            db.commit()
            
            return {"message": "Compliance CSID issued and stored successfully"}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ZATCA API Connection Error: {str(e)}")

@router.post("/issue-production-csid")
async def issue_production_csid(
    payload: schemas.ProductionCSIDRequest,
    current_user: schemas.TokenPayload = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    company = db.query(models.Company).filter(models.Company.id == current_user.company_id).first()
    if not company.onboarding_data:
        raise HTTPException(status_code=400, detail="Compliance CSID not found. Run compliance first.")
    
    decrypted_old_data = auth.decrypt_data(company.onboarding_data)
    old_data = json.loads(decrypted_old_data)
    zatca_url = "https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal/api/v2/production/csids"
    
    headers = {
        "Accept-Version": "V2",
        "Authorization": f"Bearer {old_data['binary_security_token']}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(zatca_url, json={"compliance_request_id": payload.compliance_request_id}, headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.json())
            
            res_data = response.json()
            
            # تحديث البيانات بشهادة الإنتاج النهائية
            raw_production_data = json.dumps({
                "private_key": old_data['private_key'],
                "binary_security_token": res_data['binarySecurityToken'],
                "secret": res_data['secret'],
                "request_id": res_data['requestID']
            })
            company.onboarding_data = auth.encrypt_data(raw_production_data)
            db.commit()
            
            return {"message": "Production CSID (PCSID) issued successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ZATCA Production API Error: {str(e)}")