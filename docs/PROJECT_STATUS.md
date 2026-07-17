# وضعیت پروژه — موتور قیمت‌گذاری پویا

> آخرین به‌روزرسانی: ۲۰۲۶-۰۷-۱۵ (CI از «گزارش» به «گیت» ارتقا یافت — branch protection فعال شد)

## خلاصهٔ فعلی
فیچر 001، 002، و 003 همگی کامل شدند. فیچر 003 CRUD کامل روی کاتالوگ را
از طریق پنج endpoint REST اضافه کرد — کاملاً دترمینیستیک، بدون LLM، بدون
تغییر schema. یک ADR جدید (ADR-0003) تصمیم «بدون auth» را به‌عنوان ریسک
شناخته‌شده مستند کرد. ۱۶۳ تست pass.

## فیچرها
| ID | نام | وضعیت | توضیح |
|---|---|---|---|
| 001 | pricing (MVP) | ✅ done | CI واقعی تأیید شد + branch protection فعال (CI اکنون «گیت» است نه «گزارش») |
| 002 | anomaly-flagging | ✅ done | آزمایش تست منفی موفق |
| 003 | catalog-management | ✅ done | پنج endpoint CRUD، ADR-0003 |
| 004 | multi-currency | ⚪ not-started | نرخ تبدیل ارز |
| 005 | inventory-check | ⚪ not-started | اعتبارسنجی موجودی انبار |

## آمار نهایی پروژه
- **۱۶۳ تست** pass (شامل ۸ property-based test با Hypothesis)
- **پوشش سه ماژول دترمینیستیک**: Decision ۱۰۰٪، Anomaly ۹۱٪، Catalog ۱۰۰٪
  (گیت مستقل خودکار: `bash scripts/check_coverage.sh` — هر ماژول با آستانهٔ
  ۸۰٪ مستقل گیت می‌شود، نه میانگین ترکیبی)
- **mypy --strict: صفر خطا** روی ۳۳ فایل
- **ruff check: صفر خطا**
- **pip-audit: صفر آسیب‌پذیری**
- **۳ ADR**: ADR-0001 (LLM adapter), ADR-0002 (PBT exemption), ADR-0003 (no-auth)

## قدم‌های بعدی
۱. تأیید واقعی CI (نیاز به remote گیت‌هاب)
۲. بازگرداندن کشف‌های باقی‌مانده به shared-kit (Decimal comparison، ORDER BY، coverage config)
۳. تست واقعی DeepSeek (کیفیت محصول)
۴. فیچر 004 (multi-currency) یا 005 (inventory-check) — هر دو پیش‌نیازشان done است
