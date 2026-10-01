# نصب بسته‌های Stata (برای Stata 16 و 17)

اسکریپت به این بسته‌های غیررسمی نیاز دارد:
`ftools`, `require`, `reghdfe`, `winsor2`, `estout`, `coefplot`, `xtabond2`, `boottest`

خطای `command reghdfe is unrecognized` یعنی `reghdfe` نصب نشده است.

## روش ۱: نصب آنلاین (اگر Stata به اینترنت دسترسی دارد)

این دستورها را یک بار در پنجره Command اجرا کنید:

```stata
sysdir set PLUS "C:\Users\Rohi\Desktop\plus"
ssc install ftools,  replace
ssc install require, replace
ssc install reghdfe, replace
ssc install winsor2, replace
ssc install estout,  replace
ssc install coefplot, replace
ssc install xtabond2, replace
ssc install boottest, replace
ftools, compile
reghdfe, compile
```

اگر `ssc install` خطا داد، `ftools` و `reghdfe` را از GitHub نصب کنید:

```stata
net install ftools,  from("https://raw.githubusercontent.com/sergiocorreia/ftools/master/src/")  replace
net install reghdfe, from("https://raw.githubusercontent.com/sergiocorreia/reghdfe/master/src/") replace
ftools, compile
reghdfe, compile
```

برای بررسی نصب، این را اجرا کنید. باید بدون خطا یک جدول رگرسیون نشان دهد:

```stata
sysuse auto, clear
reghdfe price weight, absorb(rep78)
```

## روش ۲: نصب آفلاین (اگر اینترنت Stata فیلتر یا قطع است)

1. روی یک کامپیوتر که اینترنت دارد، این دو مخزن را دانلود کنید: دکمه سبز **Code** و بعد **Download ZIP**.
   - https://github.com/sergiocorreia/ftools
   - https://github.com/sergiocorreia/reghdfe
2. فایل‌ها را از حالت فشرده خارج کنید، مثلاً در `C:\Users\Rohi\Desktop\pkgs\`.
3. در Stata این دستورها را اجرا کنید:

```stata
sysdir set PLUS "C:\Users\Rohi\Desktop\plus"
net install ftools,  from("C:\Users\Rohi\Desktop\pkgs\ftools-master\src")  replace
net install reghdfe, from("C:\Users\Rohi\Desktop\pkgs\reghdfe-master\src") replace
ftools, compile
reghdfe, compile
```

4. برای بسته‌های دیگر (`winsor2`، `estout`، `coefplot`، `xtabond2`، `boottest`، `require`):
   1. فایل‌های `.ado`، `.sthlp` و `.mata` (اگر دارد) را از آرشیو SSC دانلود کنید. آدرس آرشیو این شکلی است: `http://fmwww.bc.edu/repec/bocode/w/` که حرف آخر آن، حرف اول نام بسته است.
   2. فایل‌ها را مستقیماً در پوشه `C:\Users\Rohi\Desktop\plus` کپی کنید. اسکریپت این پوشه را با `adopath +` به مسیر جستجوی Stata اضافه می‌کند.

## نکته

اسکریپت اصلی حالا در ابتدا خودش نصب را امتحان می‌کند. اگر بسته‌ای هنوز نصب نشده باشد یا `reghdfe` اجرا نشود، با یک پیام واضح متوقف می‌شود. این بهتر از آن است که اجرا وسط کار با خطا قطع شود.
