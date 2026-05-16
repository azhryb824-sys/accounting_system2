from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, auth
from datetime import datetime

router = APIRouter(prefix="/purchases", tags=["Purchases"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_purchase(invoice_in: schemas.PurchaseInvoiceCreate, current_user: schemas.TokenPayload = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    company_id = current_user.company_id
    
    # 1. إنشاء فاتورة المشتريات
    new_purchase = models.PurchaseInvoice(
        company_id=company_id,
        invoice_number=invoice_in.invoice_number,
        contact_id=invoice_in.contact_id,
        total_exclusive_vat=invoice_in.total_exclusive_vat,
        vat_amount=invoice_in.vat_amount,
        total_inclusive_vat=invoice_in.total_inclusive_vat,
        issue_date=datetime.utcnow()
    )
    db.add(new_purchase)
    db.flush()

    # 2. زيادة المخزن ومعالجة البنود
    for item in invoice_in.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id, models.Product.company_id == company_id).first()
        if not product:
            raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
        
        # زيادة الكمية في المخزن
        product.stock_quantity += item.quantity

        # إضافة تفاصيل البند
        line_vat = (item.quantity * item.unit_price) * (product.vat_rate / 100)
        db.add(models.PurchaseInvoiceLine(
            invoice_id=new_purchase.id,
            product_id=product.id,
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            vat_amount=line_vat
        ))

    # 3. القيد المحاسبي آلياً
    # مدين: المشتريات/المخزون (5101) | مدين: ضريبة المدخلات (2101) | دائن: النقدية أو الموردين (1101 أو 2201)
    entry = models.JournalEntry(
        company_id=company_id,
        description=f"Purchase Invoice #{new_purchase.invoice_number}",
        entry_date=new_purchase.issue_date
    )
    db.add(entry)
    db.flush()

    accounts = {acc.code: acc.id for acc in db.query(models.Account).filter(models.Account.company_id == company_id).all()}
    
    # المدين
    db.add(models.JournalLine(entry_id=entry.id, account_id=accounts['5101'], debit=new_purchase.total_exclusive_vat, credit=0))
    db.add(models.JournalLine(entry_id=entry.id, account_id=accounts['2101'], debit=new_purchase.vat_amount, credit=0))
    
    # الدائن (نفترض النقدية للتبسيط، أو يمكن ربطها بحساب المورد 2201)
    db.add(models.JournalLine(entry_id=entry.id, account_id=accounts['1101'], debit=0, credit=new_purchase.total_inclusive_vat))

    db.commit()
    return {"message": "Purchase recorded and stock updated", "purchase_id": new_purchase.id}