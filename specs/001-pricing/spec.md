# spec.md — 001-pricing (موتور قیمت‌گذاری پویا)

## Why
این فیچر آزمایش کامل «معماری سه‌لایه (Perception/Decision/Generation) + property-based testing + LLM-adapter» است. دلیل انتخاب این دامنه: invariantهای مالی (price ≥ 0، discount ≤ base، tax = subtotal × rate) ریاضی‌اند، بنابراین property-based testing در اینجا بدیهی‌ترین ابزار است — نه تمرینی به‌زور. اگر نتوان در این دامنه از property-based testing دفاع کرد، در هیچ دامنه‌ای قابل‌دفاع نیست.

این فیچر همچنین اولین آزمایش قانون **done-with-caveat روی وابستگی از جنس سرویس خارجی** (نه دیتابیس) است: اگر کلید LLM در دسترس نباشد، فیچر با dummy-LLM ساخته می‌شود و معیار «تولید متن طبیعی واقعی» به‌صورت done-with-caveat علامت می‌خورد.

## What
یک سرویس قیمت‌گذاری که درخواست مشتری به زبان طبیعی (فارسی) + context (catalog، customer tier، season) را می‌گیرد و پیش‌فاکتور ساختاریافته (فارسی) برمی‌گرداند.

سه لایه باید فیزیکی جدا باشند (ماژول‌های جدا، نه توابع پشت‌سرهم):
- `perception/`: parse درخواست آزاد به `PurchaseRequest` ماشین‌خوان (LLM از طریق adapter)
- `decision/`: اعمال قواعد قیمت/مالیات/تخفیف روی `PurchaseRequest` (دترمینیستیک، **بدون LLM**)
- `generation/`: تولید پیش‌فاکتور قابل‌فهم فارسی + توضیح تخفیف (LLM از طریق adapter)

### ورودی
```
POST /price
{
  "request_text": "۲۰ عدد هدفون X، ارسال اکسپرس، مشتری ویژه",
  "context": {
    "catalog": [...8 محصول seed...],
    "customer_tier": "special" | "regular",
    "season": "normal" | "sale"
  }
}
```

### خروجی
```
{
  "line_items": [{"product": "هدفون X", "qty": 20, "unit_price": ..., "line_total": ...}],
  "subtotal": ...,
  "discount": ...,
  "discount_reason": "...",
  "tax": ...,
  "total": ...,
  "invoice_text": "..."   // پیش‌فاکتور فارسی قابل‌فهم
}
```

## Acceptance Criteria
1. endpoint `POST /price` درست کار می‌کند و قرارداد خروجی بالا را برمی‌گرداند.

2. **قواعد Category 1 (hard) همیشه حفظ می‌شوند، فارغ از خروجی LLM:**
   - `items` باید حداقل یک آیتم داشته باشد — اگر Perception به‌خاطر پاسخ نامفهوم
     LLM لیست خالی برگرداند، Decision باید آن را با دلیل صریح **رد کند**، نه
     به‌عنوان یک «سفارش موفق ۰ تومانی» بپذیرد. (همان anti-pattern silent-drop
     که برای qty بسته شد، اینجا در مرز Perception↔Decision بسته شد.)
   - `qty > 0` همیشه — Decision باید هر line item با qty نامعتبر (صفر یا منفی) را
     با خطای صریح **رد کند**، نه silently drop یا محاسبهٔ نادرست. این دقیقاً همان
     نوع سوراخی است که Perception را غیرقابل‌اعتماد می‌کند و Decision باید محافظ باشد.
   - `unit_price ≥ 0` همیشه.
   - `discount ≤ base` همیشه (نکته: تخفیف non-stacking است — اگر چند تخفیف هم‌زمان
     صدق کنند، فقط بیشترین مقدار اعمال می‌شود).
   - **مالیات روی مبلغ بعد از تخفیف، نه base خام** (VAT ایران روی مبلغ نهایی پرداختی):
       ```
       base           = Σ(unit_price × qty)              // فقط وقتی محاسبه می‌شود
                                                        // که همهٔ qtyها معتبر باشند؛
                                                        // اگر حتی یک qty نامعتبر وجود
                                                        // داشته باشد، کل درخواست رد
                                                        // می‌شود (نه فیلتر تک‌آیتم)
       discount       = max(applicable_discounts)        // non-stacking, مقدار مطلق پولی
       subtotal       = base − discount
       tax            = subtotal × rate                  // rate فیکس: 0.09
       total          = subtotal + tax
       ```
   - توجه: `discount` در این فرمول **مقدار مطلق پولی** است، نه نرخ. تبدیل نرخ→مبلغ
     (`discount_amount = base × discount_rate`) باید در لایهٔ Decision رخ دهد، نه بیرون از آن.
   - حتی اگر Perception خروجی نامعتبر برگرداند، Decision آن را رد می‌کند، نه اینکه
     قیمت منفی یا تخفیف بیش از ۱۰۰٪ تولید کند.

