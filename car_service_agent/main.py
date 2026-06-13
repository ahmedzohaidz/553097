#!/usr/bin/env python3
"""
الوكيل الرئيسي لمركز تشخيص وصيانة السيارات
Main agent entry point for the Car Diagnostic & Service Center

يهيئ قاعدة البيانات عند أول تشغيل، ويعرض قائمة تفاعلية للوصول إلى
المهارات الثماني (Agent Skills) الموجودة في مجلد skills/.
"""

from __future__ import annotations

from tabulate import tabulate

from database.db import calculate_vat, get_connection, init_db
from skills.customer_followup import scripts as followup_skill
from skills.diagnostics import scripts as diagnostics_skill
from skills.inventory import scripts as inventory_skill
from skills.pricing_invoicing import scripts as invoicing_skill
from skills.reports import scripts as reports_skill
from skills.technicians import scripts as technicians_skill
from skills.vehicle_intake import scripts as intake_skill
from skills.work_orders import scripts as work_orders_skill

MENU = """
================================================
  وكيل مركز تشخيص وصيانة السيارات
  Car Service Center Agent
================================================
 1) استقبال سيارة جديدة      | New vehicle intake
 2) تسجيل تشخيص               | Add diagnostic
 3) إدارة أمر عمل              | Manage work order
 4) إصدار فاتورة                | Issue invoice
 5) قطع الغيار والمخزون          | Parts & inventory
 6) إدارة الفنيين                | Manage technicians
 7) متابعة العميل (واتساب)        | Customer follow-up
 8) التقارير والأداء              | Reports
 0) خروج                          | Exit
================================================
"""


def prompt(text: str) -> str:
    return input(text).strip()


def action_intake(conn) -> None:
    print("\n-- استقبال سيارة جديدة | New vehicle intake --")
    name = prompt("اسم العميل | Customer name: ")
    phone = prompt("رقم الهاتف (+966...) | Phone: ")
    lang = prompt("اللغة المفضلة (ar/en) | Preferred language [ar]: ") or "ar"
    customer_id = intake_skill.find_or_create_customer(conn, name, phone, preferred_lang=lang)

    plate = prompt("رقم اللوحة | Plate number: ")
    make = prompt("الشركة المصنعة | Make: ")
    model = prompt("الموديل | Model: ")
    year_input = prompt("سنة الصنع | Year (optional): ")
    odometer_input = prompt("قراءة العداد بالكم | Odometer km [0]: ") or "0"
    vehicle_id = intake_skill.find_or_create_vehicle(
        conn,
        customer_id,
        plate,
        make,
        model,
        year=int(year_input) if year_input else None,
        odometer_km=int(odometer_input),
    )

    complaint = prompt("سبب الزيارة / الشكوى | Complaint: ")
    work_order_id = intake_skill.open_work_order(conn, vehicle_id, customer_id, complaint)
    print(f"\nتم فتح أمر عمل رقم {work_order_id} | Work order #{work_order_id} created.")


def action_diagnostics(conn) -> None:
    print("\n-- تسجيل تشخيص | Add diagnostic --")
    work_order_id = int(prompt("رقم أمر العمل | Work order ID: "))
    obd_codes = prompt("أكواد OBD (اختياري) | OBD codes (optional): ") or None
    findings = prompt("نتائج الفحص | Findings: ")
    recommendation = prompt("التوصية | Recommendation: ") or None
    severity = prompt("الخطورة (low/medium/high/critical) [medium]: ") or "medium"

    diagnostics_skill.add_diagnostic(
        conn, work_order_id, findings, obd_codes=obd_codes,
        recommendation=recommendation, severity=severity,
    )

    new_status = prompt("الحالة الجديدة لأمر العمل (Enter لتجاهل) | New status (Enter to skip): ")
    if new_status:
        diagnostics_skill.update_work_order_status(conn, work_order_id, new_status)
    print("تم تسجيل التشخيص بنجاح | Diagnostic recorded.")


