---
name: technicians
description: إدارة بيانات الفنيين وتخصصاتهم وتوفرهم، ومراجعة عدد أوامر العمل المفتوحة لكل فني لتوازن الحمل. Use when adding/updating technician records, checking availability, or reviewing technician workload.
---

# إدارة الفنيين | Technician Management

## الهدف | Purpose
إدارة سجلات الفنيين العاملين في المركز (الاسم، التخصص، رقم الهاتف،
معدل التكلفة بالساعة، الحالة نشط/غير نشط)، ومساعدة المشرف على توزيع
أوامر العمل بالتوازن بين الفنيين بحسب التخصص وعدد المهام المفتوحة لكل
منهم.

Manage technician records (name, specialty, phone, internal hourly
cost, active status) and help balance work order assignment across
technicians by specialty and current open workload.

## متى تُستخدم | When to use
- عند إضافة فني جديد أو تحديث بياناته (تخصص، حالة النشاط).
- عند الحاجة لاختيار فني مناسب لتعيينه على أمر عمل (مهارة
  `work_orders` → `assign_technician`).
- عند مراجعة عبء العمل الحالي لكل فني.

## التخصصات الشائعة | Common specialties
`mechanical` (ميكانيكا)، `electrical` (كهرباء)، `ac` (تكييف)،
`bodywork` (سمكرة وصبغ)، `tires` (إطارات وزيوت)، `diagnostics`
(تشخيص متقدم).

## سير العمل | Workflow
1. **إضافة/تحديث فني**: استخدم `add_technician` أو `update_technician`.
2. **اختيار فني لأمر عمل جديد**:
   - استخدم `get_technician_workload` لمعرفة عدد أوامر العمل المفتوحة
     (`received`, `diagnosing`, `awaiting_approval`, `in_progress`)
     لكل فني نشط.
   - فضِّل الفني الذي يطابق التخصص المطلوب وله أقل عدد أوامر مفتوحة.
3. **تعطيل فني**: عند انتهاء عقد فني أو إجازته الطويلة، استخدم
   `set_technician_active(conn, technician_id, is_active=False)` بدلاً
   من حذف السجل (لأن السجلات التاريخية مرتبطة به).

## الأدوات المتاحة | Available tools
الوظائف في `scripts.py`:

- `add_technician(conn, name, specialty=None, phone=None, hourly_rate=0)`
- `update_technician(conn, technician_id, **fields)`
- `set_technician_active(conn, technician_id, is_active)`
- `list_technicians(conn, active_only=True)`
- `get_technician_workload(conn)` — يُعيد عدد أوامر العمل المفتوحة لكل
  فني نشط.

## ملاحظات | Notes
- `hourly_rate` هو معدل التكلفة **الداخلي** (لتحليل الربحية)، وهو
  منفصل عن `rate` (سعر الساعة للعميل) المسجَّل في
  `work_order_labor`.
