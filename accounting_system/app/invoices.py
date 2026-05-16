import uuid
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
import httpx
from app.database import get_db
from app import models, schemas, auth, zatca # Assuming zatca.py is imported correctly
from datetime import datetime

router = APIRouter(prefix="/invoices", tags=["Invoices"])

@router.post("/", response_model=schemas.InvoiceOut)
def create_invoice(invoice_in: schemas.InvoiceCreate, current_user: schemas.TokenPayload = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    company_id = current_user.company_id
    
    # 1. تنفيذ العملية كـ Transaction لضمان سلامة المخزن والحسابات
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # توليد الـ QR Code باستخدام محرك Zatca
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    # جلب بصمة الفاتورة السابقة (ZATCA Chaining)
    last_invoice = db.query(models.Invoice).filter(
        models.Invoice.company_id == company_id
    ).order_by(models.Invoice.id.desc()).first()
    
    previous_hash = last_invoice.invoice_hash if last_invoice else "NWZlY2ViOTZmOTYyNDY4..." # Hash افتراضي لأول فاتورة

    # تحضير بيانات الـ XML لتوليد الـ Hash الفعلي
    xml_data = {
        'number': invoice_in.invoice_number,
        'uuid': str(uuid.uuid4()),
        'date': datetime.now().strftime("%Y-%m-%d"),
        'time': datetime.now().strftime("%H:%M:%S"),
        'supplier_vat': company.vat_number,
        'type': invoice_in.invoice_type,
        'total_excl_vat': invoice_in.total_exclusive_vat,
        'total_incl_vat': invoice_in.total_inclusive_vat
    }
    
    # 1. توليد الـ XML
    invoice_xml = zatca.ZatcaEncoder.generate_ubl_xml(xml_data)
    
    # 2. حساب الـ Hash الفعلي للملف
    actual_invoice_hash = zatca.ZatcaEncoder.calculate_hash(invoice_xml)

    # 3. توليد الـ QR Code المتوافق
    qr_code_base64 = zatca.ZatcaEncoder.generate_qr_base64(
        seller=company.name_ar,
        vat_no=company.vat_number,
        timestamp=timestamp,
        total=str(invoice_in.total_inclusive_vat),
        vat=str(invoice_in.vat_amount)
    )

    # استبعاد items من القاموس الأساسي لإنشاء موديل الفاتورة
    invoice_data = invoice_in.model_dump()
    items_list = invoice_data.pop('items')

    new_invoice = models.Invoice(
        **invoice_data,
        company_id=company_id,
        qr_code=qr_code_base64,
        issue_date=datetime.now(),
        uuid=xml_data['uuid'],
        previous_invoice_hash=previous_hash,
        invoice_hash=actual_invoice_hash,
        buyer_name=invoice_in.customer_name,
        buyer_vat=invoice_in.buyer_vat,
        buyer_street=invoice_in.buyer_street,
        buyer_city=invoice_in.buyer_city,
        buyer_postcode=invoice_in.buyer_postcode
    )
    
    db.add(new_invoice)
    db.flush()

    # 2. معالجة بنود الفاتورة وخصم المخزون
    for item in items_list:
        product = db.query(models.Product).filter(models.Product.id == item['product_id'], models.Product.company_id == company_id).first()
        if not product:
            raise HTTPException(status_code=400, detail=f"Product {item['product_id']} not found")
        
        if product.stock_quantity < item['quantity']:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.name}")

        # خصم المخزن
        product.stock_quantity -= item['quantity']

        # إضافة تفاصيل البند
        line_vat = (item['quantity'] * item['unit_price']) * (product.vat_rate / 100)
        db.add(models.InvoiceLine(
            invoice_id=new_invoice.id,
            product_id=product.id,
            **item,
            vat_amount=line_vat
        ))

    # إنشاء القيود المحاسبية آلياً (Journal Entry)
    # مدين: نقدية بالصندوق (1101) | دائن: إيرادات مبيعات (4101) | دائن: ضريبة القيمة المضافة (2101)
    entry = models.JournalEntry(
        company_id=company_id,
        description=f"Sales Invoice #{new_invoice.invoice_number}",
        entry_date=new_invoice.issue_date
    )
    db.add(entry)
    db.flush()

    # استخراج معرفات الحسابات بناءً على الأكواد
    accounts = {acc.code: acc.id for acc in db.query(models.Account).filter(models.Account.company_id == company_id).all()}
    
    # التأكد من وجود الحسابات الأساسية قبل الترحيل
    required_codes = ['1101', '4101', '2101']
    for code in required_codes:
        if code not in accounts:
            raise HTTPException(status_code=500, detail=f"Required accounting code {code} is missing for this company.")

    # إضافة سطور القيد
    db.add(models.JournalLine(entry_id=entry.id, account_id=accounts['1101'], debit=new_invoice.total_inclusive_vat, credit=0))
    db.add(models.JournalLine(entry_id=entry.id, account_id=accounts['4101'], debit=0, credit=new_invoice.total_exclusive_vat))
    db.add(models.JournalLine(entry_id=entry.id, account_id=accounts['2101'], debit=0, credit=new_invoice.vat_amount))

    db.commit()
    db.refresh(new_invoice)
    return new_invoice