def action_work_order(conn) -> None:
    print("\n-- إدارة أمر العمل | Manage work order --")
    open_orders = work_orders_skill.get_open_work_orders(conn)
    if open_orders:
        rows = [[o["work_order_id"], o["status"], o["complaint"]] for o in open_orders]
        print(tabulate(rows, headers=["ID", "Status", "Complaint"]))
    else:
        print("لا توجد أوامر عمل مفتوحة | No open work orders.")

    work_order_id = int(prompt("\nرقم أمر العمل | Work order ID: "))
    print("1) إضافة بند عمل | Add labor item")
    print("2) إضافة قطعة غيار | Add part item")
    print("3) تغيير الحالة | Change status")
    print("4) عرض الملخص | Show summary")
    choice = prompt("اختر | Choose: ")

    if choice == "1":
        description = prompt("الوصف | Description: ")
        hours = float(prompt("الساعات | Hours: "))
        rate = float(prompt("سعر الساعة | Rate (SAR): "))
        work_orders_skill.add_labor_item(conn, work_order_id, description, hours, rate)
    elif choice == "2":
        sku = prompt("رمز القطعة SKU: ")
        part = inventory_skill.get_part_by_sku(conn, sku)
        if not part:
            print("القطعة غير موجودة | Part not found.")
            return
        quantity = int(prompt("الكمية | Quantity: "))
        inventory_skill.consume_stock(conn, part["part_id"], quantity)
        work_orders_skill.add_part_item(conn, work_order_id, part["part_id"], quantity, part["unit_price"])
    elif choice == "3":
        status = prompt("الحالة الجديدة | New status: ")
        work_orders_skill.set_status(conn, work_order_id, status)
        if status == "delivered":
            work_orders_skill.mark_delivered(conn, work_order_id)
    elif choice == "4":
        summary = work_orders_skill.get_work_order_summary(conn, work_order_id)
        print(f"\nالإجمالي قبل الضريبة | Subtotal: {summary['subtotal']:.2f} SAR")
        vat_amount, total = calculate_vat(summary["subtotal"])
        print(f"ضريبة القيمة المضافة (15%) | VAT: {vat_amount:.2f} SAR")
        print(f"الإجمالي شامل الضريبة | Total: {total:.2f} SAR")


def action_invoice(conn) -> None:
    print("\n-- إصدار فاتورة | Issue invoice --")
    work_order_id = int(prompt("رقم أمر العمل | Work order ID: "))
    invoice_id = invoicing_skill.issue_invoice(conn, work_order_id)
    invoice = invoicing_skill.get_invoice(conn, work_order_id)
    summary = work_orders_skill.get_work_order_summary(conn, work_order_id)
    lang = (summary["customer"] or {}).get("preferred_lang", "ar")
    print(f"\nتم إصدار الفاتورة رقم {invoice_id} | Invoice #{invoice_id} issued.\n")
    print(invoicing_skill.format_invoice_text(invoice, summary, lang=lang))

    if prompt("\nتم السداد؟ (y/n) | Paid? (y/n): ").lower() == "y":
        invoicing_skill.mark_invoice_paid(conn, invoice_id)
        print("تم تسجيل السداد | Payment recorded.")


def action_inventory(conn) -> None:
    print("\n-- قطع الغيار والمخزون | Parts & inventory --")
    print("1) إضافة قطعة جديدة | Add new part")
    print("2) استلام شحنة | Receive stock")
    print("3) عرض القطع منخفضة المخزون | Low stock report")
    choice = prompt("اختر | Choose: ")

    if choice == "1":
        sku = prompt("رمز القطعة SKU: ")
        name_ar = prompt("الاسم بالعربية | Arabic name: ")
        name_en = prompt("الاسم بالإنجليزية | English name (optional): ") or None
        unit_cost = float(prompt("تكلفة الشراء (بدون ضريبة) | Unit cost: "))
        unit_price = float(prompt("سعر البيع (بدون ضريبة) | Unit price: "))
        quantity = int(prompt("الكمية الحالية | Quantity on hand [0]: ") or "0")
        reorder = int(prompt("حد إعادة الطلب | Reorder level [5]: ") or "5")
        inventory_skill.add_part(conn, sku, name_ar, name_en, unit_cost, unit_price, quantity, reorder)
    elif choice == "2":
        sku = prompt("رمز القطعة SKU: ")
        part = inventory_skill.get_part_by_sku(conn, sku)
        if not part:
            print("القطعة غير موجودة | Part not found.")
            return
        quantity = int(prompt("الكمية المستلمة | Quantity received: "))
        inventory_skill.receive_stock(conn, part["part_id"], quantity)
    elif choice == "3":
        rows = inventory_skill.get_low_stock_parts(conn)
        if rows:
            table = [[r["sku"], r["name_ar"], r["quantity_on_hand"], r["reorder_level"]] for r in rows]
            print(tabulate(table, headers=["SKU", "Name", "On hand", "Reorder level"]))
        else:
            print("لا توجد قطع منخفضة المخزون | No low-stock parts.")


