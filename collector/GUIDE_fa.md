# راهنمای کامل `rohi_collect.py` (از صفر تا آخر)

همهٔ دستورها در PowerShell و داخل پوشهٔ برنامه (مثلاً `G:\rohi`) اجرا شوند. فایل `my_symbols.csv` (ستون‌های `Symbol`، `company`، `firm_id`) کنار برنامه باشد.
**هر مرحله را یکی‌یکی و بعد از پایان قبلی اجرا کنید؛ دو مرحله را هم‌زمان در دو پنجره اجرا نکنید.**

## ۰) نصب (یک بار)
```
pip install pandas numpy requests lxml openpyxl pypdf pymupdf pytesseract pillow
```
برای OCR (PDFهای اسکن‌شده): Tesseract را از نسخهٔ UB Mannheim نصب کنید و در نصب‌کننده زبان **Persian** را تیک بزنید.

## ۱) بازار (تی‌اس‌ای‌سی)
فیلترشکن را طوری بگذارید که `cdn.tsetmc.com` باز شود.
```
python rohi_collect.py --symbols my_symbols.csv --stage tse
```
خروجی: قیمت، حجم، بازده، آمیهود، ناهمزمانی، NCSKEW و ... در پوشهٔ `out` (برای کدال به `out_codal` کپی می‌شود).

## ۲) اسناد از تی‌اس‌ای‌سی (بدون کپچا)
فهرست اطلاعیه‌ها، PDF صورت مالی (گزارش حسابرس و یادداشت‌ها)، کنترل داخلی، گزارش تفسیری. فقط دانلود می‌کند.
```
python rohi_collect.py --symbols my_symbols.csv --stage docs-tse --workers 10
```

## ۳) اکسل‌ها (هیئت‌مدیره، مدیرعامل، کارکنان، صورت‌های مالی) با دانلودمنیجر
اکسل فقط از کدال می‌آید. برای کم‌کردن کپچا، برنامه خودش اکسل را دانلود نکند و فقط **لینک‌ها** را بسازد:

۳-الف) آدرس اکسل‌ها را از کدال بگیرید (فیلترشکن خاموش؛ فقط چند صفحهٔ جست‌وجو برای هر شرکت):
```
python rohi_collect.py --symbols my_symbols.csv --stage codal --part 1/20 --urls-only --interactive
```
همین را برای قسمت‌های `2/20` تا `19/20` تکرار کنید (یا حلقه):
```
for ($i=1; $i -le 19; $i++) { python rohi_collect.py --symbols my_symbols.csv --stage codal --part "$i/20" --urls-only --interactive }
```
اگر کپچا آمد، در مرورگر حل کنید و Enter بزنید.

۳-ب) فهرست لینک‌ها را بسازید (مرتب بر اساس شرکت و سال، فقط اکسل‌هایی که هنوز ندارید):
```
python rohi_collect.py --symbols my_symbols.csv --make-links
```
خروجی: `out_codal\excel_links.txt` (هر خط یک لینک) و `excel_links_map.csv` (ترتیب → شرکت و سال).

۳-پ) در IDM:
1. Options ← Connection ← **Maximum simultaneous downloads = 1** (برای حفظ ترتیب).
2. فایل `excel_links.txt` را باز کنید، `Ctrl+A` و `Ctrl+C`.
3. در IDM: **Tasks ← Add batch download from clipboard**.
4. پوشهٔ مقصد: یک پوشهٔ خالی، مثلاً `D:\idm_excel`.

۳-ت) فایل‌ها را در پوشه‌های درست بگذارید (خودکار؛ سال هر فایل از داخل خودش تشخیص داده می‌شود):
```
python rohi_collect.py --symbols my_symbols.csv --ingest-sequence D:\idm_excel
```
فایل‌ها به نام استاندارد در `codal_files\<شماره>_<نماد>\<سال>\FS_excel_<شماره‌پیگیری>.xls` قرار می‌گیرند. اگر یک فایل دانلود نشده باشد رد می‌شود و بقیه درست جا می‌افتند.

(اکسل‌هایی را که خودتان دستی دانلود کرده‌اید می‌توانید در پوشه‌هایی به نام نماد بریزید و با `--ingest-excel پوشه` وارد کنید.)

## ۴) بررسی پوشش (بدون اینترنت)
```
python rohi_collect.py --symbols my_symbols.csv --file-gaps
```
جدول هر سال: چند شرکت اکسل، PDF حسابرس، گزارش هیئت‌مدیره، کنترل داخلی دارند. جزئیات: `out_codal\file_gaps.csv`.

## ۵) تکمیل جاهای خالی از کدال (با کپچای دستی)
```
python rohi_collect.py --symbols my_symbols.csv --stage codal --part 1/20 --interactive --fill-codal --download-only
```
برای قسمت‌های ۱ تا ۱۹. فقط شرکت‌های ناقص را از کدال تکمیل می‌کند.

## ۶) استخراج (بدون اینترنت، چند هسته‌ای)
```
python rohi_collect.py --symbols my_symbols.csv --reparse --ocr --tesseract-cmd "C:\Program Files\Tesseract-OCR\tesseract.exe"
```
- اکسل‌ها: هیئت‌مدیره، مدیرعامل، کارکنان، صادرات، پیش‌بینی.
- PDFها: گزارش حسابرس (نوع اظهارنظر، تأکید، ابهام، تداوم فعالیت، عدم رعایت، موسسه)، یادداشت‌ها، کنترل داخلی، گزارش تفسیری (ESG، خوانایی، لحن).
- `--ocr` فقط برای PDFهای اسکن‌شده و فقط چند صفحهٔ اول (پیش‌فرض ۸). برای یادداشت‌ها `--ocr-pages 40` (خیلی کندتر).
آزمایش OCR روی یک فایل: `--ocr-test فایل.pdf --tesseract-cmd "..."`.

## ۷) مجموعه‌داده صورت‌های مالی از اکسل‌ها
```
python rohi_collect.py --symbols my_symbols.csv --export-fs
```
خروجی: `fs_codal_long.csv` و `fs_codal_wide.csv` (سود و زیان، سود و زیان جامع، وضعیت مالی، جریان نقدی؛ میلیون ریال).

## ۸) خروجی نهایی
```
python rohi_collect.py --symbols my_symbols.csv --build
```
خروجی‌ها در `out_codal`: `features_firm_year.csv/.xlsx` (همهٔ متغیرها)، `coverage_by_firm_year.csv`، `board_members.csv`، `letters_index.csv`، `shareholders_snapshot.csv`.
بعد از آن فایل `features_firm_year.xlsx` را بفرستید تا به پنل تحلیل وصل شود.

## نکته‌ها
- وسط کار می‌توانید ببندید؛ همان دستور را دوباره بزنید و ادامه می‌دهد (پیشرفت در `out_codal\firms` و فایل‌ها در `codal_files`). این پوشه‌ها را پاک نکنید.
- اگر برنامه با خطای فایل وضعیت خراب مواجه شد، آن را کنار می‌گذارد و دوباره می‌سازد.
- `--inspect نماد` برای بررسی یک شرکت، `--pdf-check` برای اینکه PDFها متن دارند یا عکس‌اند.
- گزارش هیئت‌مدیره (PDF جدا) از ۱۴۰۱ به بعد معمولاً فایل ندارد؛ محتوایش در اکسل (گزارش تفسیری) است.
