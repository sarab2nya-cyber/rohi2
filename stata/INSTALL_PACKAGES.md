# نصب بسته‌های Stata بدون اینترنت و بدون Java

## علت خطای `Java installation not found r(5004)`

Stata 17 برای دانلود از اینترنت (دستورهای `ssc install` و `net install` با آدرس https) از Java داخلی خودش استفاده می‌کند. در نصب شما Java وجود ندارد یا خراب است، بنابراین هیچ دانلودی از داخل Stata انجام نمی‌شود. این مشکل به کد پروژه ربطی ندارد.

راه ساده این است که بسته‌ها را از یک پوشه محلی نصب کنید. همه بسته‌های لازم در پوشه `stata_pkgs` همین پروژه آماده‌اند.

## مراحل نصب (یک بار کافی است)

1. فایل zip پروژه را باز کنید و پوشه `stata_pkgs` را در این مسیر کپی کنید:
   `C:\Users\Rohi\Desktop\stata_pkgs`
   داخل این پوشه باید زیرپوشه‌های `ftools`، `require`، `reghdfe`، `estout`، `xtabond2` و `boottest` باشند.

2. فایل `01_master_CSD_MA_InvEff.do` را اجرا کنید. اسکریپت خودش بسته‌ها را از این پوشه نصب می‌کند و برای این کار به اینترنت نیاز ندارد.

اگر پوشه را جای دیگری گذاشتید، در بخش 0 do-file این خط را اصلاح کنید:
```stata
global PKGDIR    "C:\Users\Rohi\Desktop\stata_pkgs"
```

## نصب دستی (اختیاری)

اگر خواستید بسته‌ها را جدا از اسکریپت نصب کنید، این دستورها را در پنجره Command اجرا کنید:

```stata
sysdir set PLUS "C:\Users\Rohi\Desktop\plus"
local D "C:\Users\Rohi\Desktop\stata_pkgs"
foreach p in ftools require reghdfe estout xtabond2 boottest {
    net install `p', from("`D'\\`p'") replace
}
ftools, compile
reghdfe, compile
```

برای بررسی نصب، این را اجرا کنید. باید یک جدول رگرسیون نمایش داده شود:

```stata
sysuse auto, clear
reghdfe price weight, absorb(rep78)
```

## نکات

- `winsor2` دیگر لازم نیست، چون do-file یک نسخه داخلی از آن دارد. `coefplot` هم استفاده نمی‌شود.
- `xtabond2` و `boottest` اختیاری‌اند و فقط در بخش آزمون‌های استحکام به کار می‌روند. اگر نصب نشوند، همان بخش‌ها رد می‌شوند و بقیه اسکریپت اجرا می‌شود.
- اگر بعداً خواستید Java را درست کنید تا `ssc install` کار کند، Java 11 یا 17 (مثلاً Eclipse Temurin) را نصب کنید. بعد در Stata دستور زیر را اجرا کنید (مسیر را با مسیر نصب خودتان جایگزین کنید). برای این پروژه لازم نیست.
  ```stata
  set java_home "C:\Program Files\Eclipse Adoptium\jdk-17...\"
  ```
- منابع بسته‌ها: reghdfe/ftools/require از Sergio Correia، estout از Ben Jann، xtabond2/boottest از David Roodman (نسخه‌های GitHub).
