# وضعیت فیچر 002-anomaly-flagging

> آخرین به‌روزرسانی: ۲۰۲۶-۰۷-۱۱

## وضعیت کلی: ✅ done

| بُعد | وضعیت | توضیح |
|---|---|---|
| کد | ✅ کامل | لایهٔ anomaly + deterministic signals + API integration |
| تست | ✅ ۱۰۴ تست کل پروژه | شامل ۲۵ تست جدید این فیچر |
| پوشش anomaly/service.py | ✅ ۹۱٪ | (AC7: ≥۸۰٪) |
| mypy --strict | ✅ صفر خطا | ۲۹ فایل app/ |
| ruff check | ✅ صفر خطا | کل پروژه |
| pip-audit | ✅ صفر آسیب‌پذیری | |
| ADR-0002 | ✅ نوشته شد | معافیت PBT برای بخش کیفی |

## معیارهای پذیرش (AC) و وضعیت نهایی
| AC | شرح | وضعیت |
|---|---|---|
| AC1 | لایهٔ anomaly جدا، PriceResult دست‌نخورده | ✅ |
| AC2 | ADR-0002 با تفکیک deterministic/qualitative | ✅ |
| AC3 | DummyLLM برای تست | ✅ |
| AC4 | تشخیص کاملاً LLM-only، بدون is_anomalous() hard | ✅ |
| AC5 | fail-open سه‌حالته (check_skipped) | ✅ |
| AC6 | هیچ PBT برای بخش کیفی | ✅ (صرفاً عدم نوشتن) |
| AC7 | coverage ≥۸۰٪ روی deterministic | ✅ (۹۱٪) |
| AC8 | anomaly در response، نه invoice_text | ✅ |

## نتیجهٔ آزمایش تست منفی

**سؤال:** آیا سیستم می‌تواند بگوید «قانون ۸۰٪ coverage + PBT اینجا صدق نمی‌کند»
و مؤدبانه در ADR مستند کند، یا مصنوعی به‌زور property test تولید می‌کند؟

**جواب:** ✅ **بله.** سیستم دقیقاً تفکیک کرد:
- سیگنال‌های deterministic (qty>100, base>10M): ۳ property test با Hypothesis ✅
- بخش کیفی (LLM-only): معاف از PBT، مستند در ADR-0002 ✅
- orchestration + fail-open: unit test با DummyLLM ✅

این یعنی قانون constitution نه مطلق اعمال شد (که غلط بود) نه بی‌صدا نادیده
گرفته شد (که نقض بود) — بلکه **صریح و با دلیل معاف شد**.

## تست‌های این فیچر
| فایل | تعداد | نوع |
|---|---|---|
| tests/decision/test_anomaly_signals.py | ۱۰ | unit + property (deterministic) |
| tests/anomaly/test_models.py | ۱۳ | unit (model + service + fail-open) |
| tests/api/test_price_endpoint.py (جدید) | ۲ | integration (AC8) |
| **مجموع جدید** | **۲۵** | |
