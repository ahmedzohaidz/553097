---
name: customer_followup
description: متابعة العميل عبر واتساب - إرسال تحديثات الحالة، طلبات الموافقة، إشعار جهوزية السيارة، وطلب التقييم بعد التسليم. Use when a customer needs a status update, approval request, pickup notification, or post-service feedback request via WhatsApp.
---

# متابعة العميل | Customer Follow-up (WhatsApp)

## الهدف | Purpose
إبقاء العميل على اطلاع بحالة سيارته طوال دورة الخدمة عبر واتساب، وطلب
موافقته على أعمال إضافية، وإشعاره عند جهوزية السيارة، وجمع تقييمه بعد
التسليم.

Keep the customer informed throughout the service cycle via WhatsApp,
request approval for additional work, notify them when the vehicle is
ready, and collect feedback after delivery.

## أنواع الرسائل | Message types (`message_type`)
| القيمة | الاستخدام |
|---|---|
| `status_update` | تحديث عام عن حالة أمر العمل (تم الاستلام، بدء التشخيص...) |
| `approval_request` | طلب موافقة العميل على أعمال/تكاليف إضافية بعد التشخيص |
| `ready_for_pickup` | إشعار بأن السيارة جاهزة للاستلام مع تفاصيل الفاتورة |
| `feedback_request` | طلب تقييم الخدمة بعد التسليم |
| `reminder` | تذكير بموعد صيانة دورية قادم |

## متى تُستخدم | When to use
- عند فتح أمر عمل جديد (`vehicle_intake`) → `status_update`.
- عند انتقال أمر العمل إلى `awaiting_approval` (`diagnostics`) →
  `approval_request`.
- عند إصدار الفاتورة (`pricing_invoicing`) أو اكتمال العمل →
  `ready_for_pickup`.
- بعد `mark_delivered` (`work_orders`) → `feedback_request` (يمكن
  جدولتها بعد ساعات قليلة).
- لمواعيد الصيانة الدورية (كل 5,000-10,000 كم أو حسب توصية الصانع) →
  `reminder`.

## سير العمل | Workflow
1. تأكد من `whatsapp_opt_in = 1` للعميل قبل الإرسال.
2. اختر اللغة من `customers.preferred_lang` (`ar` أو `en`) لصياغة
   الرسالة.
3. سجّل الرسالة في جدول `followups` (الحالة الابتدائية `queued`).
4. استخدم `send_whatsapp_message` لإرسال الرسالة فعلياً عبر Meta Cloud
   API، ثم حدّث حالة السجل إلى `sent` أو `failed`.
5. عند استقبال رد العميل (عبر webhook خارجي)، حدّث الحالة إلى `replied`
   وسجّل التقييم في `customer_feedback` إن كان رداً على
   `feedback_request`.

## الأدوات المتاحة | Available tools
الوظائف في `scripts.py`:

- `queue_followup(conn, customer_id, message_type, message_body, work_order_id=None, channel="whatsapp")`
- `send_whatsapp_message(phone, message)` — **stub**: يحتاج لربط فعلي
  بـ Meta WhatsApp Cloud API (`config.WHATSAPP_API_TOKEN` و
  `WHATSAPP_PHONE_NUMBER_ID`). راجع التعليقات داخل الدالة.
- `mark_followup_status(conn, followup_id, status)`
- `record_feedback(conn, work_order_id, customer_id, rating, comments=None)`
- `build_status_message(status, lang="ar")` — يولّد نص رسالة عربي/إنجليزي
  مناسب لحالة أمر العمل.

## ملاحظات للسوق السعودي | Saudi market notes
- استخدم أرقام هاتف بصيغة دولية (`+966...`) مع Meta Cloud API.
- التزم بسياسات WhatsApp Business بشأن "نوافذ الرسائل" (24 ساعة) -
  الرسائل الترويجية بعد ذلك تتطلب قوالب معتمدة مسبقاً (Message
  Templates).
- اجعل الرد التلقائي ثنائي اللغة عند عدم معرفة لغة العميل المفضّلة.
