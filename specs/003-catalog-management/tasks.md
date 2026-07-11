# Tasks — 003-catalog-management

> هر تسک معیار «تست pass + صفر Linter + mypy صفر» را دارد. Fail Fast برقرار است.
> پس از هر تسک، lint روی کل پروژه (نه فقط فایل همان تسک) — طبق constitution.

## فاز ۰ — ADR + پایهٔ فنی

### T0.1 — ADR-0003 (چرا بدون auth در MVP)
- [ ] `docs/decisions/ADR-0003-no-auth-mvp-risk.md` نوشته شود (با الگوی TEMPLATE.md).
- [ ] Context، Decision، Consequences (ریسک شناخته‌شده)، و شرط رفع
      (چه وقتی auth باید برگردد: وقتی API به شبکهٔ خارج از trusted-zone برسد).
- [ ] commit: `docs(catalog): ADR-0003 — no-auth as known risk in MVP`

### T0.2 — Pydantic schemas + اعتبارسنجی Category 1
- [ ] `app/catalog/__init__.py` (خالی).
- [ ] `app/catalog/schemas.py`: `ProductCreate`, `ProductUpdate`, `ProductOut`.
- [ ] اعتبارسنجی در schema:
      - `unit_price ≥ 0` (422).
      - `unit_price` با ≤ ۲ رقم اعشار (422) — تصمیم plan.
      - `name_fa` غیرخالی.
      - `id` slug الگو (حروف/عدد/خط‌تیره).
- [ ] تست واحد روی schemas (هر خطای اعتبارسنجی).
- [ ] Linter + mypy صفر.
- [ ] commit: `feat(catalog): add Pydantic schemas with Category 1 validation`

## فاز ۱ — Service لایه (دترمینیستیک)

### T1.1 — CRUD service + audit log
- [ ] `app/catalog/service.py`:
      - `create_product(session, data) -> Product` (IntegrityError → 409).
      - `list_products(session) -> list[Product]`.
      - `get_product(session, id) -> Product` (ناموجود → 404).
      - `update_product(session, id, data) -> Product` (ناموجود → 404؛
        audit log وقتی unit_price تغییر کرد).
      - `delete_product(session, id) -> None` (ناموجود → 404).
- [ ] خطاهای مفهومی کلاس اختصاصی: `ProductNotFound`, `ProductAlreadyExists`.
- [ ] audit log با `logging` (ساختار ثابت در plan).
- [ ] تست واحد service با SQLite in-memory (هر عملیات + audit با caplog).
- [ ] Linter + mypy صفر.
- [ ] commit: `feat(catalog): add CRUD service with audit log (T1.1)`

## فاز ۲ — HTTP لایه

### T2.1 — catalog_routes.py + ثبت در main.py
- [ ] `app/api/catalog_routes.py`: پنج endpoint نازک (dispatch به service).
      - POST `/products` → 201.
      - GET `/products` → 200.
      - GET `/products/{id}` → 200 | 404.
      - PUT `/products/{id}` → 200 | 404 | 422 (id body ≠ path).
      - DELETE `/products/{id}` → 204 | 404.
- [ ] نگاشت خطای مفهومی → HTTP status (404، 409، 422).
- [ ] ثبت router در `app/main.py` (`app.include_router(catalog_router)`).
- [ ] Linter + mypy صفر.
- [ ] commit: `feat(api): add five catalog CRUD endpoints (T2.1)`

### T2.2 — تست integration endpoint
- [ ] `tests/api/test_catalog_endpoints.py`: همهٔ مسیرها (موفق + خطا) با
      TestClient + in-memory SQLite (همان fixture الگوی test_price_endpoint).
- [ ] موارد:
      - create (201)، id تکراری (409)، قیمت منفی (422)، >۲ رقم اعشار (422)،
        name خالی (422)، slug نامعتبر (422).
      - list (200)، get_one (200)، get_one ناموجود (404).
      - update (200)، update ناموجود (404)، id body ≠ path (422)،
        audit log تولید شد، audit log **نشده** وقتی قیمت ثابت ماند.
      - delete (204)، delete ناموجود (404).
- [ ] Linter + mypy صفر.
- [ ] commit: `test(catalog): add endpoint integration tests (T2.2)`

## فاز ۳ — Quality gates + مستندسازی

### T3.1 — تست نهایی + coverage + seed idempotency
- [ ] اجرای pytest روی کل پروژه — همگی pass.
- [ ] ruff check . — صفر.
- [ ] mypy --strict app/ — صفر.
- [ ] coverage روی `app/catalog/service.py` ≥ ۸۰٪.
- [ ] `tests/test_seed.py` دوباره اجرا شود → idempotency در حضور CRUD سالم (AC5).
- [ ] pip-audit — صفر آسیب‌پذیری.
- [ ] commit: `test(catalog): full suite passes, coverage + seed verified (T3.1)`

### T3.2 — data-model + status.md + PROJECT_STATUS
- [ ] `specs/003-catalog-management/data-model.md`: قرارداد API (پنج endpoint).
- [ ] `specs/003-catalog-management/status.md` نوشته شود.
- [ ] به‌روزرسانی `PROJECT_STATUS.md` و `ROADMAP.md` (۰۰۳ → done).
- [ ] commit: `docs(catalog): finalize data-model + status (T3.2)`
