"""
طبقة الوصول لقاعدة البيانات | Database access layer
======================================================
يوفر هذا الملف اتصالاً بقاعدة بيانات SQLite الخاصة بمركز الصيانة، وينشئ
الجدوال تلقائياً من schema.sql عند أول تشغيل، ويعرض دوال مساعدة مشتركة
تستخدمها مهارات الوكيل (skills).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
DEFAULT_DB_PATH = BASE_DIR / "data" / "service_center.db"


def get_connection(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """يفتح اتصالاً بقاعدة البيانات مع تفعيل الصفوف كقواميس."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    """ينشئ الجداول إذا لم تكن موجودة باستخدام schema.sql."""
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = get_connection(db_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()


def calculate_vat(subtotal: float, vat_rate: float = 0.15) -> tuple[float, float]:
    """يحسب قيمة ضريبة القيمة المضافة والإجمالي شامل الضريبة.

    Returns:
        (vat_amount, total)
    """
    vat_amount = round(subtotal * vat_rate, 2)
    total = round(subtotal + vat_amount, 2)
    return vat_amount, total
