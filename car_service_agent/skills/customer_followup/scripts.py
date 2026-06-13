"""دوال مهارة متابعة العميل عبر واتساب | Customer follow-up (WhatsApp) helpers."""

from __future__ import annotations

import sqlite3

import requests

from config import (
    WHATSAPP_API_BASE_URL,
    WHATSAPP_API_TOKEN,
    WHATSAPP_API_VERSION,
    WHATSAPP_PHONE_NUMBER_ID,
)

VALID_MESSAGE_TYPES = {
    "status_update",
    "approval_request",
    "ready_for_pickup",
    "feedback_request",
    "reminder",
}

STATUS_MESSAGES = {
    "received": {
        "ar": "تم استلام سيارتكم في المركز وسيتم البدء بالفحص قريباً.",
        "en": "Your vehicle has been received and inspection will begin shortly.",
    },
    "diagnosing": {
        "ar": "جارٍ فحص سيارتكم حالياً من قبل فريقنا الفني.",
        "en": "Our technicians are currently diagnosing your vehicle.",
    },
    "awaiting_approval": {
        "ar": "تم اكتشاف أعمال إضافية مطلوبة. يرجى مراجعة التفاصيل والموافقة للمتابعة.",
        "en": "Additional work has been identified. Please review and approve to proceed.",
    },
    "in_progress": {
        "ar": "جارٍ تنفيذ أعمال الصيانة على سيارتكم.",
        "en": "Maintenance work on your vehicle is now in progress.",
    },
    "completed": {
        "ar": "تم إنجاز جميع الأعمال على سيارتكم. سيتم إرسال تفاصيل الفاتورة قريباً.",
        "en": "All work on your vehicle has been completed. Invoice details will follow shortly.",
    },
    "delivered": {
        "ar": "شكراً لزيارتكم! تم تسليم سيارتكم بنجاح.",
        "en": "Thank you for visiting us! Your vehicle has been delivered successfully.",
    },
}


def queue_followup(
    conn: sqlite3.Connection,
    customer_id: int,
    message_type: str,
    message_body: str,
    work_order_id: int | None = None,
    channel: str = "whatsapp",
) -> int:
    """يسجّل رسالة متابعة في قائمة الانتظار ويُعيد followup_id."""
    if message_type not in VALID_MESSAGE_TYPES:
        raise ValueError(f"نوع رسالة غير صالح: {message_type}")

    cur = conn.execute(
        "INSERT INTO followups (customer_id, work_order_id, channel, message_type, message_body, status) "
        "VALUES (?, ?, ?, ?, ?, 'queued')",
        (customer_id, work_order_id, channel, message_type, message_body),
    )
    conn.commit()
    return cur.lastrowid


def send_whatsapp_message(phone: str, message: str) -> bool:
    """يرسل رسالة نصية عبر WhatsApp Business Cloud API (Meta).

    ملاحظة: هذه دالة "stub" - تحتاج لضبط WHATSAPP_API_TOKEN و
    WHATSAPP_PHONE_NUMBER_ID في متغيرات البيئة (راجع config.py) قبل
    استخدامها في بيئة الإنتاج. تُعيد True عند نجاح الإرسال (HTTP 2xx).
    """
    if not WHATSAPP_API_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        raise RuntimeError(
            "إعدادات واتساب غير مكتملة: يجب ضبط WHATSAPP_API_TOKEN و "
            "WHATSAPP_PHONE_NUMBER_ID في متغيرات البيئة."
        )

    url = (
        f"{WHATSAPP_API_BASE_URL}/{WHATSAPP_API_VERSION}/"
        f"{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    headers = {
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": message},
    }

    response = requests.post(url, headers=headers, json=payload, timeout=10)
    return response.ok


def mark_followup_status(conn: sqlite3.Connection, followup_id: int, status: str) -> None:
    """يحدّث حالة رسالة المتابعة (queued/sent/failed/replied)."""
    if status not in {"queued", "sent", "failed", "replied"}:
        raise ValueError(f"حالة غير صالحة: {status}")

    conn.execute("UPDATE followups SET status = ? WHERE followup_id = ?", (status, followup_id))
    conn.commit()


def record_feedback(
    conn: sqlite3.Connection,
    work_order_id: int,
    customer_id: int,
    rating: int,
    comments: str | None = None,
) -> int:
    """يسجّل تقييم العميل لخدمة معينة (1-5)."""
    if not 1 <= rating <= 5:
        raise ValueError("التقييم يجب أن يكون بين 1 و 5")

    cur = conn.execute(
        "INSERT INTO customer_feedback (work_order_id, customer_id, rating, comments) "
        "VALUES (?, ?, ?, ?)",
        (work_order_id, customer_id, rating, comments),
    )
    conn.commit()
    return cur.lastrowid


def build_status_message(status: str, lang: str = "ar") -> str:
    """يولّد نص رسالة تحديث حالة (عربي/إنجليزي) لأمر عمل."""
    template = STATUS_MESSAGES.get(status)
    if not template:
        return ""
    return template.get(lang, template["ar"])
