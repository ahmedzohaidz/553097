"""دوال مهارة إدارة الفنيين | Technician management helpers."""

from __future__ import annotations

import sqlite3

ALLOWED_FIELDS = {"name", "specialty", "phone", "hourly_rate"}


def add_technician(
    conn: sqlite3.Connection,
    name: str,
    specialty: str | None = None,
    phone: str | None = None,
    hourly_rate: float = 0,
) -> int:
    """يضيف فنياً جديداً ويُعيد technician_id."""
    cur = conn.execute(
        "INSERT INTO technicians (name, specialty, phone, hourly_rate) VALUES (?, ?, ?, ?)",
        (name, specialty, phone, hourly_rate),
    )
    conn.commit()
    return cur.lastrowid


def update_technician(conn: sqlite3.Connection, technician_id: int, **fields) -> None:
    """يحدّث حقولاً محددة لفني (name, specialty, phone, hourly_rate)."""
    updates = {key: value for key, value in fields.items() if key in ALLOWED_FIELDS}
    if not updates:
        return

    set_clause = ", ".join(f"{key} = ?" for key in updates)
    params = list(updates.values()) + [technician_id]
    conn.execute(f"UPDATE technicians SET {set_clause} WHERE technician_id = ?", params)
    conn.commit()


def set_technician_active(conn: sqlite3.Connection, technician_id: int, is_active: bool) -> None:
    """يفعّل أو يعطّل فنياً دون حذف سجله."""
    conn.execute(
        "UPDATE technicians SET is_active = ? WHERE technician_id = ?",
        (1 if is_active else 0, technician_id),
    )
    conn.commit()


def list_technicians(conn: sqlite3.Connection, active_only: bool = True) -> list[sqlite3.Row]:
    """يُعيد قائمة الفنيين (النشطين فقط بشكل افتراضي)."""
    if active_only:
        return conn.execute("SELECT * FROM technicians WHERE is_active = 1 ORDER BY name").fetchall()
    return conn.execute("SELECT * FROM technicians ORDER BY name").fetchall()


def get_technician_workload(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """يُعيد عدد أوامر العمل المفتوحة لكل فني نشط."""
    return conn.execute(
        """
        SELECT t.technician_id, t.name, t.specialty,
               COUNT(wo.work_order_id) AS open_work_orders
        FROM technicians t
        LEFT JOIN work_orders wo
            ON wo.assigned_technician_id = t.technician_id
            AND wo.status NOT IN ('delivered', 'cancelled')
        WHERE t.is_active = 1
        GROUP BY t.technician_id, t.name, t.specialty
        ORDER BY open_work_orders ASC, t.name
        """
    ).fetchall()
