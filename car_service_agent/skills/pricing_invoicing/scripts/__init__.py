"""دوال مهارة التسعير والفواتير | Pricing & invoicing helpers."""

from __future__ import annotations

import sqlite3


def issue_invoice(conn: sqlite3.Connection, work_order_id: int, vat_rate: float = 0.15) -> int:
    """يصدر فاتورة لأمر عمل بناءً على بنود العمل وقطع الغيار، ويُعيد invoice_id."""
    # تجنّب إصدار فاتورة مكررة لنفس أمر العمل
    existing = conn.execute(
        "SELECT invoice_id FROM invoices WHERE work_order_id = ?", (work_order_id,)
    ).fetchone()
    if existing:
        return existing["invoice_id"]

    labor_total = conn.execute(
        "SELECT COALESCE(SUM(hours * rate), 0) AS total FROM work_order_labor "
        "WHERE work_order_id = ?",
        (work_order_id,),
    ).fetchone()["total"]

    parts_total = conn.execute(
        "SELECT COALESCE(SUM(quantity * unit_price), 0) AS total FROM work_order_parts "
        "WHERE work_order_id = ?",
        (work_order_id,),
    ).fetchone()["total"]

    subtotal = round(labor_total + parts_total, 2)
    vat_amount = round(subtotal * vat_rate, 2)
    total = round(subtotal + vat_amount, 2)

    cur = conn.execute(
        "INSERT INTO invoices (work_order_id, subtotal, vat_rate, vat_amount, total, status) "
        "VALUES (?, ?, ?, ?, ?, 'unpaid')",
        (work_order_id, subtotal, vat_rate, vat_amount, total),
    )
    conn.commit()
    return cur.lastrowid


def mark_invoice_paid(conn: sqlite3.Connection, invoice_id: int) -> None:
    """يسجّل دفع الفاتورة."""
    conn.execute(
        "UPDATE invoices SET status = 'paid', paid_at = datetime('now') "
        "WHERE invoice_id = ?",
        (invoice_id,),
    )
    conn.commit()


def get_invoice(conn: sqlite3.Connection, work_order_id: int) -> sqlite3.Row | None:
    """يُعيد فاتورة أمر عمل إن وُجدت."""
    return conn.execute(
        "SELECT * FROM invoices WHERE work_order_id = ?", (work_order_id,)
    ).fetchone()


def format_invoice_text(invoice: sqlite3.Row, summary: dict, lang: str = "ar") -> str:
    """يولّد نصاً جاهزاً لإرسال تفاصيل الفاتورة للعميل (عربي/إنجليزي)."""
    wo = summary["work_order"]
    customer = summary["customer"]
    vehicle = summary["vehicle"]

    lines_ar = [f"فاتورة أمر العمل رقم {wo['work_order_id']}"]
    lines_en = [f"Invoice for Work Order #{wo['work_order_id']}"]

    if customer:
        lines_ar.append(f"العميل: {customer['name']}")
        lines_en.append(f"Customer: {customer['name']}")
    if vehicle:
        lines_ar.append(
            f"المركبة: {vehicle['make']} {vehicle['model']} {vehicle['year'] or ''} - "
            f"لوحة {vehicle['plate_number']}"
        )
        lines_en.append(
            f"Vehicle: {vehicle['make']} {vehicle['model']} {vehicle['year'] or ''} - "
            f"Plate {vehicle['plate_number']}"
        )

    lines_ar.append("")
    lines_en.append("")
    lines_ar.append("البنود:")
    lines_en.append("Items:")

    for item in summary["labor_items"]:
        amount = round(item["hours"] * item["rate"], 2)
        lines_ar.append(
            f"- {item['description']} ({item['hours']} ساعة × {item['rate']:.2f} ريال) = {amount:.2f} ريال"
        )
        lines_en.append(
            f"- {item['description']} ({item['hours']} hr x {item['rate']:.2f} SAR) = {amount:.2f} SAR"
        )

    for item in summary["part_items"]:
        amount = round(item["quantity"] * item["unit_price"], 2)
        name = item["name_ar"] if lang == "ar" else (item["name_en"] or item["name_ar"])
        lines_ar.append(f"- {name} × {item['quantity']} = {amount:.2f} ريال")
        lines_en.append(f"- {name} x {item['quantity']} = {amount:.2f} SAR")

    lines_ar.append("")
    lines_en.append("")
    lines_ar.append(f"الإجمالي قبل الضريبة: {invoice['subtotal']:.2f} ريال")
    lines_en.append(f"Subtotal: {invoice['subtotal']:.2f} SAR")
    lines_ar.append(f"ضريبة القيمة المضافة ({invoice['vat_rate'] * 100:.0f}%): {invoice['vat_amount']:.2f} ريال")
    lines_en.append(f"VAT ({invoice['vat_rate'] * 100:.0f}%): {invoice['vat_amount']:.2f} SAR")
    lines_ar.append(f"الإجمالي شامل الضريبة: {invoice['total']:.2f} ريال")
    lines_en.append(f"Total (incl. VAT): {invoice['total']:.2f} SAR")

    return "\n".join(lines_ar if lang == "ar" else lines_en)
