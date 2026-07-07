# API Contract — 001-pricing

## POST /price

### Request
```json
{
  "request_text": "۲۰ عدد هدفون مدل X و ۵ عدد کیبورد مدل Y، ارسال اکسپرس",
  "context": {
    "customer_tier": "special",
    "season": "sale"
  }
}
```

فیلدها:
- `request_text` (string, required): درخواست به زبان طبیعی فارسی.
- `context.customer_tier` (enum: `"regular"` | `"special"`, required).
- `context.season` (enum: `"normal"` | `"sale"`, required).

توجه: `catalog` به‌صورت ضمنی از دیتابیس خوانده می‌شود (seed شده)، نه در request.

### Response 200 (موفق)
```json
{
  "line_items": [
    {"product_id": "headphone-x", "product_name": "هدفون مدل X", "qty": 20, "unit_price": "150000.00", "line_total": "3000000.00"},
    {"product_id": "keyboard-y",  "product_name": "کیبورد مدل Y", "qty": 5,  "unit_price": "800000.00", "line_total": "4000000.00"}
  ],
  "base": "7000000.00",
  "discount": "1050000.00",
  "discount_reason": "تخفیف مشتری ویژه (۱۵٪) — بالاتر از تخفیف فصلی (۱۰٪)",
  "subtotal": "5950000.00",
  "tax": "535500.00",
  "total": "6485500.00",
  "invoice_text": "پیش‌فاکتور:\n  ۲۰ عدد هدفون مدل X — ۳٬۰۰۰٬۰۰۰ تومان\n  ۵ عدد کیبورد مدل Y — ۴٬۰۰۰٬۰۰۰ تومان\nجمع کل: ۷٬۰۰۰٬۰۰۰ تومان\nتخفیف مشتری ویژه (۱۵٪): −۱٬۰۵۰٬۰۰۰ تومان\nمالیات بر ارزش افزوده (۹٪): ۵۳۵٬۵۰۰ تومان\nمبلغ نهایی قابل پرداخت: ۶٬۴۸۵٬۵۰۰ تومان",
  "status": "priced",
  "rejection_reason": null
}
```

### Response 422 (رد توسط Decision — Category 1 نقض شد)
```json
{
  "detail": {
    "status": "rejected",
    "rejection_reason": "qty نامعتبر برای محصول headphone-x: qty=-5 باید > 0 باشد",
    "line_items": []
  }
}
```

### Response 503 (LLLM در دسترس نیست و fallback به DummyLLM ناموفق بود)
```json
{
  "detail": "قادر به parse درخواست نیستیم — لطفاً بعداً تلاش کنید"
}
```

## مثال محاسبه ( برای property tests)

ورودی: ۲۰ هدفون (۱۵۰٬۰۰۰) + ۵ کیبورد (۸۰۰٬۰۰۰)، customer=special، season=sale.
```
base     = 20×150000 + 5×800000 = 3000000 + 4000000 = 7000000
discount = max(7000000 × 0.15, 7000000 × 0.10) = max(1050000, 700000) = 1050000
subtotal = 7000000 − 1050000 = 5950000
tax      = 5950000 × 0.09 = 535500
total    = 5950000 + 535500 = 6485500
```
