---
name: inventory
description: إدارة قطع الغيار والمخزون - إضافة قطع، تحديث الكميات، التنبيه عند الوصول لحد إعادة الطلب. Use when checking part availability, recording stock usage/receipts, or reviewing low-stock items.
---

# قطع الغيار والمخزون | Parts & Inventory Management

## الهدف | Purpose
إدارة كتالوج قطع الغيار (`parts`) في المركز: التحقق من توفر القطعة قبل
استخدامها في أمر عمل، تحديث الكمية عند الاستهلاك أو الاستلام من المورد،
وتنبيه الإدارة عند الوصول إلى حد إعادة الطلب (`reorder_level`).

Manage the parts catalog: check availability before using a part on a
work order, adjust stock on consumption/receipt, and flag low-stock
items that need reordering.

## متى تُستخدم | When to use
- قبل إضافة قطعة لأمر عمل (للتحقق من توفر الكمية).
- بعد استخدام قطعة في أمر عمل (لخصمها من المخزون).
- عند استلام شحنة جديدة من المورد (لإضافتها للمخزون).
- عند مراجعة دورية لقطع الغيار التي قاربت على النفاد.

## سير العمل | Workflow
1. **التحقق من التوفر**: استخدم `get_part_by_sku` أو `search_parts` لإيجاد
   القطعة والتحقق من `quantity_on_hand`.
2. **الاستخدام في أمر عمل**: استخدم `use_part_in_work_order` (من
   `scripts/parts_tracker.py`) - تقوم هذه الدالة بخصم الكمية من
   المخزون **وإضافة بند الفاتورة بسعر البيع تلقائياً** (بما يشمل هامش
   الربح عن `unit_cost`)، وتُعيد ملخصاً بالهامش لكل وحدة.
3. **استلام شحنة**: استخدم `receive_stock` لزيادة `quantity_on_hand`
   وتحديث `unit_cost` إن تغيّر. راجع `reference/suppliers_sa.md` لمعرفة
   المورّد المناسب (أصلي OEM أو بديل موثوق) ووقت التوصيل.
4. **اختيار قطعة أصلية أو بديلة**: راجع قسم "متى تنصح العميل بالأصلي /
   البديل" في `reference/suppliers_sa.md` قبل اقتراح بديل للعميل.
5. **التنبيه الصباحي**: شغّل `run_daily_inventory_check` (من
   `scripts/inventory_alert.py`) لإنتاج تقرير واتساب يومي للمدير،
   يتضمن القطع النافدة 🔴 والقاربة على النفاد 🟡 وتكلفة الطلب المقترح،
   ويحفظ طلب إعادة التوريد في `reorder_requests`.
6. **مراجعة دورية**: استخدم `get_low_stock_parts` أو
   `reference/critical_parts.md` لمراجعة تصنيف القطع (يومي/أسبوعي/شهري)
   وضبط `reorder_level` لكل قطعة بما يناسب حجم المركز.
7. **تحليل الاستخدام**: استخدم `get_part_usage_history` و
   `get_most_used_parts` (من `scripts/parts_tracker.py`) لمعرفة أكثر
   القطع استهلاكاً والمركبات المرتبطة بها.

## الأدوات المتاحة | Available tools
الوظائف في `scripts/__init__.py` (متاحة عبر `scripts`):

- `add_part(conn, sku, name_ar, name_en, unit_cost, unit_price, quantity_on_hand=0, reorder_level=5, supplier=None)`
- `get_part_by_sku(conn, sku)`
- `search_parts(conn, query)`
- `consume_stock(conn, part_id, quantity)`
- `receive_stock(conn, part_id, quantity, unit_cost=None)`
- `get_low_stock_parts(conn)`

الوظائف في `scripts/parts_tracker.py`:

- `use_part_in_work_order(conn, work_order_id, part_id, quantity)` —
  يخصم المخزون ويضيف بند الفاتورة بسعر البيع مع هامش الربح في خطوة
  واحدة.
- `calculate_margin(part)` — هامش الربح (المبلغ والنسبة) لقطعة معينة.
- `get_part_usage_history(conn, part_id)` — سجل استخدام القطعة
  (التاريخ، أمر العمل، المركبة).
- `get_most_used_parts(conn, limit=10)` — أكثر القطع استخداماً.

الوظائف في `scripts/inventory_alert.py`:

- `get_out_of_stock_parts(conn)` / `get_low_stock_parts(conn)` — 🔴
  النافدة و 🟡 القاربة على النفاد.
- `build_reorder_items(conn)` — يبني قائمة بنود إعادة الطلب المقترحة
  مع الكمية المقترحة وتكلفتها.
- `calculate_suggested_order_cost(items)` — التكلفة الإجمالية المقترحة.
- `build_whatsapp_report(out_of_stock, low_stock, total_cost, approval_link=None, lang="ar")`
  — نص تقرير المخزون الصباحي الجاهز لواتساب (عربي/إنجليزي).
- `save_reorder_request(conn, items, notes=None)` — يحفظ طلب إعادة
  التوريد في `reorder_requests` / `reorder_request_items`.
- `run_daily_inventory_check(conn, lang="ar", approval_link=None)` —
  ينفّذ الفحص الكامل ويُعيد `{"message", "reorder_request_id", "total_cost"}`.

## مراجع تفصيلية | Reference files
- `reference/suppliers_sa.md` — الموردون المعتمدون مصنّفون: فئة A (قطع
  أصلية OEM) مع وقت التوصيل والحد الأدنى للطلب وطريقة الدفع، فئة B (قطع
  بديلة موثوقة مثل Bosch/NGK/Monroe) مع متى يُنصح بالأصلي ومتى يكفي
  البديل، وفئة C (موردو الإطارات والمقاسات الأكثر طلباً في السعودية).
- `reference/critical_parts.md` — تصنيف القطع الحرجة (🔴 يومي / 🟡
  أسبوعي / 🟢 شهري) مع الكمية الدنيا المقترحة، نقطة إعادة الطلب،
  والمورد المفضل والبديل لكل قطعة.

## ملاحظات للسوق السعودي | Saudi market notes
- `unit_cost` و `unit_price` يتم تخزينهما **بدون ضريبة القيمة المضافة**؛
  تُضاف الضريبة عند إصدار الفاتورة (راجع مهارة `pricing_invoicing`).
- يفضَّل استخدام رموز (SKU) موحّدة تطابق كتالوج المورّد لتسهيل إعادة
  الطلب.
