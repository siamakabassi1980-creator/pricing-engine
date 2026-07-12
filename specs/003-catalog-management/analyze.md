# Analyze Report — 003-catalog-management

> خروجی فاز `/speckit.analyze`: بررسی هم‌خوانی spec/plan/tasks با constitution.

## نتیجه: ✅ هم‌خوان (پس از چک‌های ویژه)

## ردیابی معیارهای پذیرش (AC → Task)
| AC | شرح | تسک پوشش‌دهنده | وضعیت |
|---|---|---|---|
| AC1 | پنج عملیات CRUD | T1.1, T2.1 | ✅ |
| AC2 | Category 1 hard (price≥0، name/id غیرخالی) | T0.2, T1.1 | ✅ |
| AC3 | خطای استاندارد REST (409/404/422) | T1.1, T2.1 | ✅ |
| AC4 | کاملاً دترمینیستیک، بدون LLM | T1.1 (ذاتی) | ✅ |
| AC5 | seed همچنان idempotent | T3.1 | ✅ |
| AC6 | تست‌پذیر با SQLite in-memory | T2.2, T3.1 | ✅ |
| AC7 | slug انگلیسی + name_fa فارسی | T0.2 | ✅ |
| AC8 | مستندسازی قرارداد API | T3.2 (data-model.md) | ✅ |
| AC9 | audit log تغییر قیمت | T1.1, T2.2 (caplog) | ✅ |
| AC10 | ADR-0003 برای «بدون auth» | T0.1 | ✅ |

همهٔ ACها دقیقاً یک تسک پوشش‌دهنده دارند — هیچ AC بی‌تسک و هیچ تسک بی‌هدف.

## چک‌های ویژه (دور بازبینی این فیچر)

### چک ۱ — تداخل با فیچر 001 (POST /price و main.py)
**سؤال:** آیا افزودن CRUD روی `products` به فیچر 001 آسیب می‌زند؟

**بررسی:** تا حدی — دو لایه روی همان جدول، ولی یک فایل فیچر 001 واقعاً لمس می‌شود:
- `routes.py::price_endpoint` (فیچر 001): **فقط می‌خواند** (`SELECT products`).
  این فایل دست‌نخورده می‌ماند.
- `main.py` (فیچر 001، T4.1): T2.1 این فایل را برای `app.include_router(catalog_router)`
  **تغییر می‌دهد**. این یک Spec Drift است → طبق قانون constitution، یک یادداشت
  drift به `specs/001-pricing/status.md` اضافه می‌شود (T2.1). بعد از تغییر، کل
  `tests/api/test_price_endpoint.py` دوباره اجرا می‌شود تا مطمئن شویم چیزی نشکسته.

**نگرانی mid-request delete:** اگر یک محصول mid-request حذف شود، risk ناچیز است چون
`POST /price` در یک transaction کوتاه همه را می‌خواند.

### چک ۱′ — تعامل DELETE با seed_database() (RESTORE-ON-RESEED)
**سؤال:** اگر یک محصول seed‌شده با DELETE حذف شود و بعداً `seed_database()` دوباره
اجرا شود (مثلاً هنگام restart)، چه می‌شود؟

**بررسی کد واقعی `seed.py`:** تابع برای هر محصول اول `SELECT` می‌کند، اگر موجود
بود skip، اگر نه **insert**. پس پاسخ قطعی: **محصول حذف‌شده دوباره ساخته می‌شود.**

این یک **رفتار شناخته‌شده** است، نه باگ. دو پیامد:
۱. این رفتار صریح در **ADR-0003** به‌عنوان محدودیت مستند می‌شود (نه ADR جدا —
   فقط یک پیامد اضافی از همان تصمیم seed-as-bootstrap).
۲. یک **تست صریح** در T3.1 اضافه می‌شود: delete یک محصول seed‌شده → اجرای
   `seed_database()` → محصول دوباره موجود است. این، رفتار واقعی را ثابت می‌کند.

**استلزام محصول:** اپراتورها باید بدانند که DELETE روی محصولات seed‌شده بعد از
restart دوباره ظاهر می‌شوند. این در `data-model.md` (T3.2) یادداشت می‌شود.