def action_technicians(conn) -> None:
    print("\n-- إدارة الفنيين | Manage technicians --")
    print("1) إضافة فني | Add technician")
    print("2) عرض عبء العمل | Show workload")
    choice = prompt("اختر | Choose: ")

    if choice == "1":
        name = prompt("الاسم | Name: ")
        specialty = prompt("التخصص | Specialty: ") or None
        phone = prompt("الهاتف | Phone (optional): ") or None
        hourly_rate = float(prompt("التكلفة بالساعة | Hourly cost [0]: ") or "0")
        technicians_skill.add_technician(conn, name, specialty, phone, hourly_rate)
    elif choice == "2":
        rows = technicians_skill.get_technician_workload(conn)
        table = [[r["technician_id"], r["name"], r["specialty"], r["open_work_orders"]] for r in rows]
        print(tabulate(table, headers=["ID", "Name", "Specialty", "Open orders"]))


def action_followup(conn) -> None:
    print("\n-- متابعة العميل | Customer follow-up --")
    work_order_id = int(prompt("رقم أمر العمل | Work order ID: "))
    summary = work_orders_skill.get_work_order_summary(conn, work_order_id)
    customer = summary["customer"]
    lang = customer["preferred_lang"]
    status = summary["work_order"]["status"]

    message = followup_skill.build_status_message(status, lang=lang)
    if not message:
        message = prompt("نص الرسالة | Message text: ")

    message_type = prompt("نوع الرسالة (status_update/approval_request/ready_for_pickup/feedback_request/reminder) [status_update]: ") or "status_update"
    followup_id = followup_skill.queue_followup(conn, customer["customer_id"], message_type, message, work_order_id=work_order_id)
    print(f"\nتمت إضافة رسالة المتابعة رقم {followup_id} | Follow-up #{followup_id} queued.")
    print(f"النص | Text: {message}")

    if prompt("\nإرسال الآن عبر واتساب؟ (y/n) | Send now via WhatsApp? (y/n): ").lower() == "y":
        try:
            sent = followup_skill.send_whatsapp_message(customer["phone"], message)
            followup_skill.mark_followup_status(conn, followup_id, "sent" if sent else "failed")
            print("تم الإرسال | Sent." if sent else "فشل الإرسال | Send failed.")
        except RuntimeError as exc:
            print(f"تعذر الإرسال | Could not send: {exc}")


def action_reports(conn) -> None:
    print("\n-- التقارير والأداء | Reports --")
    start_date = prompt("من تاريخ (YYYY-MM-DD، اختياري) | Start date (optional): ") or None
    end_date = prompt("إلى تاريخ (YYYY-MM-DD، اختياري) | End date (optional): ") or None

    revenue = reports_skill.revenue_summary(conn, start_date, end_date)
    print("\nملخص الإيرادات | Revenue summary:")
    for key, value in revenue.items():
        print(f"  {key}: {value}")

    print("\nحالة أوامر العمل | Work order status breakdown:")
    for status, count in reports_skill.work_order_status_breakdown(conn).items():
        print(f"  {status}: {count}")

    print("\nالقطع منخفضة المخزون | Low stock parts:")
    low_stock = reports_skill.low_stock_report(conn)
    if low_stock:
        table = [[r["sku"], r["name_ar"], r["quantity_on_hand"], r["reorder_level"]] for r in low_stock]
        print(tabulate(table, headers=["SKU", "Name", "On hand", "Reorder level"]))
    else:
        print("  لا توجد | None")

    satisfaction = reports_skill.customer_satisfaction(conn, start_date, end_date)
    print(f"\nرضا العملاء | Customer satisfaction: {satisfaction}")


ACTIONS = {
    "1": action_intake,
    "2": action_diagnostics,
    "3": action_work_order,
    "4": action_invoice,
    "5": action_inventory,
    "6": action_technicians,
    "7": action_followup,
    "8": action_reports,
}


def main() -> None:
    init_db()
    conn = get_connection()
    try:
        while True:
            print(MENU)
            choice = prompt("اختر رقم العملية | Select option: ")
            if choice == "0":
                print("إلى اللقاء | Goodbye!")
                break

            action = ACTIONS.get(choice)
            if not action:
                print("اختيار غير صالح | Invalid option.")
                continue

            try:
                action(conn)
            except (ValueError, RuntimeError) as exc:
                print(f"خطأ | Error: {exc}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
