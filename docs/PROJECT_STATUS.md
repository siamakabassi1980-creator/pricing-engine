# وضعیت پروژه — موتور قیمت‌گذاری پویا

> آخرین به‌روزرسانی: ۲۰۲۶-۰۷-۱۱ (پایان فاز ۴ — فیچر ۰۰۱ done)

## خلاصهٔ فعلی
فیچر 001-pricing کامل شد (با یک caveat: CI workflow ساخته شد ولی تأیید نشده چون
remote گیت‌هاب فعلاً موجود نیست). ۷۹ تست pass، پوشش Decision ۱۰۰٪.

## فیچرها
| ID | نام | وضعیت | توضیح |
|---|---|---|---|
| 001 | pricing (MVP) | ✅ done-with-caveat | CI workflow بدون remote تأیید نشده |
| 002 | catalog-management | ⚪ not-started | وابسته به 001 |
| 003 | multi-currency | ⚪ not-started | وابسته به 001 |
| 004 | inventory-check | ⚪ not-started | وابسته به 001, 002 |

## آمار نهایی فیچر 001
- **۷۹ تست** pass (شامل ۵ property-based test با Hypothesis)
- **پوشش Decision: ۱۰۰٪** (الزام: ≥۸۰٪)
- **mypy --strict: صفر خطا** روی ۲۵ فایل
- **ruff check: صفر خطا** روی کل پروژه
- **pip-audit: صفر آسیب‌پذیری**
- **۵ فاز کامل**: Foundation → Decision → Perception → Generation → API

## بستر پروژه (Platform)
| مؤلفه | وضعیت |
|---|---|
| Git repo | ✅ |
| AGENTS.md (نازک) | ✅ |
| constitution.md (سه‌لایه) | ✅ |
| .specify/ (Spec Kit) | ✅ |
| pre-commit (نصب + تأیید) | ✅ |
| venv (python 3.12) | ✅ |
| ADR-0001 (LLM adapter) | ✅ |
| CI workflow | ⚠️ done-with-caveat |

## کشف‌های متدولوژیکی (برای بازگشت به shared-kit)
۱. قانون زبان سه‌محوری (✅ اعمال شد)
۲. قانون empty-items / boundary guards
۳. قانون گزارش‌دهی: تأیید عددی
۴. دستورالعمل specify init برای ZCode
۵. قانون پروژهٔ جدید در برابر فیچر جدید
