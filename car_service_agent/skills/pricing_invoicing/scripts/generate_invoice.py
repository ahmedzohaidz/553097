"""
توليد فاتورة PDF احترافية ثنائية اللغة | Bilingual professional PDF invoice
==============================================================================

يولّد هذا السكريبت ملف PDF لفاتورة أمر عمل يتضمن:
- شعار المركز (إن وُجد) وبياناته (السجل التجاري والرقم الضريبي).
- بيانات العميل والمركبة.
- تفصيل كل بند عمل (Labor) وقطعة غيار (Parts).
- حساب ضريبة القيمة المضافة (15%) بدقة.
- رقم فاتورة تسلسلي وتاريخ الإصدار.
- شروط الضمان.
- رمز QR (نمط الفاتورة الضريبية المبسّطة - ZATCA Phase 1: اسم البائع،
  الرقم الضريبي، التاريخ، الإجمالي، قيمة الضريبة).
- محتوى ثنائي اللغة (عربي/إنجليزي).

الاعتماديات: reportlab، qrcode، arabic-reshaper، python-bidi (مذكورة في
requirements.txt).

ملاحظة عن الخط العربي: PDF لا يعرض الحروف العربية بشكل صحيح إلا بخط
TTF يدعم العربية (مثل Noto Naskh Arabic). حدّد مساره عبر متغير البيئة
ARABIC_FONT_PATH (راجع config.py). بدون هذا الخط، سيُستخدم خط افتراضي
وقد لا تظهر الحروف العربية بشكل صحيح.
"""

from __future__ import annotations

import base64
import io
from datetime import datetime

import qrcode
from arabic_reshaper import reshape
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import ParagraphStyle

import config

ARABIC_FONT_NAME = "ArabicFont"
_FONT_REGISTERED = False


def _register_arabic_font() -> str:
    """يسجّل خطاً عربياً إن وُجد مساره في الإعدادات، ويُعيد اسم الخط المستخدم."""
    global _FONT_REGISTERED
    if config.ARABIC_FONT_PATH:
        if not _FONT_REGISTERED:
            pdfmetrics.registerFont(TTFont(ARABIC_FONT_NAME, config.ARABIC_FONT_PATH))
            _FONT_REGISTERED = True
        return ARABIC_FONT_NAME
    return "Helvetica"


def _ar(text: str) -> str:
    """يهيئ نصاً عربياً للعرض الصحيح (RTL shaping) داخل PDF."""
    if not text:
        return ""
    return get_display(reshape(text))


