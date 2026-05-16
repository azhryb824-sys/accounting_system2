from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from app.enums import UserRole, AccountType, ContactType


# ================= AUTH =================

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: str
    company_id: int
    role: str
    exp: datetime


# ================= USER =================

class UserBase(BaseModel):
    email: EmailStr
    role: UserRole


class UserCreate(UserBase):
    password: str
    company_id: int


class UserOut(UserBase):
    id: int
    company_id: int

    class Config:
        from_attributes = True


# ================= COMPANY =================

class CompanyCreate(BaseModel):
    name_ar: str
    name_en: Optional[str] = None
    vat_number: str
    cr_number: Optional[str] = None


# ================= CONTACT =================

class ContactCreate(BaseModel):
    name: str
    vat_number: Optional[str] = None
    type: ContactType


# ================= PRODUCT =================

class ProductCreate(BaseModel):
    name: str
    sku: Optional[str] = None
    price: Decimal
    stock_quantity: Decimal
    vat_rate: Decimal = Decimal("15.0")


class ProductOut(ProductCreate):
    id: int

    class Config:
        from_attributes = True


# ================= INVOICE =================

class InvoiceLineBase(BaseModel):
    product_id: int
    description: str
    quantity: Decimal
    unit_price: Decimal


class InvoiceCreate(BaseModel):
    invoice_number: str
    invoice_type: str = "0200000"
    total_exclusive_vat: Decimal
    vat_amount: Decimal
    total_inclusive_vat: Decimal
    customer_name: Optional[str] = None
    buyer_vat: Optional[str] = None
    buyer_street: Optional[str] = None
    buyer_city: Optional[str] = None
    buyer_postcode: Optional[str] = None
    items: List[InvoiceLineBase]


class InvoiceOut(BaseModel):
    id: int
    invoice_number: str
    issue_date: datetime
    total_inclusive_vat: Decimal
    total_exclusive_vat: Decimal
    vat_amount: Decimal
    invoice_type: str
    uuid: str
    customer_name: Optional[str] = None
    buyer_vat: Optional[str] = None
    qr_code: Optional[str] = None
    invoice_hash: Optional[str] = None

    class Config:
        from_attributes = True


# ================= PURCHASE =================

class PurchaseInvoiceCreate(BaseModel):
    invoice_number: str
    contact_id: int
    total_exclusive_vat: Decimal
    vat_amount: Decimal
    total_inclusive_vat: Decimal
    items: List[InvoiceLineBase]


# ================= ZATCA ONBOARDING =================

class OnboardingComplianceRequest(BaseModel):
    otp: str

class OnboardingCSRResponse(BaseModel):
    csr: str
    private_key: str

class ProductionCSIDRequest(BaseModel):
    compliance_request_id: str


# ================= ACCOUNT =================

class AccountCreate(BaseModel):
    code: str
    name_ar: str
    name_en: Optional[str] = None
    type: AccountType


# ================= EXPENSE =================

class ExpenseCreate(BaseModel):
    description: str
    amount: Decimal
    expense_account_code: str
    payment_account_code: str
    date: Optional[datetime] = None


# ================= REPORTS =================

class TrialBalanceItem(BaseModel):
    account_code: str
    account_name: str
    total_debit: Decimal
    total_credit: Decimal
    balance: Decimal

class TrialBalanceOut(BaseModel):
    items: List[TrialBalanceItem]
    total_debit: Decimal
    total_credit: Decimal

class AccountReportItem(BaseModel):
    name: str
    code: str
    amount: Decimal

class IncomeStatementOut(BaseModel):
    revenues: List[AccountReportItem]
    expenses: List[AccountReportItem]
    total_revenue: Decimal
    total_expense: Decimal
    net_income: Decimal

class BalanceSheetOut(BaseModel):
    assets: List[AccountReportItem]
    liabilities: List[AccountReportItem]
    equity: List[AccountReportItem]
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal
    net_income: Decimal

class AccountStatementItem(BaseModel):
    date: datetime
    description: str
    debit: Decimal
    credit: Decimal
    balance: Decimal

class AccountStatementOut(BaseModel):
    account_name: str
    account_code: str
    opening_balance: Decimal
    items: List[AccountStatementItem]
    closing_balance: Decimal

class ProductProfitabilityItem(BaseModel):
    product_name: str
    sku: Optional[str]
    sold_quantity: Decimal
    sales_revenue: Decimal
    cost_of_goods_sold: Decimal
    gross_profit: Decimal
    margin_percentage: Decimal

class ProductProfitabilityOut(BaseModel):
    items: List[ProductProfitabilityItem]
    total_revenue: Decimal
    total_profit: Decimal

class VatReportOut(BaseModel):
    taxable_sales: Decimal
    output_vat: Decimal
    taxable_purchases: Decimal
    input_vat: Decimal
    net_vat_payable: Decimal


class CreditNoteCreate(BaseModel):
    parent_invoice_id: int
    reason: str
    total_exclusive_vat: Decimal
    vat_amount: Decimal
    total_inclusive_vat: Decimal
    invoice_number: str