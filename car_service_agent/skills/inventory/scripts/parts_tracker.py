"""
تتبع استخدام قطع الغيار | Parts usage tracking
==================================================

يوفّر هذا السكريبت دالة موحّدة لاستخدام قطعة غيار في أمر عمل: تخصم
الكمية من المخزون تلقائياً (`parts.quantity_on_hand`)، تضيف بند القطعة
للفاتورة بسعر البيع الحالي (الذي يشمل هامش الربح عن تكلفة الشراء)،
وتسمح باستعراض سجل استخدام كل قطعة (التاريخ والمركبة المرتبطة).
"""

from __future__ import annotations

import sqlite3


def calculate_margin(part: sqlite3.Row) -> dict:
    """يحسب هامش الربح لكل وحدة ونسبته لقطعة معينة."""
    unit_cost = part["unit_cost"]
    unit_price = part["unit_price"]
    margin_amount = round(unit_price - unit_cost, 2)
    margin_percent = round((margin_amount / unit_cost) * 100, 2) if unit_cost else None
    return {
        "unit_cost": unit_cost,
        "unit_price": unit_price,
        "margin_amount": margin_amount,
        "margin_percent": margin_percent,
    }


def use_part_in_work_order(conn: sqlite3.Connection, work_order_id: int, part_id: int, quantity: int) -> dict:
    """يسجّل استخدام قطعة غيار في أمر عمل: يخصم المخزون ويضيف بند الفاتورة بسعر البيع.

    Returns:
        ملخص يتضمن part_id، الكمية، سعر البيع المستخدم، هامش الربح،
        وقيمة البند الإجمالية (بدون ضريبة).
    """
    part = conn.execute("SELECT * FROM parts WHERE part_id = ?", (part_id,)).fetchone()
    if part is None:
        raise ValueError(f"القطعة غير موجودة: {part_id}")
    if part["quantity_on_hand"] < quantity:
        raise ValueError(
            f"الكمية المطلوبة ({quantity}) غير متوفرة في المخزون "
            f"(المتوفر: {part['quantity_on_hand']})"
        )

    # خصم المخزون
    conn.execute(
        "UPDATE parts SET quantity_on_hand = quantity_on_hand - ?, updated_at = datetime('now') "
        "WHERE part_id = ?",
        (quantity, part_id),
    )

    # إضافة بند الفاتورة بسعر البيع الحالي (يشمل هامش الربح عن التكلفة)
    unit_price = part["unit_price"]
    conn.execute(
        "INSERT INTO work_order_parts (work_order_id, part_id, quantity, unit_price) "
        "VALUES (?, ?, ?, ?)",
        (work_order_id, part_id, quantity, unit_price),
    )
    conn.commit()

    margin = calculate_margin(part)
    return {
        "part_id": part_id,
        "sku": part["sku"],
        "quantity": quantity,
        "unit_price": unit_price,
        "line_total": round(unit_price * quantity, 2),
        "margin_amount_per_unit": margin["margin_amount"],
        "margin_percent": margin["margin_percent"],
    }


def get_part_usage_history(conn: sqlite3.Connection, part_id: int) -> list[dict]:
    """يُعيد سجل استخدام قطعة معينة: التاريخ، أمر العمل، والمركبة المرتبطة."""
    rows = conn.execute(
        """
        SELECT wop.created_at, wop.work_order_id, wop.quantity, wop.unit_price,
               v.plate_number, v.make, v.model, v.year
        FROM work_order_parts wop
        JOIN work_orders wo ON wo.work_order_id = wop.work_order_id
        JOIN vehicles v ON v.vehicle_id = wo.vehicle_id
        WHERE wop.part_id = ?
        ORDER BY wop.created_at DESC
        """,
        (part_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def get_most_used_parts(conn: sqlite3.Connection, limit: int = 10) -> list[dict]:
    """يُعيد القطع الأكثر استخداماً (بالكمية الإجمالية المستخدمة)."""
    rows = conn.execute(
        """
        SELECT p.part_id, p.sku, p.name_ar, p.name_en,
               SUM(wop.quantity) AS total_quantity_used,
               SUM(wop.quantity * wop.unit_price) AS total_revenue
        FROM work_order_parts wop
        JOIN parts p ON p.part_id = wop.part_id
        GROUP BY p.part_id, p.sku, p.name_ar, p.name_en
        ORDER BY total_quantity_used DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]
