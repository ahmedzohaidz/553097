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
2. **الاستخدام في أمر عمل**:
   - تحقق أن `quantity_on_hand >= quantity_needed`.
   - استدعِ `consume_stock` لخصم الكمية.
   - استخدم `add_part_item` (من مهارة `work_orders`) لتسجيل البند في
     أمر العمل بسعر `unit_price` الحالي للقطعة.
3. **استلام شحنة**: استخدم `receive_stock` لزيادة `quantity_on_hand`
   وتحديث `unit_cost` إن تغيّر.
4. **مراجعة حدود إعادة الطلب**: استخدم `get_low_stock_parts` للحصول على
   قائمة القطع التي `quantity_on_hand <= reorder_level`، وأرسلها لمدير
   المخزون (يمكن تضمينها في تقرير دوري عبر مهارة `reports`).

## الأدوات المتاحة | Available tools
الوظائف في `scripts.py`:

- `add_part(conn, sku, name_ar, name_en, unit_cost, unit_price, quantity_on_hand=0, reorder_level=5, supplier=None)`
- `get_part_by_sku(conn, sku)`
- `search_parts(conn, query)`
- `consume_stock(conn, part_id, quantity)`
- `receive_stock(conn, part_id, quantity, unit_cost=None)`
- `get_low_stock_parts(conn)`

## ملاحظات للسوق السعودي | Saudi market notes
- `unit_cost` و `unit_price` يتم تخزينهما **بدون ضريبة القيمة المضافة**؛
  تُضاف الضريبة عند إصدار الفاتورة (راجع مهارة `pricing_invoicing`).
- يفضَّل استخدام رموز (SKU) موحّدة تطابق كتالوج المورّد لتسهيل إعادة
  الطلب.
