# Implementation Plan: 001-pricing (موتور قیمت‌گذاری پویا)

**Branch**: `001-pricing` | **Date**: 2026-07-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-pricing/spec.md`

## Summary
ساخت یک سرویس قیمت‌گذاری سه‌لایه (Perception/Decision/Generation) که درخواست
طبیعی فارسی را به پیش‌فاکتور تبدیل می‌کند. هستهٔ منطقی (Decision) کاملاً
دترمینیستیک است و با ۴ property-based test پوشش داده می‌شود. لایه‌های LLM از
طریق adapter قابل‌تعویض‌اند.

## Technical Context

**Language/Version**: Python 3.11+ (محیط فعلی: 3.12.8)
**Primary Dependencies**: FastAPI, SQLAlchemy, Alembic, Hypothesis, pytest,
  httpx (برای فراخوانی DeepSeek API)
**Storage**: PostgreSQL (production)، SQLite in-memory (تست)
**Testing**: pytest + Hypothesis (property-based)
**Target Platform**: Linux server (پشت reverse proxy)
**Project Type**: web-service (API فقط، بدون frontend)
**Performance Goals**: p95 < ۲ ثانیه (شامل فراخوانی LLM)
**Constraints**:_TOTAL_LATENCY_BUDGET=2s (LLM غالب)
**Scale/Scope**: MVP تک‌نفره، ۸ محصول seed، دو customer tier

## Constitution Check
- ✅ جداسازی سه‌لایه (Perception/Decision/Generation) — هر کدام ماژول فیزیکی جدا.
- ✅ قانون ۳۰۰ خط — هیچ فایلی نباید عبور کند (طراحی زیر برای جلوگیری از آن است).
- ✅ Type checking — `mypy --strict` در plan.md فعال است.
- ✅ Property-based testing — Hypothesis برای لایهٔ Decision.
- ✅ LLM adapter — DummyLLM قابل‌تزریق.
- ✅ no-secret — کلید از `.env`.
- ✅ زبان سه‌محوری — کد انگلیسی، مستندات فارسی، محتوای کاربر فارسی.

## Project Structure

### Documentation (this feature)
```text
specs/001-pricing/
├── spec.md              ✅
├── plan.md              # این فایل
├── research.md          # بعداً
├── data-model.md        # بعداً
├── contracts/           # بعداً
└── tasks.md             # فاز بعدی (/speckit.tasks)
```

### Source Code
```text
pricing-engine/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app + route registration (کوتاه)
│   ├── config.py                    # pydantic-settings (env vars)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py                # POST /price endpoint (نازک — فقط dispatch)
│   │   └── schemas.py               # Pydantic request/response models
│   │
│   ├── perception/                  # لایهٔ ۱: LLM parse
│   │   ├── __init__.py
│   │   ├── service.py               # orchestration
│   │   ├── llm_adapter.py           # abstract LLMAdapter + DeepSeekAdapter + DummyLLM
│   │   └── prompts.py               # prompt templates (فارسی→PurchaseRequest)
│   │
│   ├── decision/                    # لایهٔ ۲: دترمینیستیک
│   │   ├── __init__.py
│   │   ├── service.py               # orchestration
│   │   ├── rules.py                 # Category 1 hard rules (qty, price, discount, tax)
│   │   ├── discounts.py             # Category 2 tunable discounts (non-stacking)
│   │   └── models.py                # PurchaseRequest, LineItem, PriceResult (dataclasses)
│   │
│   ├── generation/                  # لایهٔ ۳: LLM تولید متن فارسی
│   │   ├── __init__.py
│   │   ├── service.py               # orchestration (استفاده از همان llm_adapter)
│   │   └── prompts.py               # prompt templates (PriceResult→متن فارسی)
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py                  # SQLAlchemy declarative base
│   │   ├── models.py                # Product, CustomerTier (seed)
│   │   ├── session.py               # sessionmaker
│   │   └── seed.py                  # ۸ محصول seed (idempotent)
│   │
│   └── migrations/                  # Alembic
│       ├── env.py
│       └── versions/
│           └── 001_initial.py       # + downgrade path
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # fixtures (DummyLLM, in-memory SQLite, test client)
│   ├── decision/
│   │   ├── test_rules.py            # unit tests + property tests (Hypothesis)
│   │   └── test_discounts.py        # unit tests + property test for non-stacking
│   ├── perception/
│   │   └── test_service.py          # با DummyLLM (نه DeepSeek واقعی)
│   ├── generation/
│   │   └── test_service.py          # با DummyLLM
│   ├── api/
│   │   └── test_price_endpoint.py   # integration (e2e با DummyLLM)
│   └── property/
│       └── test_invariants.py       # ۴ property-based tests اصلی
│
├── pyproject.toml                   # ruff, mypy, pytest, Hypothesis config
├── requirements.txt
├── alembic.ini
├── .env.example
└── (governance files)
```

**Structure Decision**: هر لایه یک پوشهٔ مجزا با `service.py` به‌عنوان نقطهٔ
ورود. این جداسازی فیزیکی است، نه قراردادی. مهم‌ترین قانون: هیچ فایلی نباید
عبور از ۳۰۰ خط کند — `rules.py` و `discounts.py` جدا نگه داشته شدند تا اگر
قواعد رشد کردند، هر کدام مستقل بمانند. `llm_adapter.py` شامل abstract base +
دو implementation است (DeepSeek + Dummy)، ولی این منطقاً یک واحد منسجم است و
احتمالاً تحت ۳۰۰ خط می‌ماند (اگر عبور کرد، در ADR ثبت می‌شود).

## منطق جریان داده (Data Flow)

```
POST /price (request_text + context)
    │
    ▼
