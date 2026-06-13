# وكيل مركز تشخيص وصيانة السيارات | Car Service Center AI Agent

وكيل ذكاء اصطناعي مبني على نظام **Agent Skills** لإدارة مراكز صيانة وتشخيص
السيارات في السوق السعودي، يدعم اللغتين العربية والإنجليزية، يحسب ضريبة
القيمة المضافة (15%)، ويتكامل مع واتساب لمتابعة العملاء.

An AI agent built on the **Agent Skills** architecture for managing car
diagnostic & maintenance centers in the Saudi market. Supports Arabic and
English, calculates 15% VAT, and integrates with WhatsApp for customer
follow-up.

## هيكل المشروع | Project Structure

```
car_service_agent/
├── README.md
├── requirements.txt
├── main.py                  # الوكيل الرئيسي - Main agent entry point
├── config.py                 # الإعدادات العامة - Global configuration
├── database/
│   ├── schema.sql             # هيكل قاعدة البيانات
│   └── db.py                  # طبقة الوصول لقاعدة البيانات
├── skills/
│   ├── vehicle_intake/        # 1. استقبال السيارة والعميل
│   │   └── SKILL.md
│   ├── diagnostics/            # 2. تشخيص الأعطال
│   │   └── SKILL.md
│   ├── work_orders/             # 3. إدارة أوامر العمل
│   │   └── SKILL.md
│   ├── pricing_invoicing/        # 4. التسعير والفواتير
│   │   └── SKILL.md
│   ├── inventory/                 # 5. قطع الغيار والمخزون
│   │   └── SKILL.md
│   ├── technicians/                # 6. إدارة الفنيين
│   │   └── SKILL.md
│   ├── customer_followup/           # 7. متابعة العميل (واتساب)
│   │   └── SKILL.md
│   └── reports/                      # 8. التقارير والأداء
│       └── SKILL.md
└── data/
    └── service_center.db       # قاعدة بيانات SQLite (تُنشأ تلقائياً)
```

## التشغيل | Running

```bash
pip install -r requirements.txt
python main.py
```

سيقوم `main.py` بإنشاء قاعدة البيانات تلقائياً من `database/schema.sql`
عند أول تشغيل، ثم يعرض قائمة تفاعلية بالمهارات الثماني المتاحة.

## ملاحظات حول التكامل مع واتساب | WhatsApp Integration Notes

يستخدم المشروع متغيرات بيئة لإعدادات WhatsApp Business API (مثل
`WHATSAPP_API_TOKEN` و `WHATSAPP_PHONE_NUMBER_ID`). راجع `config.py`
و `skills/customer_followup/SKILL.md` للتفاصيل. الوظائف الفعلية لإرسال
الرسائل (`send_whatsapp_message`) هي دوال "stub" تحتاج لربطها بمزوّد
فعلي (مثل Meta Cloud API أو Twilio) قبل الاستخدام في بيئة الإنتاج.
