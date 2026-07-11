# Tasks — 002-anomaly-flagging

> هر تسک معیار «تست pass + صفر Linter» را دارد. Fail Fast همچنان برقرار است.

## فاز ۰ — سیگنال‌های deterministic + ADR

### T0.1 — سیگنال‌های deterministic در decision/rules.py
- [ ] `is_large_quantity(items, threshold=100) -> bool` در rules.py.
- [ ] `is_large_total_base(base, threshold=10_000_000) -> bool` در rules.py.
- [ ] property test برای هر دو (Hypothesis): `for all qty > 100, result=True`.
- [ ] Linter + mypy صفر.
- [ ] commit: `feat(decision): add deterministic anomaly signals (qty, base)`

### T0.2 — ADR-0002 (چرا PBT برای بخش کیفی صدق نمی‌کند)
- [ ] `docs/decisions/ADR-0002-anomaly-qualitative-pbt-exemption.md` نوشته شود.
- [ ] صریح توضیح دهد: چرا «مشکوک بودن» invariant ریاضی ندارد.
- [ ] صریح توضیح دهد: تفکیک deterministic (قابل PBT) در برابر qualitative (معاف).
- [ ] commit: `docs(anomaly): ADR-0002 — PBT exemption for qualitative detection`

## فاز ۱ — لایهٔ anomaly

### T1.1 — AnomalyResult model (سه‌حالته)
- [ ] `app/anomaly/models.py`: AnomalyResult با `anomaly_status` (Literal),
      `anomaly_reason`.
- [ ] تست: ساخت سه حالت.
- [ ] Linter صفر.
- [ ] commit: `feat(anomaly): add AnomalyResult three-state model`

### T1.2 — Prompts برای تحلیل کیفی LLM
- [ ] `app/anomaly/prompts.py`: template برای تحلیل کیفی (ترکیب عجیب، لحن مشکوک).
- [ ] Linter صفر.
- [ ] commit: `feat(anomaly): add qualitative analysis prompt template`

### T1.3 — Anomaly service (orchestration + fail-open)
- [ ] `app/anomaly/service.py`: `assess_anomaly(price_result, request_text,
      deterministic_flags, llm) -> AnomalyResult`.
- [ ] orchestration: deterministic_flags + LLM qualitative → نتیجه نهایی.
- [ ] fail-open: LLM نباشد → `check_skipped`، نه exception.
- [ ] تست با DummyLLM (۳ مسیر: clean, flagged, skipped).
- [ ] Linter + mypy صفر.
- [ ] commit: `feat(anomaly): add service with fail-open three-state logic`

## فاز ۲ — Integration

### T2.1 — API schema + route update
- [ ] `app/api/schemas.py`: + `anomaly_status`, `anomaly_reason` در response.
- [ ] `app/api/routes.py`: فراخوانی anomaly layer پس از Decision، پیش Generation.
- [ ] ترکیب PriceResult + AnomalyResult فقط در schema HTTP.
- [ ] invoice_text بدون ذکر anomaly (AC8).
- [ ] تست integration: assertion روی anomaly_status در response.
- [ ] Linter صفر.
- [ ] commit: `feat(api): integrate anomaly layer into POST /price`

## فاز ۳ — Quality gates + مستندسازی

### T3.1 — تست نهایی + coverage
- [ ] اجرای pytest روی همه — pass.
- [ ] ruff check . — صفر.
- [ ] mypy --strict app/ — صفر.
- [ ] coverage روی app/anomaly/service.py ≥ ۸۰٪ (AC7).
- [ ] coverage روی app/decision/rules.py ≥ ۸۰٪ (سیگنال‌های جدید).
- [ ] pip-audit — صفر آسیب‌پذیری.
- [ ] commit: `test(anomaly): full suite passes, coverage verified`

### T3.2 — status.md + PROJECT_STATUS
- [ ] `specs/002-anomaly-flagging/status.md` نوشته شود.
- [ ] گزارش نتیجهٔ آزمایش تست منفی: آیا سیستم توانست PBT را معاف کند؟
- [ ] به‌روزرسانی PROJECT_STATUS.md.
- [ ] commit: `docs(anomaly): finalize status and negative-test experiment report`
