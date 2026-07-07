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
