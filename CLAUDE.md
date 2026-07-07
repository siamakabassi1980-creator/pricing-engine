# Pricing Engine

پل دسترسی به قوانین حاکمیتی: دو خط زیر تضمین می‌کنند که قوانین در هر نشست
بارگذاری شوند، نه فقط هنگام اجرای دستور اسلش.

@AGENTS.md
@.specify/memory/constitution.md

## Active Technologies
<!-- این بخش به‌صورت خودکار توسط Spec Kit هنگام اجرای /speckit.plan به‌روز می‌شود. -->
- Backend: FastAPI (Python 3.11+)
- Database: PostgreSQL (production), SQLite (tests)
- Testing: Pytest + Hypothesis (property-based)
- LLM: DeepSeek (via adapter, swappable)
- Linting: ruff + mypy
