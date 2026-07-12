# وضعیت فیچر 001-pricing

> آخرین به‌روزرسانی: ۲۰۲۶-۰۷-۱۱

## وضعیت کلی: ✅ done (با یک caveat: CI)

| بُعد | وضعیت | توضیح |
|---|---|---|
| کد | ✅ کامل | ۳ لایه Perception/Decision/Generation + API endpoint |
| تست | ✅ ۷۹ تست pass | شامل ۵ property-based test با Hypothesis |
| پوشش Decision | ✅ ۱۰۰٪ | (الزام: ≥۸۰٪) |
| mypy --strict | ✅ صفر خطا | ۲۵ فایل app/ |
| ruff check | ✅ صفر خطا | کل پروژه |
| pip-audit | ✅ صفر آسیب‌پذیری | |
| pre-commit | ✅ نصب و تأیید | تست خطای عمدی رد شد |
| CI workflow | ⚠️ done-with-caveat | فایل ساخته شد ولی remote گیت‌هاب فعلاً موجود نیست |

## معیارهای پذیرش (AC) و وضعیت نهایی
| AC | شرح | وضعیت |
|---|---|---|
| AC1 | endpoint POST /price | ✅ |
| AC2 | Category 1 hard rules (items nonempty, qty>0, price≥0, discount≤base, post-discount tax) | ✅ |
| AC3 | coverage ≥۸۰٪ + ۵ property test (Hypothesis) | ✅ (۱۰۰٪) |
| AC4 | LLM adapter + DummyLLM | ✅ |
| AC5 | ADR for adapter | ✅ (ADR-0001) |
| AC6 | rollback migration | ✅ (upgrade + downgrade تست شد) |
| AC7 | no-secret | ✅ (.env.example, detect-private-key hook) |
| AC8 | زبان محتوا فارسی | ✅ |

## Spec Drift یادداشت (فیچر 002)
`app/decision/rules.py` در T0.1 فیچر 002 دوباره لمس شد — تابع جدید
`check_deterministic_signals()` اضافه شد (Category 2، env-var configurable، جدا
از `price()`). طبق قانون Spec Drift: کل `tests/decision/` و `tests/property/`
دوباره اجرا شد — ۴۱ تست همگی pass، coverage همچنان ۱۰۰٪. فیچر 001 دست‌نخورده است.

## Spec Drift یادداشت (فیچر 003)
`app/main.py` در T2.1 فیچر 003 دوباره لمس شد — `app.include_router(catalog_router)`
برای ثبت پنج endpoint CRUD کاتالوگ اضافه شد. طبق قانون Spec Drift: کل
`tests/api/test_price_endpoint.py` دوباره اجرا شد — هر ۶ تست pass، مسیر
قیمت‌گذاری (`POST /price`) دست‌نخورده است.

## کشف‌های این فاز (برای بازگشت به shared-kit)

۱. **قانون زبان سه‌محوری** — کشف شد که قانون قبلی («کد/مستندات») محور
   «زبان محتوای کاربر-نهایی» را پوشش نمی‌داد. در constitution این پروژه اعمال شد.
۲. **قانون empty-items** — مرز Perception↔Decision نیاز به guard جدا دارد (همان
   الگوی qty، در لایه‌ای دیگر). این یک درس عمومی است: هر مرز نیاز به guard دارد.
۳. **بررسی گزارش با عدد واقعی** — گزارش‌های تست همیشه باید با `--collect-only`
   تأیید شوند، نه از حافظه. (درس از اشتباه گزارش‌دهی ۳۸ در برابر ۴۸.)
۴. **تست integration واقعی** — برچسب «integration» روی یک تست unit، گمراه‌کننده است.
   integration واقعی باید از نقطهٔ ورود واقعی شروع شود (مثلاً parse_request)، نه
   ساخت دستی ورودی.
۵. **قانون تصمیم پروژهٔ جدید در برابر فیچر جدید** — کشف شد وقتی مفهوم محصول
   متفاوت است، باید پروژهٔ جدید ساخت.
۶. **specify init --ai منسوخ** — الان `--integration` است؛ و ZCode شناسایی نمی‌شود،
   `--ignore-agent-tools` لازم است.

## درس‌های متدولوژیکی برای کیت مشترک
این موارد باید به `shared-kit/constitution-template.md` یا SETUP.md بازگردند:
- قانون زبان سه‌محوری (✅ اعمال شد در template).
- قانون empty-items / boundary guards (الگوی تعمیم‌پذیر).
- قانون گزارش‌دهی: تأیید عددی با collect-only.
- دستورالعمل specify init برای ZCode (--ignore-agent-tools).
