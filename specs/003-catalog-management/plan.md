# Implementation Plan: 003-catalog-management

**Branch**: `003-catalog-management` | **Date**: 2026-07-11 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-catalog-management/spec.md`

## Summary
افزودن CRUD کامل روی جدول `products` موجود (بدون تغییر schema) از طریق پنج
endpoint REST. همه‌چیز کاملاً دترمینیستیک است — هیچ LLM دخالت ندارد. تصمیم
«بدون auth» در MVP در ADR-0003 به‌عنوان ریسک شناخته‌شده مستند می‌شود. هر تغییر
قیمت در server log ثبت می‌شود (AC9). فیچر 001 (`POST /price`) دست‌نخورده
می‌ماند؛ این لایه‌ای جدا روی همان جدول است.

## Technical Context

**Language/Version**: Python 3.11+ (محیط فعلی: 3.12.8)
**Primary Dependencies**: FastAPI، SQLAlchemy (هر دو از فیچر 001 — بدون وابستگی تازه)
**Storage**: بدون تغییر (PostgreSQL/SQLite از فیچر 001 — همان جدول `products`)
**Testing**: pytest + httpx (TestClient) — الگوی موجود `tests/api/test_price_endpoint.py`
**Project Type**: web-service (افزودن route به API موجود)
**Constraints**: قانون ۳۰۰ خط هر فایل؛ mypy --strict صفر؛ ruff صفر.

## Constitution Check
- ✅ قانون ۳۰۰ خط: هر فایل تحت کنترل (طراحی زیر).
- ✅ Type checking: mypy --strict.
- ✅ no-secret: این فیچر رازی ندارد (بدون auth، بدون LLM).
- ✅ زبان سه‌محوری: کد انگلیسی، مستندات فارسی، `name_fa` فارسی.
- ✅ Decision دست‌نخورده: این لایه روی `products` است، نه روی لایهٔ Decision.
- ✅ Migration: **نیازی نیست** (schema تغییر نمی‌کند — جدول موجود استفاده می‌شود).
- ✅ Spec Drift: چون این فیچر روی همان جدول `products` که فیچر 001 آن را seeded
  می‌کند عمل می‌کند ولی **هیچ فایل فیچر 001 را تغییر نمی‌دهد**، یادداشت drift
  لازم نیست. ولی بعد از implement، `tests/test_seed.py` باید دوباره اجرا شود تا
  idempotency seed در حضور CRUD تأیید شود (AC5).

## تصمیم پیاده‌سازی (نکتهٔ باز از Clarify)
**رفتار `unit_price` با بیش از دو رقم اعشار (مثلاً `150000.999`):**
- **رد شود (HTTP 422).** دلیل: ستون `Numeric(12, 2)` است؛ گرد کردن خودکار
  داده‌ای را که اپراتور وارد کرده به‌صورت خام تغییر می‌داد (یک فعل مخفی نامطلوب).
  رد صریح، رفتار را شفاف و قابل پیش‌بینی می‌کند. اپراتور باید خودش گرد کند.
- پیاده‌سازی: اعتبارسنجی در لایهٔ schema (Pydantic) قبل از رسیدن به DB.
  اگر به DB می‌رسد، SQLAlchemy/SQLite خطای rounding می‌داد که ۵۰۰ تولید
  می‌کرد — ما جلوتر از آن در ۴۲۲ رد می‌کنیم (Fail Fast).

## Project Structure (افزودنی روی فیچر 001)

```text
app/
├── catalog/                       # لایهٔ جدید — CRUD روی جدول products موجود
│   ├── __init__.py
│   ├── service.py                 # منطق CRUD (دترمینیستیک، نازک) + audit log
│   └── schemas.py                 # Pydantic: ProductCreate, ProductUpdate, ProductOut
│
├── api/
│   ├── routes.py                  # دست‌نخورده (POST /price همان‌طور می‌ماند)
│   └── catalog_routes.py          # پنج endpoint جدید (ثبت در main.py)
│
└── db/
    └── models.py                  # دست‌نخورده (Product موجود — بدون schema change)

