"""دوال مهارة التقارير والأداء | Reports & performance helpers."""

from __future__ import annotations

import sqlite3


def _date_filter(column: str, start_date: str | None, end_date: str | None) -> tuple[str, list]:
    """يبني شرط WHERE اختياري لفلترة التاريخ، ويُعيد (sql_fragment, params)."""
    conditions = []
    params: list = []
    if start_date:
        conditions.append(f"{column} >= ?")
        params.append(start_date)
    if end_date:
        conditions.append(f"{column} <= ?")
        params.append(end_date + " 23:59:59")

    if not conditions:
        return "", params
    return "WHERE " + " AND ".join(conditions), params


def revenue_summary(conn: sqlite3.Connection, start_date: str | None = None, end_date: str | None = None) -> dict:
    """يُعيد ملخص الإيرادات وضريبة القيمة المضافة لفترة معينة."""
    where_sql, params = _date_filter("issued_at", start_date, end_date)

    row = conn.execute(
        f"SELECT COUNT(*) AS invoice_count, "
        f"COALESCE(SUM(subtotal), 0) AS subtotal, "
        f"COALESCE(SUM(vat_amount), 0) AS vat_amount, "
        f"COALESCE(SUM(total), 0) AS total "
        f"FROM invoices {where_sql}",
        params,
    ).fetchone()

    paid_where_sql, paid_params = _date_filter("issued_at", start_date, end_date)
    if paid_where_sql:
        paid_where_sql += " AND status = 'paid'"
    else:
        paid_where_sql = "WHERE status = 'paid'"

    paid_total = conn.execute(
        f"SELECT COALESCE(SUM(total), 0) AS total FROM invoices {paid_where_sql}",
        paid_params,
    ).fetchone()["total"]

    return {
        "invoice_count": row["invoice_count"],
        "subtotal": round(row["subtotal"], 2),
        "vat_amount": round(row["vat_amount"], 2),
        "total": round(row["total"], 2),
        "paid_total": round(paid_total, 2),
        "unpaid_total": round(row["total"] - paid_total, 2),
    }


def work_order_status_breakdown(conn: sqlite3.Connection) -> dict[str, int]:
    """يُعيد عدد أوامر العمل حسب كل حالة."""
    rows = conn.execute(
        "SELECT status, COUNT(*) AS count FROM work_orders GROUP BY status"
    ).fetchall()
    return {row["status"]: row["count"] for row in rows}


def technician_performance(conn: sqlite3.Connection, start_date: str | None = None, end_date: str | None = None) -> list[dict]:
    """يُعيد عدد أوامر العمل المكتملة وساعات العمل لكل فني خلال فترة معينة."""
    where_sql, params = _date_filter("wo.updated_at", start_date, end_date)
    extra = "AND wo.status IN ('completed', 'delivered')"
    if where_sql:
        where_sql += f" {extra}"
    else:
        where_sql = f"WHERE {extra[4:]}"

    rows = conn.execute(
        f"""
        SELECT t.technician_id, t.name,
               COUNT(DISTINCT wo.work_order_id) AS completed_orders,
               COALESCE(SUM(wol.hours), 0) AS total_hours
        FROM technicians t
        LEFT JOIN work_orders wo ON wo.assigned_technician_id = t.technician_id
        LEFT JOIN work_order_labor wol ON wol.work_order_id = wo.work_order_id
        {where_sql}
        GROUP BY t.technician_id, t.name
        ORDER BY completed_orders DESC
        """,
        params,
    ).fetchall()
    return [dict(row) for row in rows]


def low_stock_report(conn: sqlite3.Connection) -> list[dict]:
    """يُعيد قطع الغيار التي وصلت لحد إعادة الطلب أو أقل."""
    rows = conn.execute(
        "SELECT sku, name_ar, name_en, quantity_on_hand, reorder_level, supplier "
        "FROM parts WHERE quantity_on_hand <= reorder_level ORDER BY quantity_on_hand"
    ).fetchall()
    return [dict(row) for row in rows]


def customer_satisfaction(conn: sqlite3.Connection, start_date: str | None = None, end_date: str | None = None) -> dict:
    """يُعيد متوسط تقييم العملاء وعدد التقييمات لفترة معينة."""
    where_sql, params = _date_filter("created_at", start_date, end_date)

    row = conn.execute(
        f"SELECT COUNT(*) AS feedback_count, AVG(rating) AS average_rating "
        f"FROM customer_feedback {where_sql}",
        params,
    ).fetchone()

    return {
        "feedback_count": row["feedback_count"],
        "average_rating": round(row["average_rating"], 2) if row["average_rating"] is not None else None,
    }
