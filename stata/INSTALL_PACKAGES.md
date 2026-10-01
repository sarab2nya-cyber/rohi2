# نصب بسته‌های Stata بدون اینترنت و بدون Java

## علت خطای `Java installation not found r(5004)`

Stata 17 برای دانلود از اینترنت (دستورهای `ssc install` و `net install` با آدرس https) از Java داخلی خودش استفاده می‌کند. در نصب شما Java وجود ندارد یا خراب است، بنابراین هیچ دانلودی از داخل Stata انجام نمی‌شود. این مشکل به کد پروژه ربطی ندارد.

راه ساده این است که بسته‌ها را از یک پوشه محلی نصب کنید. همه بسته‌های لازم در پوشه `stata_pkgs` همین پروژه آماده‌اند.

## مراحل نصب (یک بار کافی است)

1. فایل `stata_pkgs.zip` را روی Desktop از حالت فشرده خارج کنید. پوشه‌ای که داخلش زیرپوشه‌های `ftools`، `reghdfe`، `estout` و بقیه هست باید در یکی از این دو مسیر باشد:
   - `C:\Users\Rohi\Desktop\stata_pkgs`
   - `C:\Users\Rohi\Desktop\stata_pkgs\stata_pkgs` (اگر Windows پوشه را دوبار تو در تو ساخته باشد؛ اسکریپت این حالت را هم پیدا می‌کند)
2. فایل **`00_install_packages.do`** را یک بار اجرا کنید. در پایان باید این پیام را ببینید:
   `All required packages are installed and working.`
3. بعد فایل اصلی `01_master_CSD_MA_InvEff.do` را اجرا کنید. این فایل هم همین بررسی را در ابتدا انجام می‌دهد.

اگر پوشه را جای دیگری گذاشتید، مسیر `global PKGDIR` را در هر دو فایل اصلاح کنید. **از `/` استفاده کنید، نه `\`**، مثلاً:
```stata
global PKGDIR "D:/MyFiles/stata_pkgs"
```

## نصب دستی (اختیاری)

```stata
sysdir set PLUS "C:/Users/Rohi/Desktop/plus"
local D "C:/Users/Rohi/Desktop/stata_pkgs"
foreach p in ftools require reghdfe estout xtabond2 boottest {
    net install `p', from("`D'/`p'") replace
}
ftools, compile
reghdfe, compile
sysuse auto, clear
reghdfe price weight, absorb(rep78)
```

> چرا `/`؟ در Stata، اگر بک‌اسلش (`\`) دقیقاً قبل از یک ماکرو بیاید، ماکرو باز نمی‌شود. خطای «Local copy … not found» در نسخه قبلی به همین دلیل بود. Stata در Windows مسیرهای با `/` را بدون مشکل می‌پذیرد.

## نکات

- `winsor2` دیگر لازم نیست، چون do-file یک نسخه داخلی از آن دارد. `coefplot` هم استفاده نمی‌شود.
- `xtabond2` و `boottest` اختیاری‌اند و فقط در بخش آزمون‌های استحکام به کار می‌روند. اگر نصب نشوند، همان بخش‌ها رد می‌شوند و بقیه اسکریپت اجرا می‌شود.
- اگر بعداً خواستید Java را درست کنید تا `ssc install` کار کند، Java 11 یا 17 (مثلاً Eclipse Temurin) را نصب کنید. بعد در Stata دستور زیر را اجرا کنید (مسیر را با مسیر نصب خودتان جایگزین کنید). برای این پروژه لازم نیست.
  ```stata
  set java_home "C:\Program Files\Eclipse Adoptium\jdk-17...\"
  ```
- منابع بسته‌ها: reghdfe/ftools/require از Sergio Correia، estout از Ben Jann، xtabond2/boottest از David Roodman (نسخه‌های GitHub).
