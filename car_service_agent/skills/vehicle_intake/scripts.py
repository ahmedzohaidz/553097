"""دوال مهارة استقبال السيارة والعميل | Vehicle & customer intake helpers."""

from __future__ import annotations

import sqlite3


def find_or_create_customer(
    conn: sqlite3.Connection,
    name: str,
    phone: str,
    preferred_lang: str = "ar",
    city: str | None = None,
) -> int:
    """يبحث عن عميل برقم الهاتف أو ينشئ سجلاً جديداً، ويُعيد customer_id."""
    row = conn.execute(
        "SELECT customer_id FROM customers WHERE phone = ?", (phone,)
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE customers SET name = ?, preferred_lang = ?, city = ? "
            "WHERE customer_id = ?",
            (name, preferred_lang, city, row["customer_id"]),
        )
        conn.commit()
        return row["customer_id"]

    cur = conn.execute(
        "INSERT INTO customers (name, phone, preferred_lang, city) "
        "VALUES (?, ?, ?, ?)",
        (name, phone, preferred_lang, city),
    )
    conn.commit()
    return cur.lastrowid


def find_or_create_vehicle(
    conn: sqlite3.Connection,
    customer_id: int,
    plate_number: str,
    make: str,
    model: str,
    year: int | None = None,
    vin: str | None = None,
    odometer_km: int = 0,
) -> int:
    """يبحث عن مركبة برقم اللوحة لهذا العميل أو ينشئ سجلاً جديداً."""
    row = conn.execute(
        "SELECT vehicle_id FROM vehicles WHERE customer_id = ? AND plate_number = ?",
        (customer_id, plate_number),
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE vehicles SET odometer_km = ?, make = ?, model = ?, year = ?, vin = ? "
            "WHERE vehicle_id = ?",
            (odometer_km, make, model, year, vin, row["vehicle_id"]),
        )
        conn.commit()
        return row["vehicle_id"]

    cur = conn.execute(
        "INSERT INTO vehicles (customer_id, plate_number, make, model, year, vin, odometer_km) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (customer_id, plate_number, make, model, year, vin, odometer_km),
    )
    conn.commit()
    return cur.lastrowid


def open_work_order(
    conn: sqlite3.Connection,
    vehicle_id: int,
    customer_id: int,
    complaint: str,
    promised_at: str | None = None,
) -> int:
    """يفتح أمر عمل جديد بحالة 'received' ويُعيد work_order_id."""
    cur = conn.execute(
        "INSERT INTO work_orders (vehicle_id, customer_id, status, complaint, promised_at) "
        "VALUES (?, ?, 'received', ?, ?)",
        (vehicle_id, customer_id, complaint, promised_at),
    )
    conn.commit()
    return cur.lastrowid
