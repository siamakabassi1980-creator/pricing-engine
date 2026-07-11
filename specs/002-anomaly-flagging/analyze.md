# Analyze Report — 002-anomaly-flagging

> خروجی فاز `/speckit.analyze`: بررسی هم‌خوانی spec/plan/tasks با constitution.

## نتیجه: ✅ هم‌خوان (پس از چک‌های ویژه)

## ردیابی معیارهای پذیرش (AC → Task)
| AC | شرح | تسک پوشش‌دهنده | وضعیت |
|---|---|---|---|
| AC1 | لایهٔ anomaly جدا، PriceResult دست‌نخورده | T1.1, T1.3, T2.1 | ✅ |
| AC2 | ADR-0002 با تفکیک deterministic/qualitative | T0.2 | ✅ |
| AC3 | DummyLLM برای تست | T1.3 | ✅ |
| AC4 | تشخیص کاملاً LLM-only، بدون is_anomalous() hard | T1.3 | ✅ |
| AC5 | fail-open سه‌حالته (check_skipped) | T1.3 | ✅ |
| AC6 | هیچ PBT برای بخش کیفی | T1.3 (صرفاً از عدم) | ✅ |
| AC7 | coverage ≥۸۰٪ روی deterministic فقط | T3.1 | ✅ |
| AC8 | anomaly_status در response، نه invoice_text | T2.1 | ✅ |

## چک‌های ویژهٔ Claude (دور بازبینی این فیچر)

### چک ۱ — هم‌پوشانی قانون qty با فیچر 001
**سؤال:** آیا `is_large_quantity(qty > 100)` با `validate_qty(qty > 0)` از فیچر 001
تناقض یا هم‌پوشانی دارد؟

**بررسی:** نه — این دو قانون مکمل‌اند، نه متناقض:
- `validate_qty` (فیچر 001): **اعتبارسنجی** — qty ≤ 0 → کل درخواست رد می‌شود.
- `is_large_quantity` (فیچر 002): **پرچم‌گذاری** — qty > 100 → درخواست همچنان
  قیمت‌گذاری می‌شود ولی برای بازبینی پرچم می‌خورد.

این دو روی آستانه‌های متفاوت عمل می‌کنند (۰ در برابر ۱۰۰) و هدف متفاوتی دارند
(رد در برابر پرچم). هیچ تناقضی وجود ندارد. ولی:
- **توصیهٔ Analyze:** در T0.1، مستند شود که این قانون **رفتار قیمت‌گذاری را تغییر
  نمی‌دهد** — فقط flag اطلاعاتی تولید می‌کند. اگر روزی خواستیم qty > 100 را
  *مسدود* کنیم (نه فقط flag)، آن‌وقت یک قانون Category ۱ جدید است و باید در
  Decision service به‌عنوان validation اضافه شود، نه flag.

### چک ۲ — محل زندگی سیگنال‌های deterministic
**تأیید:** طبق plan.md، سیگنال‌های deterministic در `app/decision/rules.py` زندگی
می‌کنند (نه `app/anomaly/`). پوشش تست آن‌ها توسط AC7 این فیچر پوشش داده **نمی‌شود** —
بلکه توسط AC coverage فیچر 001 (`--cov=app/decision`) پوشش داده می‌شود. AC7 فقط
روی `app/anomaly/service.py` اعمال می‌شود. هیچ فایلی بی‌پوشش نمی‌ماند.

## انطباق با Constitution
| قانون | وضعیت | توضیح |
|---|---|---|
| Decision هرگز LLM صدا نمی‌زند | ✅ | AnomalyResult جدا، PriceResult دست‌نخورده |
| حد ۳۰۰ خط | ✅ | هر فایل تحت کنترل |
| Type checking | ✅ | mypy --strict |
| PBT | ✅ | فقط deterministic، qualitative معاف (ADR-0002) |
| Fail Fast | ✅ | tasks.md header |
| زبان سه‌محوری | ✅ | invoice_text فارسی بدون anomaly |

## یادآوری‌های متدولوژیکی برای Implement
۱. T0.2 (ADR-0002) قبل از هر چیز نوشته شود — قلب آزمایش تست منفی است.
۲. T1.3 (service) با DummyLLM تست شود، نه DeepSeek واقعی.
۳. AC6 «هیچ PBT برای کیفی» — عدم نوشتن تست هم یک معیار پذیرش است.
