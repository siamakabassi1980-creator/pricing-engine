# وضعیت پروژه — موتور قیمت‌گذاری پویا

> آخرین به‌روزرسانی: ۲۰۲۶-۰۷-۰۷ (پایان فاز Specify/Clarify + بستر آماده)

## خلاصهٔ فعلی
پروژه در فاز Specify/Clarify است. بستر (governance, pre-commit, venv) آماده و
تأیید شده. مرحلهٔ بعدی: `/speckit.plan`.

## فیچرها
| ID | نام | وضعیت | فاز |
|---|---|---|---|
| 001 | pricing (MVP) | 🔵 in-progress | specify + clarify done، در انتظار plan |

## بستر پروژه (Platform)
| مؤلفه | وضعیت | یادداشت |
|---|---|---|
| Git repo | ✅ initialized | commit پایه + commit اصلاح qty |
| AGENTS.md | ✅ نازک (از shared-kit) | فقط ارجاع به constitution |
| constitution.md | ✅ نوشته شده | معماری سه‌لایه + حاکمیت کیت |
| .specify/ (Spec Kit) | ✅ نصب | `specify init` واقعی اجرا شد |
| pre-commit | ✅ نصب + تأیید | تست خطای عمدی رد شد (۴ خطا) |
| venv | ✅ ساخته شد | python 3.12.8 |
| CLAUDE.md | ✅ پل @AGENTS.md | Active Technologies دستی (رصد برای تداخل با plan) |
| .env.example | ✅ | کلید DeepSeek placeholder |
| LLM key | ✅ در `.env` | (نه در repo) |

## کشف‌های متدولوژیکی (برای بازگشت به shared-kit)

> هر کشف واقعی در طول این پروژه که قانون/الگویی جدید لو می‌دهد، اینجا جمع
> می‌شود. در پایان فیچر، این موارد به `shared-kit/constitution-template.md`
> بازمی‌گردند.

- (تا الان) قانون زبان سه‌محوری (کد/مستندات/محتوای کاربر) — از دورهای بازبینی
  SDD کشف شد، در constitution این پروژه اعمال شده، باید به shared-kit برگردد. ✅
- قانون تصمیم «پروژهٔ جدید در برابر فیچر جدید» — اعمال شد در AGENTS.md. ✅
- (در انتظار) رفتار سیستم وقتی property-based testing نامناسب است (فیچر ۰۰۲).

## معیارهای پذیرش فیچر ۰۰۱ و وضعیت
- AC1 (endpoint): ⚪ pending implement
- AC2 (Category 1 hard rules: qty>0, price≥0, discount≤base, post-discount tax): ⚪ pending
- AC3 (coverage ≥۸۰٪ + ۴ property tests): ⚪ pending
- AC4 (LLM adapter + DummyLLM): ⚪ pending
- AC5 (ADR for adapter): ⚪ pending
- AC6 (rollback migration): ⚪ pending
- AC7 (no-secret): ✅ بستر (.env.example, detect-private-key hook)
- AC8 (زبان محتوا فارسی): ⚪ pending implement
