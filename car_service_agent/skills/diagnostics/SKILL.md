---
name: diagnostics
description: تشخيص أعطال المركبة وتسجيل نتائج الفحص وأكواد القراءة (OBD) والتوصيات. Use when a technician inspects a vehicle and needs to record diagnostic findings and recommendations on an existing work order.
---

# تشخيص الأعطال | Vehicle Diagnostics

## الهدف | Purpose
تسجيل نتائج الفحص الفني لمركبة العميل المرتبطة بأمر عمل قائم، بما في ذلك
أكواد قراءة جهاز التشخيص (OBD-II)، الأعطال المكتشفة، التوصيات، ومستوى
الخطورة، ثم تحديث حالة أمر العمل إلى `diagnosing` أو `awaiting_approval`.

Record diagnostic findings for an existing work order — OBD-II codes,
findings, recommendations, and severity — then move the work order to
`diagnosing` or `awaiting_approval`.

## متى تُستخدم | When to use
- بعد استقبال السيارة (`vehicle_intake`) وقبل إنشاء أمر عمل تفصيلي.
- عند إضافة فحص جديد أو متابعة لمركبة قيد الصيانة.

## البيانات المطلوبة | Required information
- `work_order_id`: رقم أمر العمل القائم.
- `technician_id`: الفني الذي أجرى الفحص (اختياري لكنه مفضّل).
- `obd_codes`: أكواد القراءة مفصولة بفواصل، مثل `P0301, P0420`.
- `findings`: وصف نتائج الفحص (بالعربية أو الإنجليزية).
- `recommendation`: التوصية بالإصلاح أو القطع المطلوبة.
- `severity`: مستوى الخطورة - أحد القيم: `low`, `medium`, `high`, `critical`.

## سير العمل | Workflow
1. تأكد من وجود أمر العمل (`work_orders`) وأنه ليس في حالة `delivered`
   أو `cancelled`.
2. أضف سجل تشخيص جديد في جدول `diagnostics`.
3. حدّث حالة أمر العمل:
   - إذا كانت التوصية تتطلب موافقة العميل على تكلفة إضافية → غيّر الحالة
     إلى `awaiting_approval` واستخدم مهارة `customer_followup` لإرسال
     طلب موافقة (`message_type = approval_request`).
   - إذا كان الفحص جزءاً من سير العمل العادي → غيّر الحالة إلى
     `diagnosing`.
4. عند الخطورة `critical`، أبرز ذلك بوضوح في الرسالة الموجهة للعميل
   ولمدير المركز.

## الأدوات المتاحة | Available tools
الوظائف في `scripts.py`:

- `add_diagnostic(conn, work_order_id, findings, technician_id=None, obd_codes=None, recommendation=None, severity="medium")`
- `update_work_order_status(conn, work_order_id, status)`
- `get_diagnostics_for_work_order(conn, work_order_id)`

## ملاحظات | Notes
- أكواد OBD-II القياسية تبدأ بـ `P` (محرك/ناقل حركة)، `B` (هيكل)، `C`
  (شاسيه)، `U` (شبكة). اذكر الكود كما هو دون ترجمة.
- عند الشك في الخطورة، اختر المستوى الأعلى لضمان سلامة العميل.