### چک ۲ — قانون «Decision هرگز LLM»
**تأیید:** این فیچر اصلاً لایهٔ Decision را لمس نمی‌کند. `app/catalog/` جدا از
`app/decision/` است. هیچ نگرانی نقض قانون سه‌لایه.

### چک ۳ — تصمیم >۲ رقم اعشار (نکتهٔ باز از Clarify)
**تأیید:** رد صریح (422) در schema، قبل از DB. دلیل در plan ثبت شد:
گرد کردن خودکار = فعل مخفی نامطلوب (دادهٔ اپراتور خام تغییر می‌کرد). تست آن در
T0.2 (schema unit) و T2.2 (integration).

### چک ۴ — لایهٔ audit log و قانون no-secret
**تأیید:** audit log در server log است (`logging`، نه DB) — پس نیازی به ذخیرهٔ
Pll ندارد و قانون no-secret نقض نمی‌شود. timestamp در UTC با ISO 8601.

**تذکر دقیق دربارهٔ ماهیت audit (مطابق اصلاح AC9):** برخلاف مسیر LLM که با
invariant ساختاری محافظت می‌شود (نقض = تست fail)، audit log یک **audit trail
پس‌رویدادی** است — هیچ تغییر قیمتی را رد یا متوقف نمی‌کند. هدف ردیابی‌پذیری
است، نه جلوگیری. این تفاوت در AC9 تصریح شد تا کسی audit را به‌اشتباه معادل
مکانیزم پیشگیرانه LLM نداند.

## انطباق با Constitution
| قانون | وضعیت | توضیح |
|---|---|---|
| جداسازی سه‌لایه | ✅ | لایهٔ catalog جدا از decision/perception/generation |
| Decision هرگز LLM | ✅ | این فیچر اصلاً decision را لمس نمی‌کند |
| حد ۳۰۰ خط | ✅ | service.py + catalog_routes.py جدا نگه داشته شدند |
| Type checking | ✅ | mypy --strict |
| Migration + rollback | ✅ N/A | schema تغییر نمی‌کند (جدول موجود) |
| Fail Fast | ✅ | >۲ رقم اعشار قبل از DB رد می‌شود |
| no-secret | ✅ | این فیچر رازی ندارد (بدون auth، بدون LLM) |
| زبان سه‌محوری | ✅ | slug/id انگلیسی، name_fa فارسی، مستندات فارسی |
| Spec Drift | ✅ | `main.py` (فیچر 001) در T2.1 برای `include_router` تغییر می‌کند → یادداشت drift به `specs/001-pricing/status.md` اضافه می‌شود + `tests/api/test_price_endpoint.py` دوباره اجرا می‌شود (چک ۱) |
| PBT | ✅ N/A | این دامنه CRUD است — invariant ریاضی ندارد؛ unit + integration کافی |

### یادآوری دربارهٔ PBT
طبق روش‌شناسی فیچر 002، PBT فقط جایی که invariant ریاضی وجود دارد الزامی است.
CRUD دترمینیستیک ساده است — نه مناسب PBT، نه نامناسب؛ فقط بی‌ربط (دقیقاً همان
طبقه‌بندی که برای catalog در ROADMAP داده شد). پس **هیچ ADR لازم نیست** چون
هیچ قانون constitution اینجا صدق نمی‌کند — برخلاف فیچر 002 که قانون ۸۰٪+PBT
صراحتاً صدق می‌کرد و باید معاف می‌شد.

## یادآوری‌های متدولوژیکی برای Implement
۱. T0.1 (ADR-0003) اول نوشته شود — ریسک شناخته‌شده قبل از کد مستند شود.
۲. T0.2 (schema) قبل از service — اعتبارسنجی Category ۱ در مرز ورودی.
۳. تست audit log با `caplog` pytest fixture، نه assertion روی فایل لاگ.
۴. بعد از هر تسک، lint روی **کل پروژه** (نه فقط فایل همان تسک) — طبق constitution.
۵. T2.1: `main.py` (فایل فیچر 001) را برای `include_router` تغییر می‌دهد → یادداشت
   drift به `specs/001-pricing/status.md` + اجرای مجدد `tests/api/test_price_endpoint.py`.
۶. T3.1: `tests/test_seed.py` دوباره اجرا شود تا idempotency در حضور CRUD سالم،
   + تست صریح restore-on-reseed (چک ۱′).
