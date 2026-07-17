# ADR-0001: Swappable LLM Adapter via Protocol

## عنوان
استفاده از یک Protocol انتزاعی (`LLMAdapter`) به‌عنوان نقطهٔ دسترسی به LLM، به‌جای فراخوانی مستقیم provider.

## وضعیت
Accepted (۲۰۲۶-۰۷-۰۷)

## زمینه (Context)
لایه‌های Perception و Generation هر دو به یک LLM نیاز دارند (DeepSeek در پروژهٔ فعلی). دو نیرو این تصمیم را شکل دادند:

۱. **تست بدون کلید API واقعی.** کلید DeepSeek در `.env` موجود است، ولی نباید وابستهٔ تست به آن باشیم. تست باید با یک DummyLLM قابل پیش‌بینی اجرا شود تا deterministic بماند و هزینه/غیرقطعیت نداشته باشد.

۲. **جلوگیری از lock-in به یک provider.** اگر در آینده خواستیم به OpenAI یا یک مدل محلی سوئیچ کنیم، نباید کد Perception/Generation بازنویسی شود — فقط یک adapter جدید.

۳. **جداسازی مسئولیت.** Perception باید منطق parse باشد، نه دانستن جزئیات HTTP و احراز هویت یک API خاص.

## تصمیم
تعریف یک `Protocol` پایتون به نام `LLMAdapter` با یک متد `complete(prompt: str) -> str`. سه پیاده‌سازی:
- `DeepSeekAdapter`: فراخوانی واقعی API با httpx، timeout، fallback.
- `DummyLLM`: پاسخ‌های از پیش تعیین‌شده برای تست (یک map از prompt→response).
- (آینده) سایر providers به‌سادگی با افزودن کلاس جدید.

## پیامدها (Consequences)
- **مثبت:** تست‌ها deterministic می‌مانند (DummyLLM)، تغییر provider بدون بازنویسی لایه‌های دامنه، جداسازی واضح مسئولیت.
- **منفی:** یک لایهٔ غیرمستقیم اضافه می‌شود (کمی پیچیدگی).
- **خنثی / ریسک:** اگر پروتکل LLM به سرعت تغییر کند (پیچیده‌تر از تک‌متن)، باید Protocol گسترش یابد.
- **پیگیری لازم:** هنگام افزودن provider دوم، بازبینی شود که Protocol هنوز کافی است یا باید چندمتدی شود.

## الحاقیهٔ امنیتی (۲۰۲۶-۰۷-۱۲) — سقوط بی‌صدا به DummyLLM ممنوع شد

### زمینهٔ تغییر
پیاده‌سازی اولیهٔ `build_llm_adapter` در نبود `DEEPSEEK_API_KEY`، بی‌صدا به
`DummyLLM` سقوط می‌کرد — حتی در محیط تولید. این خطرناک بود: Perception ممکن
بود ورودی کاملاً نامرتبط DummyLLM را به‌جای درخواست واقعی مشتری پردازش کند، یا
Generation متن فاکتور ساختگی تولید کند — بدون هیچ crash یا سیگنال بیرونی. این
دقیقاً همان الگوی «silent-fail به حالت ناامن» است.

### تصمیم اصلاحی
رفتار fallback با یک فلگ صریح opt-in دروازه‌بانی شد:

```python
def build_llm_adapter(settings: Settings) -> LLMAdapter:
    if settings.deepseek_api_key:
        return DeepSeekAdapter(api_key=settings.deepseek_api_key)
    if settings.allow_dummy_fallback:
        return DummyLLM()
    raise RuntimeError("DEEPSEEK_API_KEY missing and dummy fallback not allowed")
```

- `allow_dummy_fallback` پیش‌فرض **False** است (safe-by-default).
- تست‌ها و local dev صریحاً `True` تنظیم می‌کنند (dependency injection، نه
  استنتاج از نام environment).
- در تولید (پیش‌فرض False)، نبود کلید یعنی برنامه اصلاً بالا نمی‌آید —
  `create_app()` validation را در startup (خارج از try/except دیتابیس) اجرا
  می‌کند، نه اینکه منتظر اولین request بماند.

**استثنا (تست/CI):** تست‌ها و CI ممکن است صریحاً
`allow_dummy_fallback=true` تنظیم کنند، چون هرگز به مشتری واقعی سرویس
نمی‌دهند — این یک opt-in آگاهانه است، نه نقض پیش‌فرض امن. شاهد: خودِ
`.github/workflows/ci.yml` در سطح job این فلگ را `true` می‌گذارد تا
`create_app()` در محیط تست اجرا شود؛ بدون آن، اصلاح امنیتی بالا تست‌های
`create_app()` را شکست می‌داد.

### اصل کلی
رفتار امن-پیش‌فرض هرگز نباید بر پایهٔ حدس‌زدن از متغیر محیطی باشد (مثلاً «اگر
در CI هستیم، احتمالاً dummy OK است»). فلگ باید صریح باشد. این اصل به
`shared-kit/constitution-template.md` (بخش حاکمیت کیفیت) هم اضافه شد.

### تست‌های زنده
- `test_build_llm_adapter_refuses_when_key_absent_and_fallback_disabled`:
  False + بدون کلید → RuntimeError.
- `test_build_llm_adapter_falls_back_to_dummy_when_key_absent`:
  True + بدون کلید → DummyLLM (رفتار تست‌های فعلی حفظ شد).