docs/
└── decisions/
    └── ADR-0003-no-auth-mvp-risk.md  # تصمیم «بدون auth» به‌عنوان ریسک شناخته‌شده

tests/
└── api/
    └── test_catalog_endpoints.py  # همهٔ پنج عملیات + خطاهای 404/409/422 + audit
```

**Structure Decision:** لایهٔ catalog یک پوشهٔ جدا (`app/catalog/`) است — نه داخل
`app/api/`. دلیل: منطق (service) و قرارداد سیم (schemas) باید از HTTP routing جدا
باشند (همان الگوی فیچر 001 که `decision/service.py` و `api/routes.py` را جدا
نگه داشت). `catalog_routes.py` نازک است — فقط dispatch به `catalog/service.py`.

**چرا `catalog_routes.py` جدا از `routes.py`؟** دو دلیل:
۱. قانون ۳۰۰ خط: اضافه‌کردن پنج endpoint به `routes.py` موجود آن را به سقف
   نزدیک می‌کرد؛ تفکیک از همان ابتدا از این مشکل جلوگیری می‌کند.
۲. جمع‌بندی منطقی: `routes.py` متعلق به سفر مشتریِ قیمت‌گذاری است؛
   `catalog_routes.py` متعلق به عملیات اپراتور. دو مخاطب متفاوت.

## Data Flow

```
POST   /products          → [catalog/service.py:create]    → ProductOut (201)
GET    /products          → [catalog/service.py:list_all]  → [ProductOut] (200)
GET    /products/{id}     → [catalog/service.py:get_one]   → ProductOut (200 | 404)
PUT    /products/{id}     → [catalog/service.py:update]    → ProductOut (200 | 404 | 422)
                             └─→ audit log: old_price, new_price, timestamp
DELETE /products/{id}     → [catalog/service.py:delete]    → 204 (| 404)
```

هر endpoint ابتدا ورودی را در Pydantic اعتبارسنجی می‌کند (Category 1: price ≥ 0،
name_fa/id غیرخالی، ≤ ۲ رقم اعشار). سپس service با Session کار می‌کند و خطاهای
دیتابیس (IntegrityError برای id تکراری، KeyError مفهومی برای id ناموجود) را به
HTTP status مناسب نگاشت می‌کند.

## اعتبارسنجی Category 1 (در schema)
- `unit_price ≥ 0` — رد صریح (422)، نه silently صفر.
- `unit_price` با ≤ ۲ رقم اعشار — رد صریح (422) (تصمیم بالا).
- `name_fa` غیرخالی (حداقل یک کاراکتر non-whitespace).
- `id` غیرخالی و منطبق با الگوی slug (حروف انگلیسی، عدد، خط‌تیره).

## Audit Log (AC9)
در `catalog/service.py:update`، فقط وقتی `unit_price` واقعاً تغییر کند، یک
`logger.info` با ساختار ثابت صادر می‌شود:

```
unit_price_changed product_id=<id> old=<old> new=<new> at=<iso8601 utc>
```

این در server log است (نه جدول DB — خارج از scope). تست آن: با
`caplog` fixture pytest بررسی می‌شود که بعد از یک PUT با تغییر قیمت، لاگ
دقیق تولید شده، و بعد از PUT بدون تغییر قیمت، لاگ تولید **نشده**.

## تست‌ها
- **create:** محصول جدید (201)؛ id تکراری (409)؛ قیمت منفی (422)؛
  بیش از دو رقم اعشار (422)؛ name خالی (422).
- **list / get_one:** لیست کامل (200)؛ یک محصول (200)؛ id ناموجود (404).
- **update:** ویرایش موفق (200)؛ id ناموجود (404)؛ id در body ≠ path (422)؛
  قیمت منفی (422)؛ audit log تولید شد (caplog)؛ audit log **نشده** وقتی قیمت
  ثابت ماند.
- **delete:** حذف موفق (204)؛ id ناموجود (404).
- **seed idempotency (AC5):** بعد از CRUD، `seed_database()` دوباره اجرا شود
  → محصولات موجود skip، ۰ درج اضافه.

## Complexity Tracking
(خالی — هیچ تخطی از constitution لازم نیست. همهٔ قوانین رعایت می‌شوند.)
