# Implementation Plan: 002-anomaly-flagging

**Branch**: `002-anomaly-flagging` | **Date**: 2026-07-11 | **Spec**: [spec.md](./spec.md)

## Summary
یک لایهٔ جدا (`app/anomaly/`) که پس از Decision اجرا می‌شود و با قضاوت LLM،
درخواست‌های مشکوک را برای بازبینی انسانی پرچم می‌زند. این فیچر آزمایش تست منفی
است: ثابت می‌کند سیستم می‌تواند قانون ۸۰٪+PBT را برای بخش کیفی معاف کند (ADR-0002)،
در حالی که سیگنال‌های deterministic همچنان با property test مستقل پوشش داده می‌شوند.

## Technical Context

**Language/Version**: Python 3.11+ (محیط فعلی: 3.12.8)
**Primary Dependencies**: FastAPI, Hypothesis (فیچر 001)، httpx (همین فیچر)
**Storage**: بدون تغییر (PostgreSQL/SQLite از فیچر 001)
**Testing**: pytest + Hypothesis (فقط برای deterministic، نه کیفی)
**Project Type**: web-service (افزودن لایه به API موجود)

## Constitution Check
- ✅ Decision دست‌نخورده: AnomalyResult جدا است، PriceResult تغییر نمی‌کند.
- ✅ قانون ۳۰۰ خط: هر فایل تحت کنترل.
- ✅ Type checking: mypy --strict.
- ✅ PBT: فقط برای deterministic، نه کیفی (ADR-0002).
- ✅ LLM adapter: استفاده از همان adapter موجود.
- ✅ زبان: کد انگلیسی، مستندات فارسی، invoice_text فارسی (بدون anomaly).

## Project Structure (افزودنی روی فیچر 001)

```text
app/
├── anomaly/                      # لایهٔ جدید — جدا از decision
│   ├── __init__.py
│   ├── models.py                 # AnomalyResult (سه‌حالته)
│   ├── service.py                # orchestration + fail-open (دترمینیستیک)
│   └── prompts.py                # prompt template برای تحلیل کیفی LLM
│
├── decision/
│   ├── rules.py                  # + سیگنال‌های deterministic اینجا اضافه می‌شوند
│   │                             #   (مثلاً is_large_quantity()) — کنار قوانین
│   │                             #   Category موجود، با property test مستقل
│   └── ...
│
├── api/
│   └── schemas.py                # + anomaly_status, anomaly_reason در response
│                                 #   (ترکیب PriceResult + AnomalyResult فقط اینجا)
└── ...

tests/
├── anomaly/
│   ├── __init__.py
│   ├── test_service.py           # orchestration + fail-open (دترمینیستیک)
│   └── test_deterministic_signals.py  # property test برای qty>100 و غیره
└── api/
    └── test_price_endpoint.py    # + assertion روی anomaly_status در response
```

### محل زندگی سیگنال‌های deterministic (نکتهٔ plan)
طبق خواستهٔ Claude، صریح: سیگنال‌های deterministic (مثل `qty > 100`، `base > 10M`)
داخل **`app/decision/rules.py`** پیاده می‌شوند — کنار قوانین Category موجود.
دلیل: آن‌ها هم deterministic هستند، هم قابل property testing، هم طبیعتاً
متعلق به لایهٔ decision (نه یک لایهٔ LLM-based). پوشش تست آن‌ها به همان
`--cov=app/decision` (که از قبل ۱۰۰٪ است) اضافه می‌شود و توسط همان AC coverage
فیچر 001 پوشش داده می‌شوند — **نه** AC7 این فیچر.

AC7 فقط روی `app/anomaly/service.py` (orchestration + fail-open) اعمال می‌شود.

## Data Flow (با لایهٔ جدید)

```
POST /price (request_text + context)
    │
    ▼
[perception] → PurchaseRequest
    │
    ▼
[decision] → PriceResult (دست‌نخورده)
    │
    ├──→ [decision/rules.py]  ← سیگنال‌های deterministic (qty>100, base>10M)
    │         │                  به‌عنوان flags در PriceResult.notes یا ساختار جدا
    │         ▼
    │    deterministic_flags[]
    │
    ▼
[anomaly/service.py]  ← orchestration (دترمینیستیک)
    │   ۱. deterministic_flags را از decision می‌گیرد
    │   ۲. qualitative analysis را از LLM می‌خواهد
    │   ۳. هر کدام flagged → checked_flagged
    │   ۴. LLM نباشد → check_skipped
    ▼
AnomalyResult (جدا از PriceResult)
    │
    ▼
[api/routes.py]  ← ترکیب PriceResult + AnomalyResult فقط در schema HTTP
    │
    ▼
HTTP Response (با anomaly_status, anomaly_reason)
    │
    ▼
[generation] → invoice_text (بدون ذکر anomaly — AC8)
```

## سیگنال‌های deterministic پیشنهادی
- `qty > 100` برای هر line item → flag deterministict
- `base > 10_000_000` (۱۰ میلیون تومان) → flag deterministic
- این‌ها به rules.py اضافه می‌شوند با property test مستقل.

## تست‌ها
- **deterministic signals**: property test (Hypothesis) — `for all qty > 100, flagged`.
- **orchestration (anomaly/service.py)**: unit test با DummyLLM (۳ مسیر:
  clean, flagged, skipped).
- **fail-open**: وقتی LLM نباشد → `check_skipped`، نه exception.
- **integration API**: `anomaly_status` در response، نه در invoice_text.

## Complexity Tracking
(خالی — هیچ تخطی از constitution لازم نیست.)
