# Tasks — 003-catalog-management

> هر تسک معیار «تست pass + صفر Linter + mypy صفر» را دارد. Fail Fast برقرار است.
> پس از هر تسک، lint روی کل پروژه (نه فقط فایل همان تسک) — طبق constitution.

## فاز ۰ — ADR + پایهٔ فنی

### T0.1 — ADR-0003 (چرا بدون auth در MVP)
- [x] `docs/decisions/ADR-0003-no-auth-mvp-risk.md` نوشته شود (با الگوی TEMPLATE.md).
- [x] Context، Decision، Consequences (ریسک شناخته‌شده)، و شرط رفع
      (چه وقتی auth باید برگردد: وقتی API به شبکهٔ خارج از trusted-zone برسد).
- [x] **محدودیت اضافی — restore-on-reseed:** چون `seed_database()` با `SELECT`
      چک می‌کند، حذف یک محصول seed‌شده با DELETE، بعد از restart/دوباره-seed
      دوباره ساخته می‌شود. این صریح مستند شود: DELETE یک محصول seed‌شده فقط
      تا next-reseed دوام دارد. (تست آن در T3.1.)
- [x] commit: `docs(catalog): ADR-0003 — no-auth as known risk in MVP`

### T0.2 — Pydantic schemas + اعتبارسنجی Category 1
- [x] `app/catalog/__init__.py` (خالی).
- [x] `app/catalog/schemas.py`: `ProductCreate`, `ProductUpdate`, `ProductOut`.
- [x] اعتبارسنجی در schema:
      - `unit_price ≥ 0` (422).
      - `unit_price` با ≤ ۲ رقم اعشار (422) — تصمیم plan.
      - `name_fa` غیرخالی.
      - `id` slug با pattern دقیق `^[a-z0-9]+(-[a-z0-9]+)*$` (حروف کوچک انگلیسی،
        عدد، خط‌تیره بین بخش‌ها؛ بدون خط‌تیره در ابتدا/انتها یا دوخط‌تیره پشت‌سرهم).
- [x] یادداشت یک‌خطی دربارهٔ race condition روی PUT هم‌زمان: «برای MVP نادیده
      گرفته می‌شود چون (الف) auth نیست و فرض single-operator از شبکهٔ داخلی است،
      (ب) last-write-wins در سطح DB (SQLite/PostgreSQL row lock) رفتار مشخصی دارد.
      اگر multi-operator لازم شد، optimistic locking (مثلاً version column) باید
      در فیچر جدا اضافه شود — schema change، نیاز به ADR.» این یادداشت در
      `schemas.py` به‌صورت کامنت فنی انگلیسی نوشته شود.
- [x] تست واحد روی schemas (هر خطای اعتبارسنجی، شامل slug نامعتبر).
- [x] Linter + mypy صفر.
- [x] commit: `feat(catalog): add Pydantic schemas with Category 1 validation`

## فاز ۱ — Service لایه (دترمینیستیک)

### T1.1 — CRUD service + audit log
- [x] `app/catalog/service.py`:
      - `create_product(session, data) -> Product` (IntegrityError → 409).
      - `list_products(session) -> list[Product]`.
      - `get_product(session, id) -> Product` (ناموجود → 404).
      - `update_product(session, id, data) -> Product` (ناموجود → 404؛
        audit log وقتی unit_price تغییر کرد).
      - `delete_product(session, id) -> None` (ناموجود → 404).
- [x] خطاهای مفهومی کلاس اختصاصی: `ProductNotFound`, `ProductAlreadyExists`.
- [x] audit log با `logging` (ساختار ثابت در plan).
- [x] تست واحد service با SQLite in-memory (هر عملیات + audit با caplog).
- [x] Linter + mypy صفر.
- [x] commit: `feat(catalog): add CRUD service with audit log (T1.1)`

## فاز ۲ — HTTP لایه

