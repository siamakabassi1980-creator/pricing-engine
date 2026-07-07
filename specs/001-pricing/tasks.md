# Tasks — 001-pricing

> هر تسک معیار «تست pass + صفر Linter» را دارد. تسک فقط با عبور از هر سه
> (کد + تست + Linter) تیک می‌خورد. در شکست دوم پشت‌سرهم با یک رویکرد، Fail Fast.

## فاز ۰ — بستر (Foundation)

### T0.1 — پیکربندی پروژه (pyproject.toml + requirements.txt)
- [ ] `pyproject.toml` با تنظیمات ruff، mypy، pytest، Hypothesis.
- [ ] `requirements.txt` با fastapi, sqlalchemy, alembic, pydantic-settings,
      httpx, hypothesis, pytest, pytest-asyncio.
- [ ] **تأیید mypy با خطای عمدی** (نه فایل خالی): یک فایل نمونه با خطای type
      عمدی بساز (مثلاً `x: int = "string"`)، تأیید کن mypy واقعاً ردش می‌کند،
      سپس پاکش کن. فایل خالی همیشه pass می‌شود — این هیچی را تأیید نمی‌کند.
- [ ] **تأیید ruff با خطای عمدی:** یک فایل نمونه با خطای ruff عمدی بساز،
      تأیید کن ruff واقعاً ردش می‌کند، سپس پاکش کن.
- [ ] بعد از پاک‌کردن فایل‌های آزمایشی، `ruff check .` و `mypy --strict .`
      روی کد واقعی صفر خطا.
- [ ] commit: `chore(pricing): configure project dependencies and tooling`
- **Done-criteria:** mypy + ruff هر کدام با یک خطای عمدی رد شده‌اند (enforcement
  تأیید شد)، سپس روی کد واقعی صفر خطا.

### T0.2 — config + db base + session
- [ ] `app/config.py` با pydantic-settings (همهٔ env vars از plan.md).
- [ ] `app/db/base.py` (declarative base)، `app/db/session.py` (sessionmaker).
- [ ] تست: بارگذاری config از `.env` کار می‌کند.
- [ ] Linter صفر.
- [ ] commit: `feat(db): add config and database session infrastructure`

### T0.3 — مدل‌های دیتابیس + seed + migration
- [ ] `app/db/models.py` (Product, CustomerTier).
- [ ] `app/db/seed.py` (idempotent — PRODUCTS_SEED + CUSTOMER_TIERS_SEED).
- [ ] `app/migrations/` با alembic، `001_initial.py` (upgrade + **downgrade**).
- [ ] تست: `seed.py` دو بار اجرا → بار دوم ۰ درج (idempotency).
- [ ] تست: `alembic upgrade head` سپس `alembic downgrade -1` → schema حذف می‌شود.
- [ ] Linter صفر.
- [ ] commit: `feat(db): add Product/CustomerTier models, seed, and migration`

## فاز ۱ — لایهٔ Decision (دترمینیستیک، قلب منطقی)

### T1.1 — domain models (dataclasses)
- [ ] `app/decision/models.py` (LineItemRequest, PurchaseRequest, LineItemResult,
      PriceResult) — مطابق data-model.md.
- [ ] تست: ساخت PurchaseRequest معتبر.
- [ ] Linter صفر.
- [ ] commit: `feat(decision): add domain dataclasses`

### T1.2 — Category 1 hard rules
- [ ] `app/decision/rules.py`:
  - `validate_qty(items) -> rejects if any qty ≤ 0` (خطای صریح).
  - `validate_prices(items) -> rejects if any unit_price < 0`.
  - `compute_base(items) -> Decimal` (Σ unit_price × qty).
  - `compute_tax(subtotal, rate) -> Decimal` (= subtotal × rate).
- [ ] تست‌های واحد برای هر تابع.
- [ ] Linter صفر.
- [ ] commit: `feat(decision): add Category 1 hard rules`

### T1.3 — Category 2 discounts (non-stacking)
- [ ] `app/decision/discounts.py`:
  - `compute_discount(base, customer_tier, season) -> (amount, reason)`.
  - non-stacking: `max(vip_discount, seasonal_discount)`.
  - تبدیل نرخ→مبلغ اینجا (`discount_amount = base × discount_rate`).
- [ ] تست‌های واحد + property test برای non-stacking.
- [ ] Linter صفر.
- [ ] commit: `feat(decision): add Category 2 non-stacking discounts`

### T1.4 — Decision service orchestration + property tests
- [ ] `app/decision/service.py`: `price(request: PurchaseRequest, catalog) -> PriceResult`.
  - فراخوانی rules → discounts → ساخت PriceResult.
  - هرگز exception رها نکند؛ خطا به `status="rejected"` تبدیل شود.
- [ ] **۴ property test در `tests/property/test_invariants.py`:**
  - (الف) total ≥ 0 برای ورودی معتبر.
  - (الف′) unit_price ≥ 0 مستقیم روی هر line item.
  - (ب) discount ≤ base برای هر ترکیب تخفیف.
  - (ج) tax = subtotal × 0.09 دقیقاً.
  - (د) ورودی با qty ≤ 0 → status="rejected" (نه exception، نه محاسبه).
- [ ] پوشش تست decision/ ≥ ۸۰٪ (با `pytest --cov`).
- [ ] Linter صفر.
- [ ] commit: `feat(decision): add service orchestration and property-based tests`

## فاز ۲ — LLM Adapter (قابل‌تعویض)

