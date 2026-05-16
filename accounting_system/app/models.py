from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from app.database import Base

from app.enums import UserRole, AccountType, ContactType


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name_ar = Column(String(255), nullable=False)
    name_en = Column(String(255))
    vat_number = Column(String(15), unique=True, nullable=False)
    cr_number = Column(String(15), unique=True)
    onboarding_data = Column(Text)

    users = relationship("User", back_populates="company")
    accounts = relationship("Account", back_populates="company")
    invoices = relationship("Invoice", back_populates="company")
    contacts = relationship("Contact", back_populates="company")
    products = relationship("Product", back_populates="company")
    purchase_invoices = relationship("PurchaseInvoice", back_populates="company")
    journal_entries = relationship("JournalEntry", back_populates="company")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    sku = Column(String(50), index=True)
    price = Column(Numeric(15, 2), nullable=False)
    stock_quantity = Column(Numeric(15, 2), default=0)
    vat_rate = Column(Numeric(5, 2), default=15.0)

    company = relationship("Company", back_populates="products")
    purchase_lines = relationship("PurchaseInvoiceLine", back_populates="product")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    vat_number = Column(String(15))
    type = Column(Enum(ContactType), nullable=False)

    company = relationship("Company", back_populates="contacts")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CASHIER)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)

    company = relationship("Company", back_populates="users")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    code = Column(String(20), nullable=False, index=True)
    name_ar = Column(String(255), nullable=False)
    name_en = Column(String(255))
    type = Column(Enum(AccountType), nullable=False)

    company = relationship("Company", back_populates="accounts")


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    description = Column(String(500))
    entry_date = Column(DateTime, default=datetime.utcnow, index=True)
    
    company = relationship("Company", back_populates="journal_entries")
    lines = relationship("JournalLine", back_populates="entry")


class JournalLine(Base):
    __tablename__ = "journal_lines"
    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    debit = Column(Numeric(15, 2), default=0)
    credit = Column(Numeric(15, 2), default=0)
    
    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    invoice_number = Column(String(50), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"))

    invoice_type = Column(String(20), default="0200000")
    invoice_subtype = Column(String(20), default="388")
    parent_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    uuid = Column(String(100), unique=True)
    issue_date = Column(DateTime, default=datetime.utcnow)

    buyer_name = Column(String(255))
    buyer_vat = Column(String(15))
    buyer_street = Column(String(255))
    buyer_city = Column(String(100))
    buyer_postcode = Column(String(10))

    total_exclusive_vat = Column(Numeric(15, 2), nullable=False)
    vat_amount = Column(Numeric(15, 2), nullable=False)
    total_inclusive_vat = Column(Numeric(15, 2), nullable=False)

    qr_code = Column(Text)
    invoice_hash = Column(String(255))
    previous_invoice_hash = Column(String(255))
    archived_xml = Column(Text)

    company = relationship("Company", back_populates="invoices")
    lines = relationship("InvoiceLine", back_populates="invoice")


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    description = Column(String(255))
    quantity = Column(Numeric(15, 2), nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=False)
    vat_amount = Column(Numeric(15, 2), nullable=False)
    
    invoice = relationship("Invoice", back_populates="lines")
    product = relationship("Product")


class PurchaseInvoice(Base):
    __tablename__ = "purchase_invoices"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    invoice_number = Column(String(50), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    issue_date = Column(DateTime, default=datetime.utcnow)

    total_exclusive_vat = Column(Numeric(15, 2), nullable=False)
    vat_amount = Column(Numeric(15, 2), nullable=False)
    total_inclusive_vat = Column(Numeric(15, 2), nullable=False)

    company = relationship("Company", back_populates="purchase_invoices")
    lines = relationship("PurchaseInvoiceLine", back_populates="invoice")


class PurchaseInvoiceLine(Base):
    __tablename__ = "purchase_invoice_lines"
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("purchase_invoices.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    description = Column(String(255))
    quantity = Column(Numeric(15, 2), nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=False)
    vat_amount = Column(Numeric(15, 2), nullable=False)

    invoice = relationship("PurchaseInvoice", back_populates="lines")
    product = relationship("Product", back_populates="purchase_lines")