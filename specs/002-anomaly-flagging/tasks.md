# Tasks — 002-anomaly-flagging

> هر تسک معیار «تست pass + صفر Linter» را دارد. Fail Fast همچنان برقرار است.

## فاز ۰ — سیگنال‌های deterministic + ADR

### T0.1 — سیگنال‌های deterministic در decision/rules.py
- [x] `is_large_quantity(items, threshold=100) -> bool` در rules.py.
- [x] `is_large_total_base(base, threshold=10_000_000) -> bool` در rules.py.
- [x] property test برای هر دو (Hypothesis): `for all qty > 100, result=True`.
- [x] Linter + mypy صفر.
- [x] commit: `feat(decision): add deterministic anomaly signals (qty, base)`

### T0.2 — ADR-0002 (چرا PBT برای بخش کیفی صدق نمی‌کند)
- [x] `docs/decisions/ADR-0002-anomaly-qualitative-pbt-exemption.md` نوشته شود.
- [x] صریح توضیح دهد: چرا «مشکوک بودن» invariant ریاضی ندارد.
- [x] صریح توضیح دهد: تفکیک deterministic (قابل PBT) در برابر qualitative (معاف).
- [x] commit: `docs(anomaly): ADR-0002 — PBT exemption for qualitative detection`

## فاز ۱ — لایهٔ anomaly

### T1.1 — AnomalyResult model (سه‌حالته)
- [x] `app/anomaly/models.py`: AnomalyResult با `anomaly_status` (Literal),
      `anomaly_reason`.
- [x] تست: ساخت سه حالت.
- [x] Linter صفر.
- [x] commit: `feat(anomaly): add AnomalyResult three-state model`

### T1.2 — Prompts برای تحلیل کیفی LLM
- [x] `app/anomaly/prompts.py`: template برای تحلیل کیفی (ترکیب عجیب، لحن مشکوک).
- [x] Linter صفر.
- [x] commit: `feat(anomaly): add qualitative analysis prompt template`

### T1.3 — Anomaly service (orchestration + fail-open)
- [x] `app/anomaly/service.py`: `assess_anomaly(price_result, request_text,
      deterministic_flags, llm) -> AnomalyResult`.
- [x] orchestration: deterministic_flags + LLM qualitative → نتیجه نهایی.
- [x] fail-open: LLM نباشد → `check_skipped`، نه exception.
- [x] تست با DummyLLM (۳ مسیر: clean, flagged, skipped).
- [x] Linter + mypy صفر.
- [x] commit: `feat(anomaly): add service with fail-open three-state logic`

## فاز ۲ — Integration

### T2.1 — API schema + route update
- [x] `app/api/schemas.py`: + `anomaly_status`, `anomaly_reason` در response.
- [x] `app/api/routes.py`: فراخوانی anomaly layer پس از Decision، پیش Generation.
- [x] ترکیب PriceResult + AnomalyResult فقط در schema HTTP.
- [x] invoice_text بدون ذکر anomaly (AC8).
- [x] تست integration: assertion روی anomaly_status در response.
- [x] Linter صفر.
- [x] commit: `feat(api): integrate anomaly layer into POST /price`

## فاز ۳ — Quality gates + مستندسازی

### T3.1 — تست نهایی + coverage
- [x] اجرای pytest روی همه — pass.
- [x] ruff check . — صفر.
- [x] mypy --strict app/ — صفر.
- [x] coverage روی app/anomaly/service.py ≥ ۸۰٪ (AC7).
- [x] coverage روی app/decision/rules.py ≥ ۸۰٪ (سیگنال‌های جدید).
- [x] pip-audit — صفر آسیب‌پذیری.
- [x] commit: `test(anomaly): full suite passes, coverage verified`

### T3.2 — status.md + PROJECT_STATUS
- [x] `specs/002-anomaly-flagging/status.md` نوشته شود.
- [x] گزارش نتیجهٔ آزمایش تست منفی: آیا سیستم توانست PBT را معاف کند؟
- [x] به‌روزرسانی PROJECT_STATUS.md.
- [x] commit: `docs(anomaly): finalize status and negative-test experiment report`
