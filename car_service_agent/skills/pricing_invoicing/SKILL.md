---
name: pricing_invoicing
description: حساب التسعير وإصدار الفواتير مع ضريبة القيمة المضافة 15% المعتمدة في السعودية، وتتبع حالة السداد. Use when a work order is completed and an invoice needs to be calculated/issued, or when payment status needs updating.
---

# التسعير والفواتير | Pricing & Invoicing

## الهدف | Purpose
حساب الإجمالي الفرعي لأمر عمل (بنود العمل + قطع الغيار)، تطبيق ضريبة
القيمة المضافة السعودية (**15%**)، إصدار فاتورة في جدول `invoices`،
وتتبع حالة السداد (`unpaid` / `paid` / `cancelled`).

Calculate the subtotal for a work order (labor + parts), apply Saudi VAT
(**15%**), issue an invoice record, and track payment status.

## متى تُستخدم | When to use
- عند اكتمال أمر العمل (`status = completed`) واستعداد العميل للسداد.
- عند تسجيل سداد فاتورة قائمة.
- عند الحاجة لعرض تفاصيل فاتورة للعميل (نص جاهز للإرسال عبر واتساب).

## قاعدة حساب الضريبة | VAT calculation rule
```
subtotal   = إجمالي بنود العمل + إجمالي بنود قطع الغيار  (بدون ضريبة)
vat_amount = subtotal × 0.15
total      = subtotal + vat_amount
```
نسبة الضريبة (`vat_rate = 0.15`) قابلة للتهيئة في `config.py` عبر متغير
البيئة `VAT_RATE`، لكنها 15% حالياً وفق نظام ضريبة القيمة المضافة في
المملكة العربية السعودية.

## سير العمل | Workflow
1. تأكد أن `work_orders.status = 'completed'`.
2. استخدم `get_work_order_summary` (من مهارة `work_orders`) لحساب
   `subtotal`.
3. استخدم `issue_invoice` لإنشاء سجل في `invoices` مع `vat_amount` و
   `total` المحسوبين تلقائياً.
4. أرسل ملخص الفاتورة للعميل (بلغته المفضلة) عبر مهارة
   `customer_followup` (`message_type = ready_for_pickup`), متضمناً:
   - رقم أمر العمل وتفاصيل الخدمات/القطع.
   - الإجمالي قبل الضريبة، قيمة الضريبة (15%)، والإجمالي شامل الضريبة.
5. عند استلام الدفع، استخدم `mark_invoice_paid`.
6. لا يُسلَّم أمر العمل (`mark_delivered`) إلا بعد أن تكون الفاتورة
   `paid` أو بعد اتفاق صريح آخر مع الإدارة.

## الأدوات المتاحة | Available tools
الوظائف في `scripts.py`:

- `issue_invoice(conn, work_order_id, vat_rate=0.15)`
- `mark_invoice_paid(conn, invoice_id)`
- `get_invoice(conn, work_order_id)`
- `format_invoice_text(invoice, summary, lang="ar")` — يولّد نصاً جاهزاً
  بالعربية أو الإنجليزية لإرساله للعميل.

## مثال على نص فاتورة (عربي) | Example invoice text (Arabic)
```
فاتورة أمر العمل رقم 102
العميل: محمد العتيبي
المركبة: تويوتا كامري 2020 - لوحة ABC 1234

البنود:
- تغيير زيت وفلتر (1.0 ساعة × 50.00 ريال) = 50.00 ريال
- طقم فحمات فرامل (Brake Pads) × 1 = 180.00 ريال

الإجمالي قبل الضريبة: 230.00 ريال
ضريبة القيمة المضافة (15%): 34.50 ريال
الإجمالي شامل الضريبة: 264.50 ريال
```
