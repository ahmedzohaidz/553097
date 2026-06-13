"""دوال مهارة إدارة أوامر العمل | Work order management helpers."""

from __future__ import annotations

import sqlite3

VALID_STATUSES = {
    "received",
    "diagnosing",
    "awaiting_approval",
    "in_progress",
    "completed",
    "delivered",
    "cancelled",
}


def assign_technician(conn: sqlite3.Connection, work_order_id: int, technician_id: int) -> None:
    """يعيّن فنياً مسؤولاً عن أمر العمل."""
    conn.execute(
        "UPDATE work_orders SET assigned_technician_id = ?, updated_at = datetime('now') "
        "WHERE work_order_id = ?",
        (technician_id, work_order_id),
    )
    conn.commit()


def add_labor_item(
    conn: sqlite3.Connection,
    work_order_id: int,
    description: str,
    hours: float,
    rate: float,
    technician_id: int | None = None,
) -> int:
    """يضيف بند عمل (ساعات + سعر الساعة) لأمر العمل."""
    cur = conn.execute(
        "INSERT INTO work_order_labor (work_order_id, technician_id, description, hours, rate) "
        "VALUES (?, ?, ?, ?, ?)",
        (work_order_id, technician_id, description, hours, rate),
    )
    conn.commit()
    return cur.lastrowid


def add_part_item(conn: sqlite3.Connection, work_order_id: int, part_id: int, quantity: int, unit_price: float) -> int:
    """يضيف بند قطعة غيار مستخدمة لأمر العمل."""
    cur = conn.execute(
        "INSERT INTO work_order_parts (work_order_id, part_id, quantity, unit_price) "
        "VALUES (?, ?, ?, ?)",
        (work_order_id, part_id, quantity, unit_price),
    )
    conn.commit()
    return cur.lastrowid


def set_status(conn: sqlite3.Connection, work_order_id: int, status: str) -> None:
    """يحدّث حالة أمر العمل بعد التحقق من صحتها."""
    if status not in VALID_STATUSES:
        raise ValueError(f"حالة غير صالحة: {status}")

    conn.execute(
        "UPDATE work_orders SET status = ?, updated_at = datetime('now') "
        "WHERE work_order_id = ?",
        (status, work_order_id),
    )
    conn.commit()


def mark_delivered(conn: sqlite3.Connection, work_order_id: int) -> None:
    """يسجّل تسليم السيارة للعميل ويغيّر الحالة إلى 'delivered'."""
    conn.execute(
        "UPDATE work_orders SET status = 'delivered', "
        "updated_at = datetime('now'), delivered_at = datetime('now') "
        "WHERE work_order_id = ?",
        (work_order_id,),
    )
    conn.commit()


def get_open_work_orders(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """يُعيد جميع أوامر العمل غير المسلَّمة أو الملغاة."""
    return conn.execute(
        "SELECT * FROM work_orders WHERE status NOT IN ('delivered', 'cancelled') "
        "ORDER BY created_at"
    ).fetchall()


def get_work_order_summary(conn: sqlite3.Connection, work_order_id: int) -> dict:
    """يُعيد ملخصاً شاملاً لأمر العمل: العميل، المركبة، البنود، والإجمالي قبل الضريبة."""
    work_order = conn.execute(
        "SELECT * FROM work_orders WHERE work_order_id = ?", (work_order_id,)
    ).fetchone()
    if not work_order:
        raise ValueError(f"أمر العمل غير موجود: {work_order_id}")

    vehicle = conn.execute(
        "SELECT * FROM vehicles WHERE vehicle_id = ?", (work_order["vehicle_id"],)
    ).fetchone()
    customer = conn.execute(
        "SELECT * FROM customers WHERE customer_id = ?", (work_order["customer_id"],)
    ).fetchone()
    labor_items = conn.execute(
        "SELECT * FROM work_order_labor WHERE work_order_id = ?", (work_order_id,)
    ).fetchall()
    part_items = conn.execute(
        "SELECT wop.*, p.name_ar, p.name_en, p.sku "
        "FROM work_order_parts wop JOIN parts p ON p.part_id = wop.part_id "
        "WHERE wop.work_order_id = ?",
        (work_order_id,),
    ).fetchall()

    labor_total = sum(row["hours"] * row["rate"] for row in labor_items)
    parts_total = sum(row["quantity"] * row["unit_price"] for row in part_items)

    return {
        "work_order": dict(work_order),
        "vehicle": dict(vehicle) if vehicle else None,
        "customer": dict(customer) if customer else None,
        "labor_items": [dict(row) for row in labor_items],
        "part_items": [dict(row) for row in part_items],
        "labor_total": round(labor_total, 2),
        "parts_total": round(parts_total, 2),
        "subtotal": round(labor_total + parts_total, 2),
    }