@router.post("/credit-note", response_model=schemas.InvoiceOut)
def create_credit_note(cn_in: schemas.CreditNoteCreate, current_user: schemas.TokenPayload = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    company_id = current_user.company_id
    
    # 1. التحقق من الفاتورة الأصلية
    original_invoice = db.query(models.Invoice).filter(
        models.Invoice.id == cn_in.parent_invoice_id, 
        models.Invoice.company_id == company_id
    ).first()
    
    if not original_invoice:
        raise HTTPException(status_code=404, detail="Original invoice not found")

    # 2. إنشاء سجل الإشعار الدائن
    new_cn = models.Invoice(
        invoice_number=cn_in.invoice_number,
        company_id=company_id,
        parent_id=original_invoice.id,
        invoice_subtype="381", # Credit Note
        invoice_type=original_invoice.invoice_type,
        total_exclusive_vat=cn_in.total_exclusive_vat,
        vat_amount=cn_in.vat_amount,
        total_inclusive_vat=cn_in.total_inclusive_vat,
        issue_date=datetime.now(),
        uuid=str(uuid.uuid4())
    )
    
    db.add(new_cn)
    db.flush()

    # 3. القيد المحاسبي العكسي
    # مدين: إيرادات المبيعات (4101) | مدين: ضريبة القيمة المضافة (2101) | دائن: النقدية أو العملاء (1101)
    entry = models.JournalEntry(
        company_id=company_id,
        description=f"Credit Note for Inv #{original_invoice.invoice_number}: {cn_in.reason}",
        entry_date=new_cn.issue_date
    )
    db.add(entry)
    db.flush()

    accounts = {acc.code: acc.id for acc in db.query(models.Account).filter(models.Account.company_id == company_id).all()}
    
    # المدين (عكس الدائن الأصلي)
    db.add(models.JournalLine(entry_id=entry.id, account_id=accounts['4101'], debit=new_cn.total_exclusive_vat, credit=0))
    db.add(models.JournalLine(entry_id=entry.id, account_id=accounts['2101'], debit=new_cn.vat_amount, credit=0))
    
    # الدائن (نقص في النقدية أو رصيد العميل)
    db.add(models.JournalLine(entry_id=entry.id, account_id=accounts['1101'], debit=0, credit=new_cn.total_inclusive_vat))

    # 4. توليد بصمة الإشعار (مطلب ZATCA)
    # يجب أن يحتوي XML الإشعار على BillingReference للفاتورة الأصلية
    db.commit()
    db.refresh(new_cn)
    return new_cn

@router.get("/", response_model=list[schemas.InvoiceOut])
def get_invoices(current_user: schemas.TokenPayload = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Invoice).filter(models.Invoice.company_id == current_user.company_id).all()

@router.post("/report-to-zatca/{invoice_id}")
async def report_invoice_to_zatca(invoice_id: int, current_user: schemas.TokenPayload = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    company_id = current_user.company_id
    
    # 1. جلب الفاتورة وبيانات الشركة
    invoice = db.query(models.Invoice).filter(
        models.Invoice.id == invoice_id,
        models.Invoice.company_id == company_id
    ).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # 2. التحقق من بيانات الربط مع ZATCA
    if not company.onboarding_data:
        raise HTTPException(status_code=400, detail="Company not onboarded with ZATCA. Please generate CSID first.")
    
    decrypted_raw = auth.decrypt_data(company.onboarding_data)
    onboarding_data = json.loads(decrypted_raw)
    private_key_pem = onboarding_data.get("private_key")
    binary_security_token = onboarding_data.get("binary_security_token") # هذا هو الـ CSID
    
    if not private_key_pem or not binary_security_token:
        raise HTTPException(status_code=400, detail="ZATCA setup incomplete for this company.")

    # جلب رقم الفاتورة الأصلية إذا كان المستند إشعاراً
    original_number = None
    if invoice.parent_id:
        parent_inv = db.query(models.Invoice).filter(models.Invoice.id == invoice.parent_id).first()
        original_number = parent_inv.invoice_number if parent_inv else None

    # 3. توليد XML الفاتورة
    xml_data = {
        'number': invoice.invoice_number,
        'uuid': invoice.uuid,
        'date': invoice.issue_date.strftime("%Y-%m-%d"),
        'time': invoice.issue_date.strftime("%H:%M:%S"),
        'supplier_vat': company.vat_number,
        'subtype': invoice.invoice_subtype,
        'original_number': original_number,
        'total_excl_vat': invoice.total_exclusive_vat,
        'total_incl_vat': invoice.total_inclusive_vat,
        'buyer_name': invoice.buyer_name,
        'buyer_vat': invoice.buyer_vat,
        'buyer_street': invoice.buyer_street,
        'buyer_city': invoice.buyer_city,
        'buyer_postcode': invoice.buyer_postcode
    }
    invoice_xml = zatca.ZatcaEncoder.generate_ubl_xml(xml_data)

    # 4. توقيع XML الفاتورة رقمياً
    signed_xml = zatca.ZatcaEncoder.sign_xml(invoice_xml, private_key_pem, binary_security_token)

    # 5. إرسال الفاتورة الموقعة إلى ZATCA Reporting API
    zatca_reporting_url = "https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal/api/v2/invoices/reporting" # Sandbox URL
    
    headers = {
        "Accept-Language": "en",
        "Accept-Version": "V2",
        "Authorization": f"Bearer {binary_security_token}", # CSID كـ Bearer Token
        "Content-Type": "application/xml"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(zatca_reporting_url, content=signed_xml.encode('utf-8'), headers=headers)
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ZATCA API Reporting Error: {str(e)}")

@router.post("/clearance-to-zatca/{invoice_id}")
async def clearance_invoice_to_zatca(invoice_id: int, current_user: schemas.TokenPayload = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    company_id = current_user.company_id
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id, models.Invoice.company_id == company_id).first()
    company = db.query(models.Company).filter(models.Company.id == company_id).first()

    decrypted_raw = auth.decrypt_data(company.onboarding_data)
    onboarding_data = json.loads(decrypted_raw)

    # جلب رقم الفاتورة الأصلية إذا كان المستند إشعاراً
    original_number = None
    if invoice.parent_id:
        parent_inv = db.query(models.Invoice).filter(models.Invoice.id == invoice.parent_id).first()
        original_number = parent_inv.invoice_number if parent_inv else None
    
    xml_data = {
        'number': invoice.invoice_number,
        'uuid': invoice.uuid,
        'date': invoice.issue_date.strftime("%Y-%m-%d"),
        'time': invoice.issue_date.strftime("%H:%M:%S"),
        'supplier_vat': company.vat_number,
        'type': '0100000', # Standard Invoice (B2B)
        'subtype': invoice.invoice_subtype,
        'original_number': original_number,
        'total_excl_vat': invoice.total_exclusive_vat,
        'total_incl_vat': invoice.total_inclusive_vat
    }
    
    invoice_xml = zatca.ZatcaEncoder.generate_ubl_xml(xml_data)
    signed_xml = zatca.ZatcaEncoder.sign_xml(invoice_xml, onboarding_data['private_key'], onboarding_data['binary_security_token'])

    zatca_clearance_url = "https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal/api/v2/invoices/clearance"
    
    headers = {
        "Accept-Version": "V2",
        "Authorization": f"Bearer {onboarding_data['binary_security_token']}",
        "Content-Type": "application/xml",
        "Clearance-Status": "1" # طلب التخليص
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(zatca_clearance_url, content=signed_xml.encode('utf-8'), headers=headers)
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ZATCA API Clearance Error: {str(e)}")

@router.get("/download-xml/{invoice_id}")
def download_invoice_xml(invoice_id: int, current_user: schemas.TokenPayload = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id, models.Invoice.company_id == current_user.company_id).first()
    
    if not invoice or not invoice.archived_xml:
        raise HTTPException(status_code=404, detail="Archived XML not found for this invoice")

    return Response(
        content=invoice.archived_xml,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename=invoice_{invoice.invoice_number}.xml"}
    )