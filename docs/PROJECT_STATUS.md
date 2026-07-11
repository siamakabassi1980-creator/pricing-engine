# وضعیت پروژه — موتور قیمت‌گذاری پویا

> آخرین به‌روزرسانی: ۲۰۲۶-۰۷-۱۱ (پایان فیچر 002 — آزمایش تست منفی)

## خلاصهٔ فعلی
فیچر 001 و 002 هر دو کامل شدند. آزمایش تست منفی موفق بود: سیستم توانست PBT
را برای بخش کیفی معاف کند و در ADR-0002 مستند نماید، در حالی که سیگنال‌های
deterministic همچنان با property test پوشش داده شدند. ۱۰۴ تست pass.

## فیچرها
| ID | نام | وضعیت | توضیح |
|---|---|---|---|
| 001 | pricing (MVP) | ✅ done-with-caveat | CI بدون remote |
| 002 | anomaly-flagging | ✅ done | آزمایش تست منفی موفق |
| 003 | catalog-management | ⚪ not-started | CRUD روی کاتالوگ |
| 004 | multi-currency | ⚪ not-started | نرخ تبدیل ارز |

## آمار نهایی پروژه
- **۱۰۴ تست** pass (شامل ۸ property-based test با Hypothesis)
- **پوشش Decision: ۱۰۰٪، Anomaly: ۹۱٪**
- **mypy --strict: صفر خطا** روی ۲۹ فایل
- **ruff check: صفر خطا**
- **pip-audit: صفر آسیب‌پذیری**
- **۲ ADR**: ADR-0001 (LLM adapter), ADR-0002 (PBT exemption)

## قدم‌های بعدی
۱. تأیید واقعی CI (نیاز به remote گیت‌هاب)
۲. بازگرداندن ۳ کشف باقی‌مانده به shared-kit
۳. تست واقعی DeepSeek (کیفیت محصول)
