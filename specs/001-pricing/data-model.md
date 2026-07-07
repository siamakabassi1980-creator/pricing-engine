# Data Model — 001-pricing

## مدل‌های دامنه (Core Domain)

> این‌ها dataclass‌های پایتون‌اند (نه مدل‌های SQLAlchemy) — موجودیت‌های
> منطقی که بین لایه‌ها جریان دارند. مدل‌های دیتابیس جدا هستند (پایین).

### PurchaseRequest (خروجی Perception، ورودی Decision)
```python
@dataclass
class LineItemRequest:
    product_id: str        # باید در catalog موجود باشد
    qty: int               # > 0 (Category 1)
    unit_price: Decimal    # ≥ 0 (Category 1) — از catalog خوانده می‌شود، نه از LLM

@dataclass
class PurchaseRequest:
    items: list[LineItemRequest]
    customer_tier: Literal["regular", "special"]
    season: Literal["normal", "sale"]
```

نکتهٔ امنیتی مهم: `unit_price` هرگز از Perception/LLM نمی‌آید — همیشه از
catalog (دیتابیس) خوانده و به `LineItemRequest` تزریق می‌شود. Perception فقط
`product_id` و `qty` را استخراج می‌کند. این یک لایهٔ دفاعی اضافه است: حتی اگر
LLM یک price جعلی برگرداند، نادیده گرفته می‌شود.

### PriceResult (خروجی Decision، ورودی Generation)
```python
@dataclass
class LineItemResult:
    product_id: str
    product_name: str
    qty: int
    unit_price: Decimal
    line_total: Decimal        # = unit_price * qty

@dataclass
class PriceResult:
    line_items: list[LineItemResult]
    base: Decimal              # Σ(line_total)
    discount: Decimal          # مبلغ مطلق (≤ base)
    discount_reason: str       # فارسی
    subtotal: Decimal          # base - discount
    tax: Decimal               # subtotal * TAX_RATE
    total: Decimal             # subtotal + tax
    status: Literal["priced", "rejected"]
    rejection_reason: str | None
```

## مدل‌های دیتابیس (SQLAlchemy)

```python
class Product(Base):
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(String, primary_key=True)      # مثلاً "headphone-x"
    name_fa: Mapped[str] = mapped_column(String)                    # نام فارسی
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))    # تومان

class CustomerTier(Base):
    __tablename__ = "customer_tiers"
    tier: Mapped[str] = mapped_column(String, primary_key=True)    # "regular" | "special"
    discount_rate: Mapped[Decimal] = mapped_column(Numeric(3, 2))  # 0.00 - 1.00
```

## Seed Data (ثابت، idempotent)

```python
PRODUCTS_SEED = [
    ("headphone-x",   "هدفون مدل X",         Decimal("150000")),
    ("keyboard-y",    "کیبورد مدل Y",        Decimal("800000")),
    ("mouse-z",       "ماوس مدل Z",          Decimal("250000")),
    ("monitor-m",     "مانیتور مدل M",       Decimal("3500000")),
    ("cable-c",       "کابل مدل C",          Decimal("45000")),
    ("speaker-s",     "اسپیکر مدل S",        Decimal("650000")),
    ("webcam-w",      "وب‌کم مدل W",         Decimal("1200000")),
    ("adapter-a",     "آداپتور مدل A",       Decimal("95000")),
]

CUSTOMER_TIERS_SEED = [
    ("regular", Decimal("0.00")),
    ("special", Decimal("0.15")),    # VIP 15% — Category 2
]
```

## Migration

```python
# migrations/versions/001_initial.py
def upgrade():
    op.create_table("products", ...)
    op.create_table("customer_tiers", ...)
    # seed via db/seed.py (idempotent)

def downgrade():
    op.drop_table("customer_tiers")
    op.drop_table("products")
```

**تست idempotency:** `seed.py` دو بار اجرا شود → بار دوم ۰ درج، همه skip
(طبق عادت خوب مستندشده در راهنمای SDD، بخش ۱۰).
