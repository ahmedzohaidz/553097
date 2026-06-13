---
name: work_orders
description: إدارة أوامر العمل من الاستلام حتى التسليم - تتبع الحالة، تعيين الفنيين، إضافة بنود العمل وقطع الغيار. Use when managing the lifecycle of a work order (status transitions, technician assignment, adding labor/parts line items).
---

# إدارة أوامر العمل | Work Order Management

## الهدف | Purpose
إدارة دورة حياة أمر العمل بالكامل: من `received` إلى `delivered`، بما في
ذلك تعيين الفني المسؤول، وإضافة بنود العمل (labor) وبنود قطع الغيار
(parts) المستخدمة، وتتبع المواعيد الموعودة للعميل.

Manage the full lifecycle of a work order from `received` to `delivered`:
assign a responsible technician, add labor and parts line items, and
track the promised delivery date.

## دورة حالة أمر العمل | Status lifecycle
```
received → diagnosing → awaiting_approval → in_progress → completed → delivered
                                                                 ↘ cancelled (في أي مرحلة)
```

## متى تُستخدم | When to use
- لتعيين/تغيير الفني المسؤول عن أمر العمل.
- لإضافة بنود عمل (ساعات عمل + سعر الساعة) أو بنود قطع غيار مستخدمة.
- لتغيير حالة أمر العمل عند تقدم العمل أو اكتماله أو إلغائه.
- لاستعراض كل أوامر العمل المفتوحة أو الخاصة بفني معين.

## سير العمل | Workflow
1. **تعيين فني**: استخدم `assign_technician` بعد التحقق من توفر الفني
   (راجع مهارة `technicians`).
2. **إضافة بنود العمل**: لكل خدمة (مثل "تغيير زيت"، "فحص فرامل") أضف
   سطراً في `work_order_labor` يحدد الوصف، عدد الساعات، وسعر الساعة
   للعميل.
3. **إضافة قطع الغيار**: عند استخدام قطعة من المخزون، استخدم مهارة
   `inventory` لخصمها من المخزون ثم أضف سطراً في `work_order_parts`
   بسعر البيع الحالي.
4. **تحديث الحالة**:
   - `in_progress` عند بدء التنفيذ الفعلي.
   - `completed` عند انتهاء جميع الأعمال (يُفعّل إصدار الفاتورة عبر
     مهارة `pricing_invoicing`).
   - `delivered` عند تسليم السيارة للعميل (يُسجَّل `delivered_at`).
   - `cancelled` إذا ألغى العميل الطلب (في أي مرحلة قبل التسليم).
5. عند كل تغيير حالة مهم، أرسل تحديثاً للعميل عبر مهارة
   `customer_followup`.

## الأدوات المتاحة | Available tools
الوظائف في `scripts.py`:

- `assign_technician(conn, work_order_id, technician_id)`
- `add_labor_item(conn, work_order_id, description, hours, rate, technician_id=None)`
- `add_part_item(conn, work_order_id, part_id, quantity, unit_price)`
- `set_status(conn, work_order_id, status)`
- `mark_delivered(conn, work_order_id)`
- `get_open_work_orders(conn)`
- `get_work_order_summary(conn, work_order_id)`

## ملاحظات | Notes
- لا يمكن الانتقال إلى `delivered` قبل إصدار الفاتورة وسدادها أو
  الاتفاق على طريقة الدفع (راجع `pricing_invoicing`).
- استخدم `get_work_order_summary` لعرض ملخص شامل (بيانات العميل،
  المركبة، التشخيص، البنود، الإجمالي) قبل إصدار الفاتورة.
