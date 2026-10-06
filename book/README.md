# اقتصادسنجی مالی و حسابداری با EViews

کتاب راهنمای عملیاتی برای نوشتن فصل روش‌شناسی و یافته‌های پایان‌نامه (فارسی، Markdown).

| فایل | محتوا |
|---|---|
| [`00-front-matter.md`](00-front-matter.md) | پیشگفتار، راهنمای کتاب، فهرست نمادها و اختصارات |
| [`01-chapter1-foundations.md`](01-chapter1-foundations.md) | فصل ۱: مبانی اقتصادسنجی (۱-۱ تا ۱-۹ + کادر نتیجه) |
| [`02-chapter2-eviews.md`](02-chapter2-eviews.md) | فصل ۲: EViews، ورود داده، Genr، Sample (۲-۱ تا ۲-۱۱ + کادر نتیجه) |
| [`03-chapter3-regression-assumptions.md`](03-chapter3-regression-assumptions.md) | فصل ۳: رگرسیون و ۸ فرض کلاسیک (۳-۱ تا ۳-۱۲) |
| [`04-appendices.md`](04-appendices.md) | پیوست الف تا د |
| `data/` | `thesis_sample.csv` (دادهٔ شبیه‌سازی‌شده، ۲۰ شرکت × ۱۰ سال) و `results.txt` (خروجی کامل آزمون‌ها) |
| `scripts/` | تولید داده و اعداد (Python)، برنامهٔ EViews (`thesis_sample.prg`) |
| `figures/` | نمودارهای کتاب |

## بازتولید اعداد
```
pip install pandas numpy scipy statsmodels matplotlib
python3 scripts/make_data_and_results.py   # داده، results.txt و نمودارهای فصل ۱ و ۳
python3 scripts/make_ch2_figures.py        # نمودارهای فصل ۲
```

## نکات صداقت
- داده‌ها **شبیه‌سازی‌شده**‌اند؛ اعداد کتاب را به‌عنوان یافتهٔ تجربی دربارهٔ شرکت‌های واقعی نقل نکنید.
- اعداد جدول‌ها با Python/statsmodels محاسبه و به قالب EViews بازنویسی شده‌اند؛ اسکرین‌شات واقعی EViews در کتاب نیست (جای آن‌ها علامت‌گذاری شده است).
- مسیرهای منو و دستورات EViews بدون دسترسی به نرم‌افزار و از روی مستندات نوشته شده‌اند؛ پیش از استفاده روی نسخهٔ خود بیازمایید.
