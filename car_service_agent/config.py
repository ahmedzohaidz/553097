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
