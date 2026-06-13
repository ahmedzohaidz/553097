---
name: reports
description: تقارير الأداء والمبيعات والمخزون والفنيين - ملخصات يومية/شهرية للإيرادات، ضريبة القيمة المضافة، أوامر العمل، وتقييمات العملاء. Use when generating performance, revenue, VAT, inventory, or technician reports for management.
---

# التقارير والأداء | Reports & Performance

## الهدف | Purpose
تجميع مؤشرات الأداء الرئيسية لمركز الصيانة من قاعدة البيانات لإعداد
تقارير دورية (يومية/أسبوعية/شهرية) للإدارة: الإيرادات وضريبة القيمة
المضافة المحصّلة، حالة أوامر العمل، أداء الفنيين، القطع منخفضة المخزون،
ومتوسط تقييم العملاء.

Aggregate key performance indicators for management reporting: revenue
and collected VAT, work order status breakdown, technician performance,
low-stock parts, and average customer ratings.

## متى تُستخدم | When to use
- لإعداد تقرير يومي/أسبوعي/شهري لمدير المركز.
- عند الحاجة لمعرفة الإيرادات وضريبة القيمة المضافة المستحقة لفترة معينة
  (لأغراض الإقرار الضريبي لهيئة الزكاة والضريبة والجمارك "زاتكا").
- لمراجعة أداء كل فني (عدد أوامر العمل المكتملة، ساعات العمل).
- لمراجعة قطع الغيار التي تحتاج إعادة طلب (بالتكامل مع مهارة
  `inventory`).

## التقارير المتاحة | Available reports
الوظائف في `scripts.py` (كل دالة تأخذ `start_date` و `end_date` بصيغة
`YYYY-MM-DD` عند الحاجة):

- `revenue_summary(conn, start_date, end_date)`
  → `{invoice_count, subtotal, vat_amount, total, paid_total, unpaid_total}`
  مفيد لإعداد إقرار ضريبة القيمة المضافة (VAT return) الدوري.
- `work_order_status_breakdown(conn)`
  → عدد أوامر العمل حسب كل حالة.
- `technician_performance(conn, start_date, end_date)`
  → عدد أوامر العمل المكتملة وساعات العمل المسجلة لكل فني.
- `low_stock_report(conn)`
  → قطع الغيار التي وصلت لحد إعادة الطلب (يستدعي مهارة `inventory`).
- `customer_satisfaction(conn, start_date, end_date)`
  → متوسط التقييم وعدد التقييمات لكل فترة.

## سير العمل | Workflow
1. حدّد الفترة الزمنية المطلوبة (يومية/أسبوعية/شهرية).
2. استدعِ الدوال المطلوبة وجمّع النتائج في تقرير واحد.
3. لإقرار ضريبة القيمة المضافة، استخدم `revenue_summary` مع بداية
   ونهاية الشهر الميلادي (الفترة الضريبية المعتادة لدى زاتكا).
4. شارك التقرير مع الإدارة (نص، أو يمكن تنسيقه كجدول باستخدام مكتبة
   `tabulate` المذكورة في `requirements.txt`).

## ملاحظات | Notes
- جميع المبالغ في قاعدة البيانات مخزَّنة بالريال السعودي (SAR) بدون رمز
  العملة؛ أضف "ريال" أو "SAR" عند العرض للمستخدم.
- `revenue_summary` يفصل بين `paid_total` و `unpaid_total` لمساعدة
  الإدارة على متابعة المتأخرات.
