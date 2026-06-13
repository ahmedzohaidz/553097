"""دوال مهارة تشخيص الأعطال | Diagnostics helpers."""

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


def add_diagnostic(
    conn: sqlite3.Connection,
    work_order_id: int,
    findings: str,
    technician_id: int | None = None,
    obd_codes: str | None = None,
    recommendation: str | None = None,
    severity: str = "medium",
) -> int:
    """يضيف سجل تشخيص جديد لأمر عمل ويُعيد diagnostic_id."""
    if severity not in {"low", "medium", "high", "critical"}:
        raise ValueError(f"severity غير صالحة: {severity}")

    cur = conn.execute(
        "INSERT INTO diagnostics "
        "(work_order_id, technician_id, obd_codes, findings, recommendation, severity) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (work_order_id, technician_id, obd_codes, findings, recommendation, severity),
    )
    conn.commit()
    return cur.lastrowid


def update_work_order_status(conn: sqlite3.Connection, work_order_id: int, status: str) -> None:
    """يحدّث حالة أمر العمل."""
    if status not in VALID_STATUSES:
        raise ValueError(f"حالة غير صالحة: {status}")

    conn.execute(
        "UPDATE work_orders SET status = ?, updated_at = datetime('now') "
        "WHERE work_order_id = ?",
        (status, work_order_id),
    )
    conn.commit()


def get_diagnostics_for_work_order(conn: sqlite3.Connection, work_order_id: int) -> list[sqlite3.Row]:
    """يُعيد جميع سجلات التشخيص لأمر عمل معين."""
    return conn.execute(
        "SELECT * FROM diagnostics WHERE work_order_id = ? ORDER BY created_at",
        (work_order_id,),
    ).fetchall()
