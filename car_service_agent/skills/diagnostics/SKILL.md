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
2. إذا وصف العميل العطل بعبارات عامية (مثل "تهتز"، "صوت غريب"، "اللمبة
   اشتعلت"، "ما تدور")، استخدم **أسئلة التشخيص الذكية** في
   `reference/customer_phrases_ar.md` لتحديد مصدر العطل بدقة قبل إضافة
   سجل التشخيص.
3. عند قراءة أكواد OBD-II، راجع `reference/obd_codes_sa.md` لمعرفة
   الوصف الأكثر احتمالاً ونطاق التكلفة/الوقت التقديري (للاستخدام
   الداخلي فقط - راجع "القواعد الذهبية" أدناه قبل ذكر أي رقم للعميل).
4. راجع `reference/vehicle_notes_sa.md` لمعرفة نقاط الضعف المعروفة
   لماركة/موديل المركبة (من جدول `vehicles`) وتضمينها في سؤال التشخيص
   أو التوصية عند الحاجة.
5. أضف سجل تشخيص جديد في جدول `diagnostics`.
6. حدّث حالة أمر العمل:
   - إذا كانت التوصية تتطلب موافقة العميل على تكلفة إضافية → غيّر الحالة
     إلى `awaiting_approval` واستخدم مهارة `customer_followup` لإرسال
     طلب موافقة (`message_type = approval_request`).
   - إذا كان الفحص جزءاً من سير العمل العادي → غيّر الحالة إلى
     `diagnosing`.
7. عند الخطورة `critical`، أبرز ذلك بوضوح في الرسالة الموجهة للعميل
   ولمدير المركز.
8. عند شرح نتيجة التشخيص للعميل، استخدم العبارات المبسّطة في
   `reference/customer_phrases_ar.md` (القسم 5) بدلاً من المصطلحات
   التقنية.

## القواعد الذهبية | Golden Rules
هذه القواعد **ثابتة ولا يجوز للوكيل مخالفتها** تحت أي ظرف:

1. **لا تُعطِ سعراً نهائياً قبل اكتمال التشخيص.** نطاقات التكلفة في
   `reference/obd_codes_sa.md` هي تقديرات داخلية لمساعدة الوكيل على
   التخطيط، ويمكن ذكرها للعميل **كنطاق تقريبي فقط** مع التوضيح أن السعر
   النهائي يُحدَّد بعد الفحص الفعلي وعبر مهارة `pricing_invoicing`.
2. **لا يبدأ تنفيذ أي عمل (`status = in_progress`) بدون موافقة صريحة
   من العميل** على التشخيص والتكلفة التقديرية. إن كانت هناك أعمال
   إضافية غير مذكورة في الزيارة الأصلية، انتقل إلى `awaiting_approval`
   وأرسل `approval_request` عبر `customer_followup` وانتظر الرد قبل
   المتابعة.
3. **كل سجل تشخيص يحتاج "توقيعاً رقمياً"**: يجب تسجيل `technician_id`
   لكل سجل في جدول `diagnostics` (لا تتركه `NULL` إلا في حالات نادرة
   موثَّقة)، باعتباره توقيع الفني المسؤول عن نتيجة الفحص ومرجعاً عند
   أي خلاف لاحق مع العميل.

## الأدوات المتاحة | Available tools
الوظائف في `scripts.py`:

- `add_diagnostic(conn, work_order_id, findings, technician_id=None, obd_codes=None, recommendation=None, severity="medium")`
- `update_work_order_status(conn, work_order_id, status)`
- `get_diagnostics_for_work_order(conn, work_order_id)`

## مراجع تفصيلية | Reference files
- `reference/obd_codes_sa.md` — قاموس أشهر 30 كود OBD-II مع الوصف
  العربي، السبب الأكثر احتمالاً، تكلفة الإصلاح التقديرية بالريال،
  والوقت التقديري.
- `reference/vehicle_notes_sa.md` — جدول أشهر السيارات في السوق
  السعودي (تويوتا، هيونداي، نيسان) ونقاط الضعف المعروفة لكل موديل.
- `reference/customer_phrases_ar.md` — أسئلة تشخيص ذكية للعبارات
  العامية الشائعة، وعبارات شرح مبسّطة وغير تقنية للعملاء.

## ملاحظات | Notes
- أكواد OBD-II القياسية تبدأ بـ `P` (محرك/ناقل حركة)، `B` (هيكل)، `C`
  (شاسيه)، `U` (شبكة). اذكر الكود كما هو دون ترجمة.
- عند الشك في الخطورة، اختر المستوى الأعلى لضمان سلامة العميل.
