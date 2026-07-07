# Analyze Report — 001-pricing

> خروجی فاز `/speckit.analyze`: بررسی هم‌خوانی spec/plan/tasks با constitution.

## نتیجه: ✅ هم‌خوان (Consistent)

هیچ تناقضی بین spec/plan/tasks و constitution یافت نشد.

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

## انطباق با Constitution
| قانون | شواهد | وضعیت |
|---|---|---|
| جداسازی سه‌لایه | plan.md: app/perception, app/decision, app/generation (ماژول‌های فیزیکی جدا) | ✅ |
| حد ۳۰۰ خط | plan.md: تفکیک صریح rules.py / discounts.py / llm_adapter.py برای جلوگیری | ✅ |
| Type checking واقعی | T0.1: mypy --strict در pyproject.toml؛ T4.2: اجرای نهایی | ✅ |
| Property-based testing | T1.4: ۴ property test با Hypothesis در tests/property/ | ✅ |
| LLM adapter قابل‌تعویض | T2.1: Protocol + DummyLLM + DeepSeekAdapter | ✅ |
| done-with-caveat | AC4: اگر کلید نباشد، DummyLLM fallback (ولی کلید هست) | ✅ (نه مورد نیاز اینجا) |
| Rollback migration | T0.3: alembic downgrade تست می‌شود | ✅ |
| no-secret | .env.example (placeholders)، detect-private-key hook فعال | ✅ |
| Fail Fast | tasks.md header: «در شکست دوم پشت‌سرهم متوقف شو» | ✅ |
| زبان سه‌محوری | constitution: کد انگلیسی، مستندات فارسی، محتوای فارسی؛ spec AC8 | ✅ |

## توقعات متدولوژیکی از Implement
۱. **طبق قانون استقلال درجه‌بندی‌شده** (بخش ۱۰ راهنما)، Implement با ۳ تا ۵ تسک
   اول شروع شود، نه همهٔ ۱۳ تسک یک‌جا.
۲. **بعد از هر تسک**، تست + Linter واقعاً در ترمینال اجرا شود، نه فقط توصیف.
۳. **انتهای هر فاز**، Linter روی کل پروژه اجرا شود (نه فقط فایل همان تسک).

## ملاحظات
- CLAUDE.md بخش «Active Technologies» را دستی پر کرده‌ام — هنگام اجرای
  /speckit.plan (اگر اجرا شود) Spec Kit معمولاً merge می‌کند، ولی رصد شود که
  تکراری/ناسازگار نشود.
- تخمین: ۱۳ تسک در ۵ فاز، منطقی برای یک MVP (طبق تجربهٔ فیچر ۰۰۲ راهنما،
  حدوداً ۱-۲ ساعت اگر بستر آماده باشد).