### T2.1 — catalog_routes.py + ثبت در main.py
- [x] `app/api/catalog_routes.py`: پنج endpoint نازک (dispatch به service).
      - POST `/products` → 201.
      - GET `/products` → 200.
      - GET `/products/{id}` → 200 | 404.
      - PUT `/products/{id}` → 200 | 404 | 422 (id body ≠ path).
      - DELETE `/products/{id}` → 204 | 404.
- [x] نگاشت خطای مفهومی → HTTP status (404، 409، 422).
- [x] ثبت router در `app/main.py` (`app.include_router(catalog_router)`).
- [x] **Spec Drift (طبق قانون constitution):** چون `main.py` فایل فیچر 001 است،
      یک یادداشت drift به `specs/001-pricing/status.md` اضافه شود که `main.py`
      در فیچر 003-T2.1 برای `include_router(catalog_router)` دوباره لمس شد.
- [x] **بازگشت تست:** کل `tests/api/test_price_endpoint.py` (هر ۶ تست) دوباره
      اجرا شود و pass شود — تا مطمئن شویم اضافه‌کردن router دوم به `create_app`
      چیزی را در مسیر قیمت‌گذاری نشکسته.
- [x] Linter + mypy صفر.
- [x] commit: `feat(api): add five catalog CRUD endpoints (T2.1)`

### T2.1b — رگرسیون فیچر 001 (checkpoint مستقل)
> مستقل از T2.1 تا حین اجرا گم نشود. به‌محض پایان T2.1 و پیش از T2.2.
- [x] `pytest tests/api/test_price_endpoint.py -v` — هر ۶ تست pass.
- [x] اگر شکست: توقف (Fail Fast)، گزارش، رفع پیش از ادامه.



### T2.2 — تست integration endpoint
- [x] `tests/api/test_catalog_endpoints.py`: همهٔ مسیرها (موفق + خطا) با
      TestClient + in-memory SQLite (همان fixture الگوی test_price_endpoint).
- [x] موارد:
      - create (201)، id تکراری (409)، قیمت منفی (422)، >۲ رقم اعشار (422)،
        name خالی (422)، slug نامعتبر (422).
      - list (200)، get_one (200)، get_one ناموجود (404).
      - update (200)، update ناموجود (404)، id body ≠ path (422)،
        audit log تولید شد، audit log **نشده** وقتی قیمت ثابت ماند.
      - delete (204)، delete ناموجود (404).
- [x] Linter + mypy صفر.
- [x] commit: `test(catalog): add endpoint integration tests (T2.2)`

## فاز ۳ — Quality gates + مستندسازی

### T3.1 — تست نهایی + coverage + seed idempotency + restore-on-reseed
- [x] اجرای pytest روی کل پروژه — همگی pass.
- [x] ruff check . — صفر.
- [x] mypy --strict app/ — صفر.
- [x] coverage روی `app/catalog/service.py` ≥ ۸۰٪.
- [x] `tests/test_seed.py` دوباره اجرا شود → idempotency در حضور CRUD سالم (AC5).
- [x] **تست restore-on-reseed (چک ۱′):** یک محصول seed‌شده را با DELETE حذف کن،
      سپس `seed_database()` را دوباره اجرا کن، و assert کن که محصول دوباره موجود
      است. این، رفتار شناخته‌شدهٔ «seed، محصولات حذف‌شده را بعد از restart
      بازمی‌گرداند» را ثابت می‌کند (مستند در ADR-0003).
- [x] pip-audit — صفر آسیب‌پذیری.
- [x] commit: `test(catalog): full suite passes, coverage + seed verified (T3.1)`

### T3.2 — data-model + status.md + PROJECT_STATUS
- [x] `specs/003-catalog-management/data-model.md`: قرارداد API (پنج endpoint).
- [x] `specs/003-catalog-management/status.md` نوشته شود.
- [x] به‌روزرسانی `PROJECT_STATUS.md` و `ROADMAP.md` (۰۰۳ → done).
- [x] commit: `docs(catalog): finalize data-model + status (T3.2)`
