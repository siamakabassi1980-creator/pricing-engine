# Analyze Report — 001-pricing

> خروجی فاز `/speckit.analyze`: بررسی هم‌خوانی spec/plan/tasks با constitution.

## نتیجه: ✅ هم‌خوان (پس از اصلاحات دور دوم بازبینی)

> **هشدار متدولوژیکی (کشف‌شده در بازبینی بیرونی):** نسخهٔ اول این گزارش گفت
> «✅ هم‌خوان، هیچ تناقضی» در حالی که دو قانون صریح constitution (CI، pip-audit)
> اصلاً چک نشده بودند. این دقیقاً همان الگوی «policy بدون enforcement» است که
> راهنما دربارهٔ pre-commit موعظه می‌کند — حالا روی خودِ فاز Analyze رخ داد.
> **درس:** «فهرست کردن قوانین و علامت زدن ✅» کافی نیست؛ باید هر قانون به‌صورت
> صریح به یک تسک نگاشت شود، وگرنه قانون به‌سادگی فراموش می‌شود.

## ردیابی معیارهای پذیرش (AC → Task)
| AC | شرح | تسک پوشش‌دهنده | وضعیت |
|---|---|---|---|
| AC1 | endpoint POST /price | T4.1 | ✅ |
| AC2 | Category 1 hard rules (qty, price, discount, tax) | T1.2, T1.3, T1.4 | ✅ |
| AC3 | coverage ≥۸۰٪ + ۴ property tests | T1.4, T4.2 | ✅ |
| AC4 | LLM adapter + DummyLLM | T2.1 | ✅ |
| AC5 | ADR for adapter | T2.1 | ✅ |
| AC6 | rollback migration | T0.3 | ✅ |
| AC7 | no-secret | T0.1, T0.3 | ✅ |
| AC8 | زبان فارسی محتوا | T3.1 | ✅ |

هر ۸ معیار پذیرش توسط حداقل یک تسک پوشش داده می‌شود. هیچ AC بی‌تسک نمانده.

## انطباق با Constitution — همهٔ قوانین (اصلاح‌شده)
| قانون | شواهد / تسک | وضعیت |
|---|---|---|
| جداسازی سه‌لایه | plan.md: app/perception, app/decision, app/generation (ماژول‌های فیزیکی جدا) | ✅ |
| حد ۳۰۰ خط | plan.md: تفکیک صریح rules.py / discounts.py / llm_adapter.py | ✅ |
| Type checking واقعی (`mypy --strict`) | T0.1 (با خطای عمدی تأیید می‌شود)، T4.2 | ✅ |
| ممنوعیت کد مرده | T4.2: ruff check روی کل پروژه | ✅ |
| Property-based testing (Hypothesis) | T1.4: ۴ property test در tests/property/ | ✅ |
| done-with-caveat برای زیرساخت غایب | T4.3: CI workflow ساخته می‌شود ولی تا افزودن remote به‌صورت done-with-caveat | ✅ |
| **بررسی دوره‌ای آسیب‌پذیری (pip-audit)** | **T4.2:** `pip-audit` روی requirements.txt اجرا می‌شود | ✅ (اصلاح شد) |
| **CI به‌عنوان خط دوم دفاع** | **T4.3:** `.github/workflows/ci.yml` ساخته می‌شود | ✅ (اصلاح شد) |
| Rollback migration | T0.3: alembic downgrade تست می‌شود | ✅ |
| Fail Fast | tasks.md header: «در شکست دوم پشت‌سرهم متوقف شو» | ✅ |
| no-secret | .env.example (placeholders)، detect-private-key hook فعال | ✅ |
| زبان سه‌محوری | constitution: کد انگلیسی، مستندات فارسی، محتوای فارسی؛ spec AC8 | ✅ |
| Spec Drift management | tasks.md: هر تسک به‌روزرسانی status.md را الزام می‌کند | ✅ |

## توقعات متدولوژیکی از Implement
۱. **طبق قانون استقلال درجه‌بندی‌شده** (بخش ۱۰ راهنما)، Implement با ۳ تا ۵ تسک
   اول شروع شود، نه همهٔ ۱۴ تسک یک‌جا.
۲. **بعد از هر تسک**، تست + Linter واقعاً در ترمینال اجرا شود، نه فقط توصیف.
۳. **انتهای هر فاز**، Linter روی کل پروژه اجرا شود (نه فقط فایل همان تسک).
۴. **T0.1:** تأیید mypy و ruff باید با خطای عمدی باشد (نه فایل خالی) — درسی
   که از همان تست pre-commit گرفتیم.

## ملاحظات
- CLAUDE.md بخش «Active Technologies» را دستی پر کرده‌ام — هنگام اجرای
  /speckit.plan (اگر اجرا شود) Spec Kit معمولاً merge می‌کند، ولی رصد شود که
  تکراری/ناسازگار نشود.
- T4.3 (CI) به‌صورت done-with-caveat است چون remote گیت‌هاب فعلاً موجود نیست.
- **تست adversarial امنیتی (T2.2):** LLM یک unit_price جعلی برگرداند، تست رد
  کند. (تصمیم امنیتی data-model.md باید regression test داشته باشد.)