3. **پوشش تست لایهٔ Decision ≥ ۸۰٪، با حداقل چهار property-based test (Hypothesis):**
   - (الف) non-negative total: برای هر ورودی تصادفی معتبر، `total ≥ 0`.
   - (الف′) **non-negative unit_price مستقیم:** `unit_price ≥ 0` به‌صورت مستقیم روی
     هر line item تست شود، نه فقط از طریق اثر نهایی‌اش روی `total` — تا اگر
     محاسبه‌ای خراب شد، تست دقیق‌تر بگوید کجا. (این یک invariant مستقیم است،
     نه ترکیبی.)
   - (ب) discount ≤ base: برای هر ترکیب تخفیف، `discount ≤ base`.
   - (ج) tax قطعی: برای هر ورودی معتبر، `tax = subtotal × 0.09` دقیقاً.
   - (د) **رد qty نامعتبر:** برای هر ورودی با qty ≤ 0، Decision خطای صریح برمی‌گرداند،
     نه یک نتیجهٔ محاسبه‌شده. (این property ممکن است نیاز به strategy خاص Hypothesis
     داشته باشد — ورودی‌های نامعتبر، نه معتبر.)

4. **Perception و Generation از طریق adapter قابل‌تعویض‌اند:** یک `DummyLLM` قابل‌تزریق برای تست بدون کلید API واقعی. وقتی کلید DeepSeek در `.env` نباشد، adapter به‌صورت خودکار به `DummyLLM` عوض می‌شود و یک هشدار صادر می‌شود (نه خطا).

5. **یک ADR ثبت می‌شود:** چرا Perception باید قابل‌تعویض باشد (lock-in نشدن به یک provider، قابلیت تست بدون کلید، آماده‌بودن برای افزودن providerهای دیگر).

6. **هر migration مسیر rollback معتبر و تست‌شده** دارد (`alembic downgrade`).

7. **no-secret:** کلید LLM از `.env` خوانده می‌شود (`DEEPSEEK_API_KEY`)، هرگز در کد نیست. `detect-private-key` hook در pre-commit فعال است.

8. **زبان محتوای کاربر-نهایی:** متن درخواست ورودی و خروجی پیش‌فاکتور **فارسی** است. (طبق constitution: کد انگلیسی، مستندات فارسی، محتوای کاربر فارسی.)

## Out of Scope
- رابط کاربری (فقط API).
- مدیریت کاتالوگ محصولات (seed ثابت با ۸ محصول؛ CRUD ندارد).
- چندارزی (فقط یک واحد پولی، فرض: تومان).
- اعتبارسنجی موجودی انبار.
- پرداخت واقعی.
- احراز هویت کاربر (در MVP فرض می‌شود context از سمت فراخواننده می‌آید).
- صوت یا STT/TTS.
- پشتیبانی از چند زبان مبدأ (فقط فارسی).

## پرسش‌های Clarify — بسته‌شده (با پاسخ توسعه‌دهنده)
1. کلید LLM: بله، کلید DeepSeek در `.env` موجود است → معیار «تولید متن طبیعی واقعی» قابل آزمایش است (نه done-with-caveat). ولیDummyLLM همچنان برای تست واحد الزامی است.
2. Category 2: فقط دو نوع تخفیف — مشتری ویژه (۱۵٪ ثابت) و فصلی (۱۰٪ پیش‌فرض، قابل تنظیم). **Non-stacking:** اگر هر دو صدق کنند، فقط بیشترین تخفیف اعمال می‌شود.
3. کاتالوگ: seed ثابت با ۸ محصول (قیمت متنوع). `customer_tier`: enum با دو مقدار `regular`/`special`.
4. زبان محتوای تجاری: فارسی.
5. فرمول مالیات: تأیید شد — `subtotal = base − discount`؛ `tax = subtotal × rate`؛ `total = subtotal + tax`. discount مقدار مطلق پولی است (نرخ→مبلغ در Decision تبدیل می‌شود).
6. کتابخانهٔ property-based: Hypothesis تأیید شد؛ پیاده‌سازی دست‌ساز استفاده نشود.
