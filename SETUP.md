# راه‌اندازی از صفر (قالب مشترک)

> این فایل یک چک‌لیست راه‌اندازی است که برای هر پروژهٔ جدید کپی و سپس
> متناسب با استک همان پروژه تکمیل می‌شود (مثلاً نسخهٔ پایتون، وابستگی‌های خاص).

## مرحلهٔ صفر — بررسی پیش‌نیازها (قبل از هر کاری)

پیش از نصب هر چیزی، وضعیت پیش‌نیازهای زیر را بررسی کن (طبق قانون راهنما:
پیش‌نیازها هرگز نباید وسط چرخهٔ SDD کشف شوند):

۱. `python --version` (نیاز: ۳.۱۱ یا بالاتر)
۲. `git --version`
۳. `pip --version`
۴. وجود ماژول `venv` در پایتون
۵. `curl --version`
۶. `pre-commit --version`
۷. اتصال به PyPI: `pip download --no-deps --dest /tmp requests`

برای هر مورد یک ردیف در یک جدول بساز: ✅ نصب است / ❌ نیاز به نصب یا وجود
مشکل شبکه. موارد ❌ را رفع کن و دوباره تأیید بگیر تا همه ✅ شود.

## ساخت محیط مجازی و نصب وابستگی‌ها

```bash
python -m venv venv
./venv/Scripts/python.exe -m pip install --upgrade pip
./venv/Scripts/python.exe -m pip install -r requirements.txt
```

اگر نصب با timeout روبه‌رو شد، طبق روش مستندشده در بخش دوازده راهنمای SDD،
wheel را مستقیم با `curl` دانلود و از فایل محلی نصب کن.

> **نکتهٔ مهم (درس از دور Implement فیچر 003):** همیشه از
> `venv/Scripts/python.exe` استفاده کن، نه `python` سیستم — وگرنه
> `pydantic_settings` و بقیهٔ وابستگی‌ها پیدا نمی‌شوند و pytest با خطای
> `ModuleNotFoundError` هنگام collection شکست می‌خورد (۱۲ خطای collection).
> همین‌طور `venv/Scripts/ruff.exe` و `venv/Scripts/mypy.exe`.

> **یافتهٔ متدولوژیک (درس از دور shared-kit فیچر 003):** مسیر نسبی در
> templateها را همیشه با ساختار واقعی دیسک تأیید کن، نه با فرض. این
> SETUP.md قبلاً `../shared-kit/` می‌گفت، سپس به `../ZCodeProject/shared-kit/`
> اصلاح شد، و سرانجام وقتی shared-kit به ریپوی مستقل sibling منتقل شد، دوباره
> `../shared-kit/` شد. هر مسیر نسبی در template را با `ls` پیش از اعمال تأیید کن.

## کپی فایل‌های حاکمیتی از shared-kit

> این بخش باید **پیش از نصب pre-commit** بیاید، چون pre-commit به
> وجود همین فایل‌های کپی‌شده (به‌ویژه `.pre-commit-config.yaml`) نیاز دارد.

```bash
cp ../shared-kit/AGENTS.md .                # نازک — فقط ارجاع به constitution
cp ../shared-kit/.gitignore .
cp ../shared-kit/.pre-commit-config.yaml .
# constitution-template.md به‌عنوان نقطهٔ شروع برای .specify/memory/constitution.md
cp ../shared-kit/constitution-template.md .specify/memory/constitution.md
```

سپس فقط بخش «معماری» constitution.md را برای پروژهٔ خودت پر کن.

## نصب pre-commit

```bash
./venv/Scripts/python.exe -m pip install pre-commit
./venv/Scripts/python.exe -m pre_commit autoupdate
./venv/Scripts/python.exe -m pre_commit install
```

## گام تأیید نهایی (همیشه اجرا کن — رد نکن)

یک فایل با خطای عمدی Linter بساز و سعی کن commit کنی — **باید رد شود**.
اگر رد نشد، enforcement فقط روی کاغذ است و باید بررسی شود.
