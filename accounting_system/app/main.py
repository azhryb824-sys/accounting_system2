import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app import models, auth, companies, invoices, reports, users, expenses, contacts, onboarding

# إنشاء الجداول عند بدء التشغيل (لأغراض التطوير)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ZATCA Accounting Engine",
    description="نظام محاسبي متكامل يدعم تعدد الشركات ومتوافق مع هيئة الزكاة",
    version="1.0.0"
)

# جلب النطاقات المسموح بها من متغيرات البيئة (CORS)
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "operational", "engine": "Gemini-Code-Assist"}

app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(invoices.router)
app.include_router(reports.router)
app.include_router(users.router)
app.include_router(expenses.router)
app.include_router(contacts.router)
app.include_router(onboarding.router)