def _build_zatca_qr(seller_name: str, vat_number: str, timestamp: str, total: float, vat_amount: float) -> bytes:
    """يبني رمز QR بنمط الفاتورة الضريبية المبسّطة (ZATCA Phase 1 TLV) ويُعيد صورة PNG كـ bytes.

    الحقول: 1) اسم البائع، 2) الرقم الضريبي، 3) الطابع الزمني (ISO 8601)،
    4) إجمالي الفاتورة شامل الضريبة، 5) إجمالي ضريبة القيمة المضافة.
    """
    tlv = b""
    fields = [
        (1, seller_name.encode("utf-8")),
        (2, vat_number.encode("utf-8")),
        (3, timestamp.encode("utf-8")),
        (4, f"{total:.2f}".encode("utf-8")),
        (5, f"{vat_amount:.2f}".encode("utf-8")),
    ]
    for tag, value in fields:
        tlv += bytes([tag, len(value)]) + value

    encoded = base64.b64encode(tlv).decode("ascii")

    qr = qrcode.QRCode(border=1, box_size=4)
    qr.add_data(encoded)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def generate_invoice_pdf(invoice, summary: dict, output_path: str) -> str:
    """يولّد ملف PDF لفاتورة أمر عمل ثنائي اللغة (عربي/إنجليزي).

    Args:
        invoice: سجل الفاتورة (sqlite3.Row أو dict) من invoicing.get_invoice().
        summary: ملخص أمر العمل من work_orders.get_work_order_summary().
        output_path: المسار الكامل لحفظ ملف PDF.

    Returns:
        المسار الذي تم حفظ الملف فيه.
    """
    font_name = _register_arabic_font()
    wo = summary["work_order"]
    customer = summary["customer"]
    vehicle = summary["vehicle"]

    invoice_number = f"INV-{invoice['invoice_id']:06d}"
    issued_at = invoice["issued_at"] or datetime.utcnow().isoformat()

    doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=15 * mm, bottomMargin=15 * mm)
    elements = []

    style_title = ParagraphStyle("title", fontName=font_name, fontSize=16, leading=20, alignment=1)
    style_normal = ParagraphStyle("normal", fontName=font_name, fontSize=10, leading=14)
    style_normal_ar = ParagraphStyle("normal_ar", fontName=font_name, fontSize=10, leading=14, alignment=2)

    # --- الترويسة | Header ---
    if config.SERVICE_CENTER_LOGO_PATH:
        elements.append(Image(config.SERVICE_CENTER_LOGO_PATH, width=40 * mm, height=20 * mm))
        elements.append(Spacer(1, 4 * mm))

    elements.append(Paragraph(f"{config.SERVICE_CENTER_NAME_EN} | {_ar(config.SERVICE_CENTER_NAME_AR)}", style_title))
    elements.append(Spacer(1, 2 * mm))
    elements.append(Paragraph(f"{config.SERVICE_CENTER_ADDRESS_EN} | {_ar(config.SERVICE_CENTER_ADDRESS_AR)}", style_normal))
    elements.append(Paragraph(
        f"CR / {_ar('السجل التجاري')}: {config.SERVICE_CENTER_CR_NUMBER} &nbsp;&nbsp; "
        f"VAT No. / {_ar('الرقم الضريبي')}: {config.SERVICE_CENTER_VAT_NUMBER}",
        style_normal,
    ))
    elements.append(Spacer(1, 4 * mm))

    # --- بيانات الفاتورة | Invoice meta ---
    elements.append(Paragraph(
        f"Invoice No. / {_ar('رقم الفاتورة')}: <b>{invoice_number}</b> &nbsp;&nbsp; "
        f"Date / {_ar('التاريخ')}: {issued_at}",
        style_normal,
    ))
    elements.append(Spacer(1, 4 * mm))

    # --- بيانات العميل والمركبة | Customer & vehicle info ---
    customer_rows = [
        [Paragraph("Customer / " + _ar("العميل"), style_normal), Paragraph(customer["name"] if customer else "-", style_normal)],
        [Paragraph("Phone / " + _ar("الهاتف"), style_normal), Paragraph(customer["phone"] if customer else "-", style_normal)],
        [Paragraph("Vehicle / " + _ar("المركبة"), style_normal),
         Paragraph(f"{vehicle['make']} {vehicle['model']} {vehicle['year'] or ''}" if vehicle else "-", style_normal)],
        [Paragraph("Plate / " + _ar("رقم اللوحة"), style_normal), Paragraph(vehicle["plate_number"] if vehicle else "-", style_normal)],
        [Paragraph("Work Order / " + _ar("أمر العمل"), style_normal), Paragraph(f"#{wo['work_order_id']}", style_normal)],
    ]
    customer_table = Table(customer_rows, colWidths=[60 * mm, 120 * mm])
    customer_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(customer_table)
    elements.append(Spacer(1, 6 * mm))

    # --- بنود الفاتورة | Line items ---
    header_row = [
        Paragraph("Description / " + _ar("الوصف"), style_normal),
        Paragraph("Qty/Hrs / " + _ar("الكمية/الساعات"), style_normal),
        Paragraph("Unit Price (SAR) / " + _ar("سعر الوحدة"), style_normal),
        Paragraph("Amount (SAR) / " + _ar("الإجمالي"), style_normal),
    ]
    item_rows = [header_row]

    for item in summary["labor_items"]:
        amount = round(item["hours"] * item["rate"], 2)
        item_rows.append([
            Paragraph(item["description"], style_normal),
            Paragraph(f"{item['hours']}", style_normal),
            Paragraph(f"{item['rate']:.2f}", style_normal),
            Paragraph(f"{amount:.2f}", style_normal),
        ])

    for item in summary["part_items"]:
        amount = round(item["quantity"] * item["unit_price"], 2)
        name = f"{item['name_en'] or item['name_ar']} / {_ar(item['name_ar'])}"
        item_rows.append([
            Paragraph(name, style_normal),
            Paragraph(f"{item['quantity']}", style_normal),
            Paragraph(f"{item['unit_price']:.2f}", style_normal),
            Paragraph(f"{amount:.2f}", style_normal),
        ])

    items_table = Table(item_rows, colWidths=[80 * mm, 30 * mm, 35 * mm, 35 * mm])
    items_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 6 * mm))

    # --- الإجماليات وضريبة القيمة المضافة | Totals & VAT ---
    totals_rows = [
        [Paragraph("Subtotal / " + _ar("الإجمالي قبل الضريبة"), style_normal), Paragraph(f"{invoice['subtotal']:.2f} SAR", style_normal)],
        [Paragraph(f"VAT ({invoice['vat_rate'] * 100:.0f}%) / " + _ar("ضريبة القيمة المضافة"), style_normal), Paragraph(f"{invoice['vat_amount']:.2f} SAR", style_normal)],
        [Paragraph("<b>Total / " + _ar("الإجمالي شامل الضريبة") + "</b>", style_normal), Paragraph(f"<b>{invoice['total']:.2f} SAR</b>", style_normal)],
    ]
    totals_table = Table(totals_rows, colWidths=[140 * mm, 40 * mm])
    totals_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 6 * mm))

    # --- شروط الضمان | Warranty terms ---
    warranty_text_en = (
        "Warranty: Labor is guaranteed for 30 days from the delivery date. "
        "Parts are covered by the supplier's warranty as noted at the time of service. "
        "This warranty excludes damage caused by misuse, accidents, or unrelated faults."
    )
    warranty_text_ar = (
        "الضمان: يشمل العمل (الأجرة) ضماناً لمدة 30 يوماً من تاريخ التسليم. "
        "قطع الغيار مشمولة بضمان المورّد كما هو موضّح وقت الخدمة. "
        "لا يشمل هذا الضمان أي ضرر ناتج عن سوء الاستخدام أو حادث أو أعطال غير مرتبطة."
    )
    elements.append(Paragraph(warranty_text_en, style_normal))
    elements.append(Spacer(1, 2 * mm))
    elements.append(Paragraph(_ar(warranty_text_ar), style_normal_ar))
    elements.append(Spacer(1, 6 * mm))

    # --- رمز QR (فاتورة ضريبية مبسّطة) | Simplified tax invoice QR ---
    qr_bytes = _build_zatca_qr(
        seller_name=config.SERVICE_CENTER_NAME_EN,
        vat_number=config.SERVICE_CENTER_VAT_NUMBER,
        timestamp=issued_at,
        total=invoice["total"],
        vat_amount=invoice["vat_amount"],
    )
    qr_image = Image(io.BytesIO(qr_bytes), width=30 * mm, height=30 * mm)
    elements.append(qr_image)
    elements.append(Paragraph("Scan to verify this simplified tax invoice / " + _ar("مسح الرمز للتحقق من الفاتورة الضريبية المبسّطة"), style_normal))

    doc.build(elements)
    return output_path
