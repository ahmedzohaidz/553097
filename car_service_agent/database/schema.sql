-- =====================================================================
-- قاعدة بيانات مركز تشخيص وصيانة السيارات
-- Car Diagnostic & Service Center Database Schema
-- SQLite
-- =====================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- 1) العملاء | Customers
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    customer_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    phone           TEXT NOT NULL UNIQUE,      -- E.164, e.g. +9665XXXXXXXX
    whatsapp_opt_in INTEGER NOT NULL DEFAULT 1, -- 1 = موافق على رسائل واتساب
    preferred_lang  TEXT NOT NULL DEFAULT 'ar', -- 'ar' or 'en'
    city            TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- 2) المركبات | Vehicles
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    plate_number    TEXT NOT NULL,             -- رقم اللوحة (سعودي)
    make            TEXT NOT NULL,             -- الشركة المصنعة
    model           TEXT NOT NULL,             -- الموديل
    year            INTEGER,
    vin             TEXT,                      -- رقم الهيكل
    odometer_km     INTEGER DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- 3) أوامر العمل | Work Orders
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS work_orders (
    work_order_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id      INTEGER NOT NULL REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
    customer_id     INTEGER NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    status          TEXT NOT NULL DEFAULT 'received'
                    CHECK (status IN ('received', 'diagnosing', 'awaiting_approval',
                                       'in_progress', 'completed', 'delivered', 'cancelled')),
    complaint       TEXT,                      -- شكوى العميل / سبب الزيارة
    assigned_technician_id INTEGER REFERENCES technicians(technician_id),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    promised_at     TEXT,                      -- موعد التسليم المتوقع
    delivered_at    TEXT
);

-- ---------------------------------------------------------------------
-- 4) التشخيص | Diagnostics
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS diagnostics (
    diagnostic_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    work_order_id   INTEGER NOT NULL REFERENCES work_orders(work_order_id) ON DELETE CASCADE,
    technician_id   INTEGER REFERENCES technicians(technician_id),
    obd_codes       TEXT,                      -- أكواد القراءة (مفصولة بفاصلة)
    findings        TEXT NOT NULL,             -- نتائج الفحص
    recommendation  TEXT,                      -- التوصية
    severity        TEXT DEFAULT 'medium'
                    CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- 5) الفنيون | Technicians
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS technicians (
    technician_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    specialty       TEXT,                      -- التخصص: كهرباء، ميكانيكا، تكييف...
    phone           TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1,
    hourly_rate     REAL NOT NULL DEFAULT 0,   -- معدل التكلفة بالساعة (داخلي)
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- 6) قطع الغيار والمخزون | Parts & Inventory
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS parts (
    part_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    sku             TEXT NOT NULL UNIQUE,      -- رمز القطعة
    name_ar         TEXT NOT NULL,
    name_en         TEXT,
    unit_cost       REAL NOT NULL DEFAULT 0,   -- تكلفة الشراء (بدون ضريبة)
    unit_price      REAL NOT NULL DEFAULT 0,   -- سعر البيع (بدون ضريبة)
    quantity_on_hand INTEGER NOT NULL DEFAULT 0,
    reorder_level   INTEGER NOT NULL DEFAULT 5, -- حد إعادة الطلب
    supplier        TEXT,
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- بنود قطع الغيار المستخدمة في أمر عمل
CREATE TABLE IF NOT EXISTS work_order_parts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    work_order_id   INTEGER NOT NULL REFERENCES work_orders(work_order_id) ON DELETE CASCADE,
    part_id         INTEGER NOT NULL REFERENCES parts(part_id),
    quantity        INTEGER NOT NULL DEFAULT 1,
    unit_price      REAL NOT NULL,             -- سعر البيع وقت الإصدار (بدون ضريبة)
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- بنود الأعمال/الخدمات (مثل ساعات عمل، فحص، إلخ) في أمر عمل
CREATE TABLE IF NOT EXISTS work_order_labor (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    work_order_id   INTEGER NOT NULL REFERENCES work_orders(work_order_id) ON DELETE CASCADE,
    technician_id   INTEGER REFERENCES technicians(technician_id),
    description     TEXT NOT NULL,             -- وصف الخدمة
    hours           REAL NOT NULL DEFAULT 0,
    rate            REAL NOT NULL DEFAULT 0,   -- سعر الساعة للعميل (بدون ضريبة)
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- 7) الفواتير | Invoices  (ضريبة القيمة المضافة 15%)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    work_order_id   INTEGER NOT NULL UNIQUE REFERENCES work_orders(work_order_id) ON DELETE CASCADE,
    subtotal        REAL NOT NULL DEFAULT 0,   -- الإجمالي قبل الضريبة
    vat_rate        REAL NOT NULL DEFAULT 0.15, -- نسبة ضريبة القيمة المضافة
    vat_amount      REAL NOT NULL DEFAULT 0,   -- قيمة الضريبة
    total           REAL NOT NULL DEFAULT 0,   -- الإجمالي شامل الضريبة
    status          TEXT NOT NULL DEFAULT 'unpaid'
                    CHECK (status IN ('unpaid', 'paid', 'cancelled')),
    issued_at       TEXT NOT NULL DEFAULT (datetime('now')),
    paid_at         TEXT
);

