# spec.md — 002-anomaly-flagging (آزمایش تست منفی)

## Why
این فیچر **آزمایش تست منفی** برای کل روش‌شناسی SDD است. فیچر 001 ثابت کرد که
سیستم می‌تواند property-based testing را در بهترین حالت اجرا کند. ولی هدف نهایی
این است که برای *هر* پروژه‌ای کار کند — از جمله دامنه‌هایی که PBT در آن‌ها
**نامناسب** است. این فیچر قرار است ثابت کند: آیا سیستم می‌تواند بگوید
«قانون ۸۰٪ coverage + PBT اینجا صدق نمی‌کند» و مؤدبانه در ADR مستند کند، یا
مصنوعی به‌زور property test تولید می‌کند؟

**دامنهٔ انتخاب‌شده — پرچم‌گذاری درخواست‌های مشکوک:** یک لایهٔ جدا (`app/anomaly/`)
که پس از Decision اجرا می‌شود. برای هر `PriceResult` با `status="priced"`،
لایهٔ anomaly تصمیم می‌گیرد: آیا این درخواست مشکوک است؟ اگر بله،
`anomaly_status="flagged"` و `anomaly_reason` به نتیجه اضافه می‌شود.

## تفکیک حیاتی: سیگنال‌های deterministic در برابر کیفی

این تفکیک قلب آزمایش تست منفی است:

| نوع سیگنال | مثال | مدل تست | کجا |
|---|---|---|---|
| **deterministic** | qty > ۱۰۰، مبلغ کل > ۱۰ میلیون | property test مستقل | قانون Category ۱/۲ معمولی |
| **کیفی (LLM-only)** | ترکیب عجیب اقلام، لحن مشکوک، الگوی غیرعادی نسبت به رفتار مشتری | **معاف از PBT** (ADR-0002) | این فیچر |

این تفکیک صادقانه‌تر است: نشون می‌دهد سیستم می‌تواند دقیق تشخیص دهد کدوم بخش
feature نیاز به تست دارد و کدوم نه — نه اینکه کل feature را یکجا معاف کند.

## What
یک لایهٔ جدید `app/anomaly/` که **پس از Decision و مستقل از آن** اجرا می‌شود.
`PriceResult` دست‌نخورده می‌ماند (نقض نمی‌شود قانون «Decision هرگز LLM صدا
نمی‌زند»).

### ورودی
```
PriceResult (از فیچر 001، status="priced") — فقط خوانده می‌شود
+ request_text (برای تحلیل کیفی توسط LLM)
```

### خروجی
```
AnomalyResult (ساختار جدا، نه فیلد در PriceResult):
  anomaly_status: Literal["checked_clean", "checked_flagged", "check_skipped"]
  anomaly_reason: str | None  # فقط اگر checked_flagged
```

سه حالت (نه bool):
- `checked_clean`: LLM بررسی کرد، مشکوک نبود.
- `checked_flagged`: LLM بررسی کرد، مشکوک تشخیص داده شد.
- `check_skipped`: LLM در دسترس نبود — **نه False** (الگوی done-with-caveat).

فقط در لایهٔ API (schema پاسخ HTTP) با `PriceResult` ترکیب می‌شود.

## Acceptance Criteria
1. لایهٔ anomaly یک ماژول جدا (`app/anomaly/`) است که پس از Decision و پیش از
   Generation اجرا می‌شود. **`PriceResult` دست‌نخورده می‌ماند** — هیچ فیلدی از
   آن توسط anomaly پر نمی‌شود (نقض قانون «Decision هرگز LLM صدا نمی‌زند»).

2. **ADR-0002** ثبت می‌شود: چرا قانون ۸۰٪ coverage + PBT فقط برای **بخش کیفی
   (LLM-only)** لایهٔ anomaly صدق نمی‌کند، نه کل لایه. سیگنال‌های deterministic
   (مثل qty > ۱۰۰) به‌صورت قانون Category ۱/۲ مستقل با property test خودشان
   پیاده می‌شوند.

3. لایهٔ anomaly با DummyLLM تست می‌شود (نه DeepSeek واقعی) — همان الگوی adapter.

4. بخش تشخیص آنومالی **کاملاً LLM-only** است — هیچ تابع `is_anomalous() -> bool`
   با قواعد hard در لایهٔ anomaly وجود ندارد. سیگنال‌های deterministic به قانون
   جدا منتقل می‌شوند (AC2).

5. اگر LLM در دسترس نباشد، لایهٔ anomaly به‌صورت **fail-open** عمل می‌کند:
   `anomaly_status="check_skipped"` (نه False). این فرق «چک شد، تمیز بود» با
   «چک نشد» را حفظ می‌کند.

6. **هیچ property-based test برای بخش کیفی (LLM-only) نوشته نشود** — صریح و عمدی
   (نقطهٔ کلیدی آزمایش تست منفی). ولی property test برای سیگنال‌های
   deterministic (قوانین جدا) نوشته می‌شود.

7. پوشش تست حداقل ۸۰٪ روی **کد دترمینیستیک** لایهٔ anomaly (orchestration,
   fallback، fail-open logic) — نه بخش LLM-only.

8. Integration با endpoint: POST /price باید `anomaly_status` و `anomaly_reason`
   را در response برگرداند. **نه در invoice_text** (متن مشتری) — فقط در پاسخ
   داخلی API/لاگ. کانال اطلاع‌رسانی به انسان (پنل ادمین، notification) خارج از
   scope این فیچر است.

## Out of Scope
- صف بازبینی انسانی (dashboard، notification) — فقط flag گذاشته می‌شود.
- یادگیری از بازخورد انسانی (feedback loop).
- مدل ML محلی برای anomaly detection.
- مسدودسازی درخواست‌های مشکوک (فقط flag، نه block).
- اعمال anomaly flag روی قیمت (قیمت تغییر نمی‌کند).
- ذکر anomaly flag در invoice_text (مشتری) — فقط در پاسخ داخلی API.

## پرسش‌های Clarify — بسته‌شده (با پاسخ توسعه‌دهنده)
۱. سیگنال‌ها به دو دسته تقسیم شوند (deterministic در برابر کیفی). ✅
۲. anomaly داخل PriceResult نرود (AnomalyResult جدا). ✅
۳. سه‌حالته (checked_clean / checked_flagged / check_skipped). ✅
۴. anomaly_flag نباید در invoice_text بیاید — فقط در پاسخ API. ✅
