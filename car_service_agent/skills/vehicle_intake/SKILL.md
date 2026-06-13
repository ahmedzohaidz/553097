---
name: vehicle_intake
description: استقبال السيارة والعميل عند الوصول إلى المركز - تسجيل بيانات العميل والمركبة وفتح أمر عمل جديد. Use when a customer/vehicle arrives at the service center and needs to be checked in.
---

# استقبال السيارة والعميل | Vehicle & Customer Intake

## الهدف | Purpose
استقبال العميل ومركبته عند الوصول إلى المركز، وتسجيل (أو تحديث) بيانات
العميل والمركبة في قاعدة البيانات، وفتح أمر عمل جديد (Work Order) بحالة
`received`.

Check in a customer and their vehicle when they arrive at the service
center: create/update the customer and vehicle records, and open a new
work order with status `received`.

## متى تُستخدم | When to use
- عند وصول عميل جديد أو عودة عميل حالي لتقديم سيارته للصيانة.
- عند الحاجة لتحديث بيانات تواصل العميل أو قراءة العداد للمركبة.

## البيانات المطلوبة | Required information
1. **العميل**: الاسم، رقم الهاتف (بصيغة دولية مثل `+9665XXXXXXXX`)، اللغة
   المفضلة (`ar`/`en`)، المدينة (اختياري).
2. **المركبة**: رقم اللوحة، الشركة المصنعة، الموديل، سنة الصنع، رقم
   الهيكل (VIN) (اختياري)، قراءة العداد الحالية بالكيلومتر.
3. **سبب الزيارة / الشكوى المبدئية** (complaint) لفتح أمر العمل.

## سير العمل | Workflow
1. ابحث عن العميل برقم الهاتف في جدول `customers`.
   - إن لم يوجد، أنشئ سجلاً جديداً.
   - إن وُجد، اعرض بياناته للعميل للتأكد ثم حدّثها عند الحاجة.
2. ابحث عن المركبة برقم اللوحة المرتبط بالعميل في جدول `vehicles`.
   - إن لم توجد، أنشئ سجلاً جديداً وارتبطه بـ `customer_id`.
   - إن وُجدت، حدّث قراءة العداد (`odometer_km`).
3. أنشئ سجلاً جديداً في `work_orders` بحالة `received` مع تسجيل الشكوى
   (`complaint`).
4. أعد للعميل ملخصاً (بلغته المفضلة) يتضمن رقم أمر العمل ووقت الاستلام
   المتوقع.
5. (اختياري) أرسل رسالة واتساب ترحيبية/تأكيدية باستخدام مهارة
   `customer_followup` مع `message_type = status_update`.

## الأدوات المتاحة | Available tools
الوظائف موجودة في `scripts.py` بهذه المهارة:

- `find_or_create_customer(conn, name, phone, preferred_lang="ar", city=None)`
- `find_or_create_vehicle(conn, customer_id, plate_number, make, model, year=None, vin=None, odometer_km=0)`
- `open_work_order(conn, vehicle_id, customer_id, complaint, promised_at=None)`

## ملاحظات للسوق السعودي | Saudi market notes
- استخدم رقم الهاتف بصيغة دولية (`+966...`) لضمان توافقه مع واتساب.
- رقم اللوحة قد يحتوي على أرقام وحروف عربية/إنجليزية - خزّنه كما هو
  مكتوب في اللوحة.
- اسأل دائماً عن اللغة المفضلة للتواصل (عربي/إنجليزي) لاستخدامها في
  الفواتير والرسائل اللاحقة.
