# وضعیت فیچر 003-catalog-management

> آخرین به‌روزرسانی: ۲۰۲۶-۰۷-۱۱

## وضعیت کلی: ✅ done

| بُعد | وضعیت | توضیح |
|---|---|---|
| کد | ✅ کامل | لایهٔ catalog (service + schemas) + پنج endpoint HTTP |
| تست | ✅ ۱۶۳ تست کل پروژه | شامل ۵۸ تست جدید این فیچر |
| پوشش catalog/service.py | ✅ ۱۰۰٪ | (AC: ≥۸۰٪) |
| پوشش catalog/schemas.py | ✅ ۱۰۰٪ | |
| mypy --strict | ✅ صفر خطا | ۳۳ فایل app/ |
| ruff check | ✅ صفر | کل پروژه |
| pip-audit | ✅ صفر آسیب‌پذیری | |
| ADR-0003 | ✅ نوشته شد | no-auth + restore-on-reseed |

## معیارهای پذیرش (AC) و وضعیت نهایی
| AC | شرح | وضعیت |
|---|---|---|
| AC1 | پنج عملیات CRUD | ✅ |
| AC2 | Category 1 hard (price≥0، name/id غیرخالی) | ✅ |
| AC3 | خطای استاندارد REST (409/404/422) | ✅ |
| AC4 | کاملاً دترمینیستیک، بدون LLM | ✅ |
| AC5 | seed همچنان idempotent | ✅ (تست restore-on-reseed هم اضافه شد) |
| AC6 | تست‌پذیر با SQLite in-memory | ✅ |
| AC7 | slug انگلیسی + name_fa فارسی | ✅ |
| AC8 | مستندسازی قرارداد API | ✅ (data-model.md) |
| AC9 | audit log تغییر قیمت (پس‌رویدادی، نه پیشگیرانه) | ✅ |
| AC10 | ADR-0003 برای «بدون auth» | ✅ |

## آمار تست این فیچر
| فایل | تعداد | نوع |
|---|---|---|
| tests/catalog/test_schemas.py | ۲۷ | unit (schema validation) |
| tests/catalog/test_service.py | ۱۳ | unit (CRUD + audit caplog) |
| tests/api/test_catalog_endpoints.py | ۱۸ | integration (TestClient) |
| tests/test_seed.py (جدید) | ۱ | restore-on-reseed |
| **مجموع جدید** | **۵۹** | |

## کشف‌های این فاز

۱. **درس Decimal-در-برابر-string دوباره بازگشت.** ستون `Numeric(12,2)` مقدار
   `"200"` را به‌صورت `"200.00"` برمی‌گرداند. این هم‌خانوادهٔ باگ
   `Decimal('0.15')==0.15` از فیچر 001 است (دقت اعشار، نه شمارش تست). ۳ تست
   شکست خوردند قبل از اینکه با مقایسهٔ Decimal اصلاح شوند. کامنت فنی ماندگار
   در `test_catalog_endpoints.py` ثبت شد.

۲. **ORDER BY صریح برای list.** کشف شد که بدون `ORDER BY`، SQLite (rowid) و
   PostgreSQL (heap) ترتیب متفاوت می‌دهند. یک باگ بالقوهٔ flaky بین backendها
   که قبل از production گرفته شد.

۳. **coverage config به‌عنوان گیت مستقل خودکار.** کشف شد که `pyproject.toml`
   فقط `app/decision` را coverage می‌کرد، و anomaly/catalog با چک دستی جدا
   تأیید می‌شدند. اولین راه‌حل (یک `source` ترکیبی با یک `fail_under`) حفره‌ای
   داشت: میانگین ترکیبی می‌توانست یک ماژول ضعیف را پشت ماژول‌های قوی پنهان
   کند. راه‌حل نهایی: `scripts/check_coverage.sh` که سه فراخوانی `pytest --cov`
   جدا (هرکدام با `--cov-fail-under=80` مستقل) را با `&&` زنجیر می‌کند.
   تأیید شد: وقتی آستانهٔ anomaly به ۹۵٪ بالا رفت، گیت شکست خورد — حتی با
   decision/catalog در ۱۰۰٪. این AC را واقعاً پایدار کرد.

۴. **restore-on-reseed یک محدودیت ذاتی است، نه باگ.** رفتار `seed_database()`
   (SELECT-then-INSERT) باعث می‌شود محصولات seed‌شدهٔ حذف‌شده بعد از restart
   برگردند. صریح در ADR-0003 + data-model.md + تست مستند شد.

۵. **Spec Drift روی main.py به‌درستی ثبت شد.** طبق قانون constitution،
   یادداشت drift به `specs/001-pricing/status.md` (به یادداشت قبلی اضافه شد،
   نه جایگزین) و رگرسیون `tests/api/test_price_endpoint.py` (۶/۶ pass) تأیید
   کرد مسیر قیمت‌گذاری دست‌نخورده است.

## یادآوری‌های متدولوژیکی برای کیت مشترک
این موارد برای بازگشت به shared-kit یا SETUP.md مناسب‌اند:
- قانون Decimal comparison (هیچ‌گاه Decimal را به‌صورت string مقایسه نکن —
  هم‌خانوادهٔ باگ ۰.۱۵).
- قانون ORDER BY صریح در همهٔ queryهای list (cross-backend flakiness).
- قانون coverage config: وقتی ماژول جدیدی به «منطق حیاتی» اضافه می‌شود،
  `pyproject.toml` را هم به‌روز کن — نه فقط status.md.