-- ---------------------------------------------------------------------
-- 8) متابعة العميل / واتساب | Customer Follow-up & WhatsApp Log
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS followups (
    followup_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    work_order_id   INTEGER REFERENCES work_orders(work_order_id),
    channel         TEXT NOT NULL DEFAULT 'whatsapp'
                    CHECK (channel IN ('whatsapp', 'sms', 'call', 'email')),
    message_type    TEXT NOT NULL
                    CHECK (message_type IN ('status_update', 'approval_request',
                                             'ready_for_pickup', 'feedback_request',
                                             'reminder')),
    message_body    TEXT,
    sent_at         TEXT NOT NULL DEFAULT (datetime('now')),
    status          TEXT NOT NULL DEFAULT 'queued'
                    CHECK (status IN ('queued', 'sent', 'failed', 'replied'))
);

-- تقييم رضا العملاء
CREATE TABLE IF NOT EXISTS customer_feedback (
    feedback_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    work_order_id   INTEGER NOT NULL REFERENCES work_orders(work_order_id) ON DELETE CASCADE,
    customer_id     INTEGER NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    rating          INTEGER CHECK (rating BETWEEN 1 AND 5),
    comments        TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- طلبات إعادة التوريد (تنبيهات المخزون اليومية)
-- Reorder requests (daily inventory alerts)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reorder_requests (
    reorder_request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'approved', 'rejected', 'received')),
    total_cost      REAL NOT NULL DEFAULT 0,   -- التكلفة الإجمالية المقترحة (بدون ضريبة)
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS reorder_request_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    reorder_request_id INTEGER NOT NULL REFERENCES reorder_requests(reorder_request_id) ON DELETE CASCADE,
    part_id         INTEGER NOT NULL REFERENCES parts(part_id),
    quantity        INTEGER NOT NULL,
    unit_cost       REAL NOT NULL,
    line_total      REAL NOT NULL
);

-- ---------------------------------------------------------------------
-- فهارس | Indexes
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_vehicles_customer        ON vehicles(customer_id);
CREATE INDEX IF NOT EXISTS idx_work_orders_vehicle      ON work_orders(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_work_orders_status       ON work_orders(status);
CREATE INDEX IF NOT EXISTS idx_diagnostics_work_order   ON diagnostics(work_order_id);
CREATE INDEX IF NOT EXISTS idx_wo_parts_work_order      ON work_order_parts(work_order_id);
CREATE INDEX IF NOT EXISTS idx_wo_labor_work_order      ON work_order_labor(work_order_id);
CREATE INDEX IF NOT EXISTS idx_followups_customer       ON followups(customer_id);
CREATE INDEX IF NOT EXISTS idx_reorder_items_request     ON reorder_request_items(reorder_request_id);