### T2.1 — abstract LLM adapter + DummyLLM
- [ ] `app/perception/llm_adapter.py`:
  - `class LLMAdapter(Protocol)`: `complete(prompt: str) -> str`.
  - `class DummyLLM`: پاسخ‌های از پیش تعیین‌شده برای تست (پشتیبانی از map prompt→response).
  - `class DeepSeekAdapter`: فراخوانی واقعی API با httpx، timeout، fallback.
- [ ] تست: DummyLLM با چند prompt از پیش تعیین‌شده.
- [ ] **نوشتن ADR-0001** (`docs/decisions/ADR-0001-swappable-llm-adapter.md`):
  چرا adapter؟ (lock-in نشدن، تست بدون کلید، آماده برای providerهای دیگر).
- [ ] Linter صفر.
- [ ] commit: `feat(perception): add swappable LLM adapter (DeepSeek + Dummy)`

### T2.2 — Perception service (parse فارسی→PurchaseRequest)
- [ ] `app/perception/prompts.py`: template برای parse (فارسی→JSON).
- [ ] `app/perception/service.py`: `parse_request(text, catalog) -> PurchaseRequest`.
  - product_id از catalog تطبیق می‌خورد؛ unit_price از catalog (نه از LLM) تزریق.
  - qty از LLM استخراج می‌شود.
- [ ] تست با DummyLLM (نه DeepSeek واقعی).
- [ ] **تست adversarial امنیتی:** LLM یک `unit_price` جعلی/منفی برگرداند،
      تأیید کن سیستم آن را نادیده می‌گیرد و قیمت catalog را استفاده می‌کند.
      (این تصمیم امنیتی در data-model.md ثبت شده — باید regression test داشته
      باشد تا در آینده توسط اشتباه خراب نشود.)
- [ ] Linter صفر.
- [ ] commit: `feat(perception): add request parser service`

## فاز ۳ — Generation (متن فارسی)

### T3.1 — Generation service (PriceResult→متن فارسی)
- [ ] `app/generation/prompts.py`: template برای invoice text فارسی.
- [ ] `app/generation/service.py`: `generate_invoice(result: PriceResult) -> str`.
  - استفاده از همان `llm_adapter` (Perception و Generation یک adapter مشترک دارند).
- [ ] تست با DummyLLM.
- [ ] Linter صفر.
- [ ] commit: `feat(generation): add invoice text generation service`

## فاز ۴ — API Integration

### T4.1 — API schemas + route
- [ ] `app/api/schemas.py`: Pydantic models (PriceRequest, PriceResponse) مطابق contracts/.
- [ ] `app/api/routes.py`: `POST /price` (نازک — dispatch به سه لایه).
- [ ] `app/main.py`: FastAPI app + route registration.
- [ ] تست‌های integration با DummyLLM (e2e از HTTP).
- [ ] Linter صفر.
- [ ] commit: `feat(api): add POST /price endpoint`

### T4.2 — تست نهایی + Linter روی کل پروژه + type check + pip-audit
- [ ] اجرای `pytest` روی همهٔ تست‌ها — همه pass.
- [ ] اجرای `ruff check .` روی **کل پروژه** — صفر خطا.
- [ ] اجرای `mypy --strict app/` — صفر خطا.
- [ ] اجرای `pytest --cov=app/decision --cov-fail-under=80` — pass.
- [ ] **اجرای `pip-audit` روی requirements.txt** (قانون constitution:
      «بررسی دوره‌ای آسیب‌پذیری وابستگی‌ها») — صفر آسیب‌پذیری شناخته‌شده، یا
      ثبت هر آسیب‌پذیری در status.md با ارزیابی.
- [ ] اجرای دوبارهٔ `seed.py` — idempotency تأیید.
- [ ] تست smoke اختیاری با DeepSeek واقعی (اگر `.env` کلید دارد).
- [ ] به‌روزرسانی `docs/PROJECT_STATUS.md` و `status.md`.
- [ ] commit: `test(pricing): full suite passes, coverage ≥80%, linters clean`

### T4.3 — پایپ‌لاین CI (خط دوم دفاع)
- [ ] ساخت `.github/workflows/ci.yml` که همون quality gate را اجرا کند:
      `ruff check`، `mypy --strict`، `pytest --cov`، `pip-audit`.
- [ ] ساختار مینیمال: trigger on push/PR به master، Python 3.11، نصب deps از
      requirements.txt، اجرای gateها به‌ترتیب.
- [ ] **تأیید محلی:** چون این ریپو فعلاً فقط لوکال است (بدون remote گیت‌هاب)،
      تأیید واقعی اجرا ممکن نیست. فایل ساخته می‌شود ولی AC مربوطه به
      **done-with-caveat** علامت می‌خورد تا remote واقعی وصل شود و اجرای واقعی
      تأیید شود. (دقیقاً همان الگوی constitution برای زیرساخت غایب.)
- [ ] در status.md یادداشت: «CI workflow ساخته شد ولی تا افزودن remote تأیید
      نشده — نباید به‌عنوان done کامل حساب شود.»
- [ ] commit: `ci(pricing): add GitHub Actions workflow as second line of defense`

## فاز ۵ — مستندسازی و بستن

### T5.1 — status.md + PROJECT_STATUS به‌روزرسانی
- [ ] `specs/001-pricing/status.md` نوشته شود.
- [ ] `docs/PROJECT_STATUS.md` وضعیت فیچر را به `done` (یا `done-with-caveat`) تغییر دهد.
- [ ] کشف‌های متدولوژیکی جمع‌بندی و به shared-kit بازگردانده شوند.
- [ ] commit: `docs(pricing): finalize feature status and methodology lessons`
