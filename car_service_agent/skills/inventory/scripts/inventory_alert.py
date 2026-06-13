"""
نظام التنبيه الصباحي للمخزون | Daily inventory alert system
================================================================

يفحص هذا السكريبت كل قطع الغيار، يحدد ما وصل لحد إعادة الطلب أو نفد
بالكامل، يولّد تقرير واتساب جاهزاً للمدير (عربي/إنجليزي)، يحسب تكلفة
الطلب المقترح، ويحفظ سجل الطلب المقترح في قاعدة البيانات
(`reorder_requests` / `reorder_request_items`) لمراجعته واعتماده لاحقاً.

التصنيف (راجع `reference/critical_parts.md`):
- 🔴 نفدت بالكامل: quantity_on_hand <= 0
- 🟡 قاربت على النفاد: 0 < quantity_on_hand <= reorder_level
"""

from __future__ import annotations

import sqlite3
from datetime import date


def get_out_of_stock_parts(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """يُعيد القطع التي نفدت بالكامل من المخزون."""
    return conn.execute(
        "SELECT * FROM parts WHERE quantity_on_hand <= 0 ORDER BY name_ar"
    ).fetchall()


def get_low_stock_parts(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """يُعيد القطع التي قاربت على النفاد (أعلى من صفر وحتى حد إعادة الطلب)."""
    return conn.execute(
        "SELECT * FROM parts WHERE quantity_on_hand > 0 AND quantity_on_hand <= reorder_level "
        "ORDER BY quantity_on_hand"
    ).fetchall()


def calculate_suggested_quantity(part: sqlite3.Row) -> int:
    """يحسب الكمية المقترحة لإعادة الطلب لإعادة المخزون إلى ضِعف حد إعادة الطلب."""
    target = max(part["reorder_level"] * 2, 1)
    suggested = target - part["quantity_on_hand"]
    return max(suggested, part["reorder_level"], 1)


def build_reorder_items(conn: sqlite3.Connection) -> list[dict]:
    """يبني قائمة بنود إعادة الطلب المقترحة (نافدة + قاربت على النفاد)."""
    items = []
    for part in list(get_out_of_stock_parts(conn)) + list(get_low_stock_parts(conn)):
        quantity = calculate_suggested_quantity(part)
        items.append({
            "part_id": part["part_id"],
            "sku": part["sku"],
            "name_ar": part["name_ar"],
            "name_en": part["name_en"],
            "quantity_on_hand": part["quantity_on_hand"],
            "reorder_level": part["reorder_level"],
            "suggested_quantity": quantity,
            "unit_cost": part["unit_cost"],
            "line_total": round(quantity * part["unit_cost"], 2),
        })
    return items


def calculate_suggested_order_cost(items: list[dict]) -> float:
    """يحسب التكلفة الإجمالية المقترحة لإعادة الطلب (بدون ضريبة)."""
    return round(sum(item["line_total"] for item in items), 2)


def save_reorder_request(conn: sqlite3.Connection, items: list[dict], notes: str | None = None) -> int:
    """يحفظ طلب إعادة التوريد المقترح في قاعدة البيانات ويُعيد reorder_request_id."""
    total_cost = calculate_suggested_order_cost(items)

    cur = conn.execute(
        "INSERT INTO reorder_requests (status, total_cost, notes) VALUES ('pending', ?, ?)",
        (total_cost, notes),
    )
    reorder_request_id = cur.lastrowid

    for item in items:
        conn.execute(
            "INSERT INTO reorder_request_items (reorder_request_id, part_id, quantity, unit_cost, line_total) "
            "VALUES (?, ?, ?, ?, ?)",
            (reorder_request_id, item["part_id"], item["suggested_quantity"], item["unit_cost"], item["line_total"]),
        )

    conn.commit()
    return reorder_request_id


def build_whatsapp_report(
    out_of_stock: list[dict],
    low_stock: list[dict],
    total_cost: float,
    approval_link: str | None = None,
    lang: str = "ar",
    report_date: str | None = None,
) -> str:
    """يبني نص تقرير المخزون الصباحي الجاهز للإرسال عبر واتساب."""
    report_date = report_date or date.today().isoformat()

    if lang == "ar":
        lines = ["📦 تقرير المخزون الصباحي", f"التاريخ: {report_date}", ""]

        if out_of_stock:
            lines.append("🔴 نفدت (اطلب فوراً):")
            for item in out_of_stock:
                lines.append(f"- {item['name_ar']}: {item['quantity_on_hand']} قطعة")
            lines.append("")

        if low_stock:
            lines.append("🟡 قاربت على النفاد:")
            for item in low_stock:
                lines.append(f"- {item['name_ar']}: {item['quantity_on_hand']} قطعة")
            lines.append("")

        if not out_of_stock and not low_stock:
            lines.append("✅ المخزون في حالة جيدة - لا توجد تنبيهات اليوم.")
            lines.append("")

        if out_of_stock or low_stock:
            lines.append(f"💰 تكلفة الطلب المقترح: {total_cost:,.2f} ريال")
            if approval_link:
                lines.append(f"اضغط للموافقة: {approval_link}")
    else:
        lines = ["📦 Morning Inventory Report", f"Date: {report_date}", ""]

        if out_of_stock:
            lines.append("🔴 Out of stock (order now):")
            for item in out_of_stock:
                name = item["name_en"] or item["name_ar"]
                lines.append(f"- {name}: {item['quantity_on_hand']} unit(s)")
            lines.append("")

        if low_stock:
            lines.append("🟡 Running low:")
            for item in low_stock:
                name = item["name_en"] or item["name_ar"]
                lines.append(f"- {name}: {item['quantity_on_hand']} unit(s)")
            lines.append("")

        if not out_of_stock and not low_stock:
            lines.append("✅ Inventory levels are healthy - no alerts today.")
            lines.append("")

        if out_of_stock or low_stock:
            lines.append(f"💰 Suggested order cost: {total_cost:,.2f} SAR")
            if approval_link:
                lines.append(f"Tap to approve: {approval_link}")

    return "\n".join(lines)


def run_daily_inventory_check(
    conn: sqlite3.Connection,
    lang: str = "ar",
    approval_link: str | None = None,
) -> dict:
    """يُشغّل الفحص الصباحي الكامل: يبني التقرير، يحسب التكلفة، ويحفظ طلب إعادة التوريد.

    Returns:
        {"message": str, "reorder_request_id": int | None, "total_cost": float}
    """
    items = build_reorder_items(conn)
    out_of_stock = [item for item in items if item["quantity_on_hand"] <= 0]
    low_stock = [item for item in items if item["quantity_on_hand"] > 0]
    total_cost = calculate_suggested_order_cost(items)

    message = build_whatsapp_report(out_of_stock, low_stock, total_cost, approval_link, lang)

    reorder_request_id = None
    if items:
        reorder_request_id = save_reorder_request(conn, items, notes="Auto-generated by daily inventory check")

    return {
        "message": message,
        "reorder_request_id": reorder_request_id,
        "total_cost": total_cost,
    }
