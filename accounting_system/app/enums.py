from enum import Enum

class UserRole(str, Enum):
    OWNER = "owner"
    ACCOUNTANT = "accountant"
    CASHIER = "cashier"

class AccountType(str, Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"

class ContactType(str, Enum):
    CUSTOMER = "customer"
    SUPPLIER = "supplier"