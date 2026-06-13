"""دوال مهارة قطع الغيار والمخزون | Parts & inventory helpers."""

from __future__ import annotations

import sqlite3


def add_part(
    conn: sqlite3.Connection,
    sku: str,
    name_ar: str,
    name_en: str | None,
    unit_cost: float,
    unit_price: float,
    quantity_on_hand: int = 0,
    reorder_level: int = 5,
    supplier: str | None = None,
) -> int:
    """يضيف قطعة غيار جديدة للكتالوج ويُعيد part_id."""
    cur = conn.execute(
        "INSERT INTO parts (sku, name_ar, name_en, unit_cost, unit_price, "
        "quantity_on_hand, reorder_level, supplier) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (sku, name_ar, name_en, unit_cost, unit_price, quantity_on_hand, reorder_level, supplier),
    )
    conn.commit()
    return cur.lastrowid


def get_part_by_sku(conn: sqlite3.Connection, sku: str) -> sqlite3.Row | None:
    """يبحث عن قطعة برمز SKU."""
    return conn.execute("SELECT * FROM parts WHERE sku = ?", (sku,)).fetchone()


def search_parts(conn: sqlite3.Connection, query: str) -> list[sqlite3.Row]:
    """يبحث عن قطع غيار بالاسم العربي أو الإنجليزي أو رمز SKU."""
    like = f"%{query}%"
    return conn.execute(
        "SELECT * FROM parts WHERE name_ar LIKE ? OR name_en LIKE ? OR sku LIKE ? "
        "ORDER BY name_ar",
        (like, like, like),
    ).fetchall()


def consume_stock(conn: sqlite3.Connection, part_id: int, quantity: int) -> None:
    """يخصم كمية من المخزون عند استخدام قطعة في أمر عمل."""
    part = conn.execute("SELECT quantity_on_hand FROM parts WHERE part_id = ?", (part_id,)).fetchone()
    if part is None:
        raise ValueError(f"القطعة غير موجودة: {part_id}")
    if part["quantity_on_hand"] < quantity:
        raise ValueError("الكمية المطلوبة غير متوفرة في المخزون")

    conn.execute(
        "UPDATE parts SET quantity_on_hand = quantity_on_hand - ?, updated_at = datetime('now') "
        "WHERE part_id = ?",
        (quantity, part_id),
    )
    conn.commit()


def receive_stock(conn: sqlite3.Connection, part_id: int, quantity: int, unit_cost: float | None = None) -> None:
    """يضيف كمية للمخزون عند استلام شحنة من المورد، ويحدّث التكلفة إن تغيّرت."""
    if unit_cost is not None:
        conn.execute(
            "UPDATE parts SET quantity_on_hand = quantity_on_hand + ?, unit_cost = ?, "
            "updated_at = datetime('now') WHERE part_id = ?",
            (quantity, unit_cost, part_id),
        )
    else:
        conn.execute(
            "UPDATE parts SET quantity_on_hand = quantity_on_hand + ?, updated_at = datetime('now') "
            "WHERE part_id = ?",
            (quantity, part_id),
        )
    conn.commit()


def get_low_stock_parts(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """يُعيد القطع التي وصلت إلى حد إعادة الطلب أو أقل."""
    return conn.execute(
        "SELECT * FROM parts WHERE quantity_on_hand <= reorder_level ORDER BY quantity_on_hand"
    ).fetchall()