[api/routes.py] ── validate input ──→ [perception/service.py]
                                          │
                                          ▼
                                   [llm_adapter] ──→ PurchaseRequest (ماشین‌خوان)
                                          │          (اگر نامعتبر: خطای صریح)
                                          ▼
                                  [decision/service.py]
                                          │
                                 ┌────────┴────────┐
                                 ▼                 ▼
                           [rules.py]         [discounts.py]
                           (Category 1)       (Category 2, non-stacking)
                                 │                 │
                                 └────────┬────────┘
                                          ▼
                                     PriceResult
                                          │
                                          ▼
                                [generation/service.py]
                                          │
                                          ▼
                                   [llm_adapter] ──→ invoice_text (فارسی)
                                          │
                                          ▼
                                   HTTP Response
```

## Cross-Cutting Concerns

### Error Handling
- Perception نامعتبر (qty منفی، محصول ناشناخته) → HTTP 422 با خطای صریح.
- LLM در دسترس نیست → fallback خودکار به DummyLLM + هشدار log (نه خطا).
- Decision هرگز نباید exception رها کند — همهٔ خطاها به‌صورت PriceResult با
  `status: "rejected"` برمی‌گردند.

### Configuration (env vars)
همه از `.env`:
- `DEEPSEEK_API_KEY` — کلید LLM
- `DATABASE_URL` — PostgreSQL production
- `TEST_DATABASE_URL` — SQLite in-memory
- `TAX_RATE` — Category 1 (default: 0.09)
- `DEFAULT_SEASONAL_DISCOUNT_RATE` — Category 2 (default: 0.10)
- `VIP_CUSTOMER_DISCOUNT_RATE` — Category 2 (default: 0.15)

### Testing Strategy
- **Unit (decision/):** ۸۰٪+ coverage، همهٔ قواعد Category 1 و ۲.
- **Property (decision/ + property/):** ۴ invariant اصلی با Hypothesis.
- **Integration (api/):** e2e با DummyLLM (نه DeepSeek واقعی).
- **LLM real (perception/, generation/):** فقط smoke test اختیاری با DeepSeek؛
  اگر کلید نباشد، skip می‌شود (done-with-caveat نه، چون کلید هست).

## Complexity Tracking
(خالی — هیچ تخطی از constitution لازم نیست. همهٔ قوانین رعایت می‌شوند.)
