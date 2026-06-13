"""
الإعدادات العامة | Global configuration
==========================================
يقرأ هذا الملف متغيرات البيئة المطلوبة لتشغيل الوكيل، مثل بيانات اعتماد
واتساب وإعدادات الضريبة. استخدم ملف `.env` (غير مرفوع لـ git) لتعريف
القيم الفعلية محلياً.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# ضريبة القيمة المضافة في السعودية | Saudi VAT rate
VAT_RATE = float(os.getenv("VAT_RATE", "0.15"))

# اللغة الافتراضية للوكيل | Default agent language ('ar' or 'en')
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "ar")

# --- إعدادات واتساب (Meta Cloud API) ---
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v19.0")
WHATSAPP_API_BASE_URL = "https://graph.facebook.com"

# اسم مركز الصيانة | Service center name (used in invoices/messages)
SERVICE_CENTER_NAME_AR = os.getenv("SERVICE_CENTER_NAME_AR", "مركز الخبراء لصيانة السيارات")
SERVICE_CENTER_NAME_EN = os.getenv("SERVICE_CENTER_NAME_EN", "Experts Car Service Center")

# --- بيانات السجل التجاري والضريبة (تُستخدم في طباعة الفواتير) ---
# Commercial registration & VAT details (used when printing invoices)
SERVICE_CENTER_ADDRESS_AR = os.getenv("SERVICE_CENTER_ADDRESS_AR", "الرياض، المملكة العربية السعودية")
SERVICE_CENTER_ADDRESS_EN = os.getenv("SERVICE_CENTER_ADDRESS_EN", "Riyadh, Saudi Arabia")
SERVICE_CENTER_CR_NUMBER = os.getenv("SERVICE_CENTER_CR_NUMBER", "1010000000")  # رقم السجل التجاري
SERVICE_CENTER_VAT_NUMBER = os.getenv("SERVICE_CENTER_VAT_NUMBER", "300000000000003")  # الرقم الضريبي
SERVICE_CENTER_LOGO_PATH = os.getenv("SERVICE_CENTER_LOGO_PATH", "")  # مسار شعار المركز (اختياري)

# خط عربي (TTF) يدعم رسم الحروف العربية في ملفات PDF
# Arabic-capable TTF font for PDF generation (e.g. Noto Naskh Arabic)
ARABIC_FONT_PATH = os.getenv("ARABIC_FONT_PATH", "")
