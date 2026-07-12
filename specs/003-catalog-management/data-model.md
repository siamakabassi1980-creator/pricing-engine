# Data Model & API Contract — 003-catalog-management

## مدل‌های دامنه

این فیچر هیچ مدل دامنه‌ی جدیدی اضافه نمی‌کند. از مدل موجود فیچر 001 استفاده
می‌کند:

```python
class Product(Base):
    __tablename__ = "products"
    id: Mapped[str]            # primary key — slug انگلیسی
    name_fa: Mapped[str]       # نام فارسی محصول
    unit_price: Mapped[Decimal]  # Numeric(12, 2) — تومان
```

**هیچ تغییری در schema دیتابیس انجام نمی‌شود.** جدول `products` موجود است و
CRUD فقط روی آن عمل می‌کند.

## Schemas (Pydantic)

```python
class ProductCreate(BaseModel):
    id: str            # slug: ^[a-z0-9]+(-[a-z0-9]+)*$
    name_fa: str       # غیرخالی
    unit_price: Decimal  # ≥ 0 و ≤ ۲ رقم اعشار

class ProductUpdate(BaseModel):
    id: str            # باید با path id مطابقت کند (id immutable)
    name_fa: str
    unit_price: Decimal

class ProductOut(BaseModel):
    id: str
    name_fa: str
    unit_price: Decimal
```

## قرارداد API

### POST /products — ایجاد محصول
- **ورودی:** `ProductCreate`
- **خروجی:** `ProductOut` با HTTP 201
- **خطاها:**
  - 409 Conflict — id تکراری
  - 422 — قیمت منفی، >۲ رقم اعشار، name خالی، slug نامعتبر

```
POST /products
{
  "id": "headphone-x",
  "name_fa": "هدفون مدل X",
  "unit_price": "150000"
}

→ 201
{
  "id": "headphone-x",
  "name_fa": "هدفون مدل X",
  "unit_price": "150000.00"
}
```

### GET /products — فهرست همهٔ محصولات
- **خروجی:** `list[ProductOut]` با HTTP 200
- مرتب‌سازی بر اساس `id` صریح (SQLite و PostgreSQL تضمین‌شده یکسان)

### GET /products/{id} — دریافت یک محصول
- **خروجی:** `ProductOut` با HTTP 200
- **خطا:** 404 Not Found

### PUT /products/{id} — جایگزینی کامل
- **ورودی:** `ProductUpdate` (هر سه فیلد لازم)
- **خروجی:** `ProductOut` با HTTP 200
- **خطاها:**
  - 404 Not Found
  - 422 — id در body با path id مطابقت ندارد (id immutable)
  - 422 — قیمت منفی، >۲ رقم اعشار، name خالی

**Audit log (AC9):** هر PUT که `unit_price` را واقعاً تغییر دهد، یک خط در server
log ثبت می‌کند:
```
unit_price_changed product_id=<id> old=<old> new=<new> at=<iso8601 utc>
```
این یک **audit trail پس‌رویدادی** است، نه مانع پیشگیرانه. هدف ردیابی‌پذیری است،
نه جلوگیری از تغییر. هیچ رد یا متوقف‌سازی‌ای انجام نمی‌شود.

### DELETE /products/{id} — حذف محصول
- **خروجی:** HTTP 204 No Content
- **خطا:** 404 Not Found

## محدودیت‌های شناخته‌شده

### restore-on-reseed (ADR-0003)
اگر یک محصول seed‌شده با DELETE حذف شود و بعداً `seed_database()` دوباره اجرا
شود (مثلاً هنگام restart)، محصول **دوباره ساخته می‌شود**. علت: تابع seed برای
هر محصول `SELECT` می‌کند و اگر موجود نبود `INSERT` می‌کند.

**استلزام برای اپراتورها:** DELETE روی محصولات seed‌شده فقط تا next-reseed دوام
دارد. اگر می‌خواهید یک محصول seed‌شده را برای همیشه حذف کنید، باید آن را از
`PRODUCTS_SEED` در `app/db/seed.py` هم حذف کنید.

این رفتار در `tests/test_seed.py::test_seed_restores_deleted_product_on_reseed`
تست شده است.

### بدون احراز هویت (ADR-0003)
endpointها بدون auth هستند. فرض: شبکهٔ داخلی قابل‌اعتماد. اگر API به شبکهٔ
خارج از trusted-zone برسد، auth باید برگردد.

### PUT هم‌زمان (race condition)
concurrent PUTها خارج از scope MVP هستند. فرض single-operator از شبکهٔ داخلی.
رفتار: last-write-wins در سطح DB row-lock. اگر multi-operator لازم شد،
optimistic locking در فیچر جدا اضافه می‌شود (schema change، نیاز به ADR).
