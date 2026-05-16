from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.database import get_db
from app import models, schemas, auth
from decimal import Decimal
from app.enums import AccountType

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/trial-balance", response_model=schemas.TrialBalanceOut)
def get_trial_balance(current_user: schemas.TokenPayload = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    company_id = current_user.company_id
    
    # استعلام لتجميع مبالغ المدين والدائن لكل حساب في الشركة
    results = db.query(
        models.Account.code,
        models.Account.name_ar,
        func.sum(models.JournalLine.debit).label('total_debit'),
        func.sum(models.JournalLine.credit).label('total_credit')
    ).join(
        models.JournalLine, models.Account.id == models.JournalLine.account_id
    ).filter(
        models.Account.company_id == company_id
    ).group_by(
        models.Account.code, models.Account.name_ar
    ).all()

    items = []
    grand_total_debit = Decimal('0')
    grand_total_credit = Decimal('0')

    for row in results:
        items.append(schemas.TrialBalanceItem(
            account_code=row.code,
            account_name=row.name_ar,
            total_debit=row.total_debit,
            total_credit=row.total_credit,
            balance=row.total_debit - row.total_credit
        ))
        grand_total_debit += row.total_debit
        grand_total_credit += row.total_credit

    return schemas.TrialBalanceOut(
        items=items,
        total_debit=grand_total_debit,
        total_credit=grand_total_credit
    )

@router.get("/income-statement", response_model=schemas.IncomeStatementOut)
def get_income_statement(current_user: schemas.TokenPayload = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    company_id = current_user.company_id
    
    # استعلام لجلب أرصدة حسابات الإيرادات والمصاريف فقط
    results = db.query(
        models.Account.code,
        models.Account.name_ar,
        models.Account.type,
        func.sum(models.JournalLine.debit).label('total_debit'),
        func.sum(models.JournalLine.credit).label('total_credit')
    ).join(
        models.JournalLine, models.Account.id == models.JournalLine.account_id
    ).filter(
        models.Account.company_id == company_id,
        models.Account.type.in_([AccountType.REVENUE, AccountType.EXPENSE])
    ).group_by(
        models.Account.code, models.Account.name_ar, models.Account.type
    ).all()

    revenues = []
    expenses = []
    total_rev = Decimal('0')
    total_exp = Decimal('0')

    for row in results:
        if row.type == models.AccountType.REVENUE:
            # رصيد الإيرادات = الدائن - المدين
            amount = row.total_credit - row.total_debit
            revenues.append(schemas.AccountReportItem(name=row.name_ar, code=row.code, amount=amount))
            total_rev += amount
        else:
            # رصيد المصاريف = المدين - الدائن
            amount = row.total_debit - row.total_credit
            expenses.append(schemas.AccountReportItem(name=row.name_ar, code=row.code, amount=amount))
            total_exp += amount

    return schemas.IncomeStatementOut(
        revenues=revenues,
        expenses=expenses,
        total_revenue=total_rev,
        total_expense=total_exp,
        net_income=total_rev - total_exp
    )

@router.get("/balance-sheet", response_model=schemas.BalanceSheetOut)
def get_balance_sheet(current_user: schemas.TokenPayload = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    company_id = current_user.company_id
    
    # جلب كافة الحسابات مع أرصدتها
    results = db.query(
        models.Account.code,
        models.Account.name_ar,
        models.Account.type,
        func.sum(models.JournalLine.debit).label('total_debit'),
        func.sum(models.JournalLine.credit).label('total_credit')
    ).join(
        models.JournalLine, models.Account.id == models.JournalLine.account_id
    ).filter(
        models.Account.company_id == company_id
    ).group_by(
        models.Account.code, models.Account.name_ar, models.Account.type
    ).all()

    assets = []
    liabilities = []
    equity = []
    total_assets = Decimal('0')
    total_liabilities = Decimal('0')
    total_equity = Decimal('0')
    
    # حساب صافي الدخل أولاً من حسابات الإيرادات والمصاريف
    total_rev = sum((row.total_credit - row.total_debit) for row in results if row.type == models.AccountType.REVENUE)
    total_exp = sum((row.total_debit - row.total_credit) for row in results if row.type == models.AccountType.EXPENSE)
    net_income = total_rev - total_exp

    for row in results:
        if row.type == models.AccountType.ASSET:
            balance = row.total_debit - row.total_credit
            assets.append(schemas.AccountReportItem(name=row.name_ar, code=row.code, amount=balance))
            total_assets += balance
        elif row.type == models.AccountType.LIABILITY:
            balance = row.total_credit - row.total_debit
            liabilities.append(schemas.AccountReportItem(name=row.name_ar, code=row.code, amount=balance))
            total_liabilities += balance
        elif row.type == models.AccountType.EQUITY:
            balance = row.total_credit - row.total_debit
            equity.append(schemas.AccountReportItem(name=row.name_ar, code=row.code, amount=balance))
            total_equity += balance

    return schemas.BalanceSheetOut(
        assets=assets,
        liabilities=liabilities,
        equity=equity,
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        total_equity=total_equity,
        net_income=net_income
    )

@router.get("/account-statement/{account_code}", response_model=schemas.AccountStatementOut)
def get_account_statement(
    account_code: str, 
    start_date: datetime, 
    end_date: datetime, 
    current_user: schemas.TokenPayload = Depends(auth.get_current_user), 
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id
    
    # 1. التأكد من وجود الحساب
    account = db.query(models.Account).filter(
        models.Account.company_id == company_id, 
        models.Account.code == account_code
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # 2. حساب الرصيد الافتتاحي (مجموع ما قبل start_date)
    opening_results = db.query(
        func.sum(models.JournalLine.debit).label('debit'),
        func.sum(models.JournalLine.credit).label('credit')
    ).join(models.JournalEntry).filter(
        models.JournalLine.account_id == account.id,
        models.JournalEntry.entry_date < start_date
    ).first()

    opening_balance = (opening_results.debit or Decimal('0')) - (opening_results.credit or Decimal('0'))
    
    # 3. جلب الحركات خلال الفترة
    lines = db.query(
        models.JournalEntry.entry_date,
        models.JournalEntry.description,
        models.JournalLine.debit,
        models.JournalLine.credit
    ).join(models.JournalLine).filter(
        models.JournalLine.account_id == account.id,
        models.JournalEntry.entry_date.between(start_date, end_date)
    ).order_by(models.JournalEntry.entry_date).all()

    statement_items = []
    current_balance = opening_balance

    for line in lines:
        current_balance += (line.debit - line.credit)
        statement_items.append(schemas.AccountStatementItem(
            date=line.entry_date,
            description=line.description,
            debit=line.debit,
            credit=line.credit,
            balance=current_balance
        ))

    return schemas.AccountStatementOut(
        account_name=account.name_ar,
        account_code=account.code,
        opening_balance=opening_balance,
        items=statement_items,
        closing_balance=current_balance
    )

@router.get("/dashboard-summary")
def get_dashboard_summary(current_user: schemas.TokenPayload = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    company_id = current_user.company_id
    
    # إجمالي المبيعات (من حسابات الإيرادات)
    total_sales = db.query(func.sum(models.JournalLine.credit - models.JournalLine.debit)).join(models.Account).filter(
        models.Account.company_id == company_id,
        models.Account.type == AccountType.REVENUE
    ).scalar() or Decimal('0')

    # إجمالي المصاريف
    total_expenses = db.query(func.sum(models.JournalLine.debit - models.JournalLine.credit)).join(models.Account).filter(
        models.Account.company_id == company_id,
        models.Account.type == AccountType.EXPENSE
    ).scalar() or Decimal('0')

    return {
        "total_sales": total_sales,
        "total_expenses": total_expenses,
        "net_profit": total_sales - total_expenses,
        "currency": "SAR"
    }

@router.get("/monthly-performance")
def get_monthly_performance(current_user: schemas.TokenPayload = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    company_id = current_user.company_id
    
    # استعلام لتجميع البيانات حسب الشهر (لآخر 6 أشهر)
    # ملاحظة: sqlite لا تدعم date_trunc لذا نستخدم strftime للتطوير، وفي postgres نستخدم date_trunc
    results = db.query(
        func.to_char(models.JournalEntry.entry_date, 'YYYY-MM').label('month'),
        func.sum(func.case((models.Account.type == models.AccountType.REVENUE, models.JournalLine.credit - models.JournalLine.debit), else_=0)).label('sales'),
        func.sum(func.case((models.Account.type == models.AccountType.EXPENSE, models.JournalLine.debit - models.JournalLine.credit), else_=0)).label('expenses')
    ).join(models.JournalLine, models.JournalEntry.id == models.JournalLine.entry_id)\
     .join(models.Account, models.JournalLine.account_id == models.Account.id)\
     .filter(models.JournalEntry.company_id == company_id)\
     .group_by('month')\
     .order_by('month')\
     .limit(6).all()

    performance_data = []
    month_names = {
        "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun",
        "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"
    }

    for row in results:
        year, month_num = row.month.split('-')
        performance_data.append({
            "name": f"{month_names[month_num]} {year}",
            "sales": float(row.sales or 0),
            "expenses": float(row.expenses or 0),
            "profit": float((row.sales or 0) - (row.expenses or 0))
        })

    return performance_data

@router.get("/export/trial-balance")
def export_trial_balance_excel(current_user: schemas.TokenPayload = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    # 1. جلب البيانات (بنفس منطق تقرير ميزان المراجعة)
    company_id = current_user.company_id
    results = db.query(
        models.Account.code, models.Account.name_ar,
        func.sum(models.JournalLine.debit).label('total_debit'),
        func.sum(models.JournalLine.credit).label('total_credit')
    ).join(models.JournalLine).filter(models.Account.company_id == company_id).group_by(models.Account.code, models.Account.name_ar).all()

    # 2. إنشاء ملف Excel في الذاكرة
    wb = Workbook()
    ws = wb.active
    ws.title = "Trial Balance"
    ws.sheet_view.rightToLeft = True # دعم الاتجاه العربي

    # العناوين
    headers = ["كود الحساب", "اسم الحساب", "إجمالي المدين", "إجمالي الدائن", "الرصيد"]
    ws.append(headers)

    # البيانات
    for row in results:
        ws.append([
            row.code,
            row.name_ar,
            float(row.total_debit or 0),
            float(row.total_credit or 0),
            float((row.total_debit or 0) - (row.total_credit or 0))
        ])

    # 3. تحويل الملف إلى Buffer لإرساله
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=trial_balance_{datetime.now().date()}.xlsx"}
    )

@router.get("/product-profitability", response_model=schemas.ProductProfitabilityOut)
def get_product_profitability(current_user: schemas.TokenPayload = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    company_id = current_user.company_id
    
    # 1. جلب بيانات المبيعات لكل منتج
    sales_data = db.query(
        models.Product.id,
        models.Product.name,
        models.Product.sku,
        func.sum(models.InvoiceLine.quantity).label('qty_sold'),
        func.sum(models.InvoiceLine.quantity * models.InvoiceLine.unit_price).label('revenue')
    ).join(models.InvoiceLine).filter(models.Product.company_id == company_id).group_by(models.Product.id).all()
    
    # 2. حساب متوسط سعر الشراء لكل منتج كـ COGS
    purchases = db.query(
        models.PurchaseInvoiceLine.product_id,
        func.avg(models.PurchaseInvoiceLine.unit_price).label('avg_cost')
    ).group_by(models.PurchaseInvoiceLine.product_id).all()
    purchase_map = {p.product_id: p.avg_cost for p in purchases}
    
    items = []
    t_rev = Decimal('0')
    t_profit = Decimal('0')
    
    for sale in sales_data:
        avg_cost = purchase_map.get(sale.id, Decimal('0'))
        cogs = (sale.qty_sold or 0) * avg_cost
        profit = (sale.revenue or 0) - cogs
        margin = (profit / sale.revenue * 100) if sale.revenue > 0 else 0
        
        items.append(schemas.ProductProfitabilityItem(
            product_name=sale.name,
            sku=sale.sku,
            sold_quantity=sale.qty_sold or 0,
            sales_revenue=sale.revenue or 0,
            cost_of_goods_sold=cogs,
            gross_profit=profit,
            margin_percentage=Decimal(str(round(margin, 2)))
        ))
        t_rev += sale.revenue or 0
        t_profit += profit
        
    return schemas.ProductProfitabilityOut(items=items, total_revenue=t_rev, total_profit=t_profit)

@router.get("/vat-report", response_model=schemas.VatReportOut)
def get_vat_report(start_date: datetime, end_date: datetime, current_user: schemas.TokenPayload = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    company_id = current_user.company_id
    
    # 1. حساب ضريبة المخرجات (المبيعات)
    sales = db.query(
        func.sum(models.Invoice.total_exclusive_vat).label('total_excl'),
        func.sum(models.Invoice.vat_amount).label('total_vat')
    ).filter(
        models.Invoice.company_id == company_id,
        models.Invoice.issue_date.between(start_date, end_date)
    ).first()

    # 2. حساب ضريبة المدخلات (المشتريات)
    purchases = db.query(
        func.sum(models.PurchaseInvoice.total_exclusive_vat).label('total_excl'),
        func.sum(models.PurchaseInvoice.vat_amount).label('total_vat')
    ).filter(
        models.PurchaseInvoice.company_id == company_id,
        models.PurchaseInvoice.issue_date.between(start_date, end_date)
    ).first()

    out_vat = sales.total_vat or Decimal('0')
    in_vat = purchases.total_vat or Decimal('0')

    return schemas.VatReportOut(
        taxable_sales=sales.total_excl or Decimal('0'),
        output_vat=out_vat,
        taxable_purchases=purchases.total_excl or Decimal('0'),
        input_vat=in_vat,
        net_vat_payable=out_vat - in_vat
    )