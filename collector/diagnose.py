# -*- coding: utf-8 -*-
"""
برنامه تشخیص: آزمون endpointهای کدال و TSETMC روی سیستم شما (داخل ایران، فیلترشکن خاموش).
اجرا:   python diagnose.py            (نماد پیش‌فرض: لابسا = آبسال)
        python diagnose.py فمراد
خروجی: پوشه diag_out/ شامل diag_report.txt و چند نمونه کوچک (JSON/HTML/PDF).
پوشه diag_out را زیپ و برای من بفرستید. حجم کل معمولاً کمتر از چند مگابایت است.
"""
import sys, os, json, re, time, io
import requests

SYM = sys.argv[1] if len(sys.argv) > 1 else "لابسا"
OUT = "diag_out"; os.makedirs(OUT, exist_ok=True)
H = {"User-Agent": "Mozilla/5.0 (research; academic use)", "Accept": "application/json, text/html, */*"}
LOG = io.open(os.path.join(OUT, "diag_report.txt"), "w", encoding="utf-8")

def log(*a):
    s = " ".join(str(x) for x in a)
    LOG.write(s + "\n"); LOG.flush()
    try: print(s)
    except UnicodeEncodeError: print(s.encode("ascii", "replace").decode())

def get(url, params=None, stream=False, timeout=25):
    log("   ... در حال اتصال:", url[:80]); t0 = time.time()
    try:
        r = requests.get(url, params=params, headers=H, timeout=(10, timeout), stream=stream)
        log("   ... پاسخ در %.1f ثانیه" % (time.time() - t0)); return r
    except requests.exceptions.ConnectTimeout:
        log("   خطا: ConnectTimeout (۱۰ ثانیه) → سایت از شبکه شما در دسترس نیست (فیلترشکن روشن؟ یا مسدود)")
    except requests.exceptions.ReadTimeout:
        log("   خطا: ReadTimeout → اتصال برقرار شد ولی سایت جواب نداد/کند است")
    except requests.exceptions.SSLError as e:
        log("   خطا: SSL →", str(e)[:120])
    except requests.exceptions.ConnectionError as e:
        log("   خطا: ConnectionError →", str(e)[:150])
    except Exception as e:
        log("   خطا:", type(e).__name__, str(e)[:150])
    return None

def save(name, data, binary=False):
    p = os.path.join(OUT, name)
    with open(p, "wb" if binary else "w", **({} if binary else {"encoding": "utf-8"})) as f: f.write(data)
    return p

log("=== تشخیص اتصال ===", time.strftime("%Y-%m-%d %H:%M:%S"), "نماد:", SYM)
for u in ("https://codal.ir", "https://search.codal.ir", "https://cdn.tsetmc.com", "https://old.tsetmc.com"):
    r = get(u, timeout=15); log("پینگ", u, "->", r.status_code if r is not None else "ناموفق")

# ---------------- کدال: جست‌وجو ----------------
log("\n=== کدال: جست‌وجوی نامه‌ها ===")
base = {"Symbol": SYM, "Length": "-1", "LetterType": "-1", "Category": "-1", "PageNumber": "1", "search": "true",
        "Publisher": "false", "Mains": "true", "Childs": "true", "TracingNo": "-1", "AuditorRef": "-1",
        "CompanyState": "0", "CompanyType": "-1", "FromDate": "1402/01/01", "ToDate": "1404/12/29"}
variants = {"کامل": base, "بدون تاریخ": {k: v for k, v in base.items() if k not in ("FromDate", "ToDate")},
            "فقط نماد": {"Symbol": SYM, "search": "true", "PageNumber": "1", "Length": "-1"}}
letters = None
for name, p in variants.items():
    r = get("https://search.codal.ir/api/search/v2/q", params=p)
    if r is None: continue
    log("وضعیت", name, "->", r.status_code, "طول پاسخ:", len(r.content))
    if r.status_code == 200:
        try:
            j = r.json()
        except Exception as e:
            log("   پاسخ JSON نیست:", r.text[:200].replace("\n", " ")); continue
        log("   کلیدهای سطح بالا:", list(j.keys())[:12])
        L = j.get("Letters") or []
        log("   تعداد نامه‌ها:", len(L), "| Total:", j.get("Total"), "| Page:", j.get("Page"))
        if L and letters is None:
            letters = L; save("codal_search_first20.json", json.dumps(L[:20], ensure_ascii=False, indent=1))
            log("   کلیدهای یک نامه:", list(L[0].keys()))
            for x in L[:12]: log("     ", x.get("PublishDateTime"), "|", x.get("TracingNo"), "|", (x.get("Title") or "")[:90])
        if L: break

# ---------------- کدال: یک صفحه نامه و پیوست ----------------
log("\n=== کدال: صفحه نامه و پیوست ===")
if letters:
    pick = next((x for x in letters if re.search(r"صورت|مالی|حسابرس", x.get("Title") or "")), letters[0])
    log("نامه انتخابی:", pick.get("TracingNo"), (pick.get("Title") or "")[:100])
    for k in ("Url", "PdfUrl", "AttachmentUrl", "ExcelUrl", "XbrlUrl", "HasPdf", "HasExcel", "HasXbrl", "HasHtml", "HasAttachment"):
        log("   ", k, "=", pick.get(k))
    u = pick.get("Url") or ""
    if u:
        r = get(u if u.startswith("http") else "https://codal.ir" + u)
        if r is not None:
            log("   صفحه نامه: وضعیت", r.status_code, "حجم", len(r.content))
            save("codal_letter_page.html", r.text)
            log("   متغیر datasource دارد؟", bool(re.search(r"var\s+datasource\s*=", r.text)))
            log("   لینک‌های پیوست در صفحه:", sorted(set(re.findall(r'href="([^"]*(?:Attachment|\.pdf|\.xlsx?|GetFile|Download)[^"]*)"', r.text)))[:10])
    pu = pick.get("PdfUrl") or pick.get("AttachmentUrl")
    if pu:
        r = get(pu if pu.startswith("http") else "https://codal.ir" + pu, stream=True)
        if r is not None:
            head = next(r.iter_content(chunk_size=5_000_000), b"")
            log("   PDF/پیوست: وضعیت", r.status_code, "| نوع", r.headers.get("Content-Type"), "| ابتدای فایل", head[:8], "| طول", r.headers.get("Content-Length"))
            if r.status_code == 200: save("codal_attachment_sample.bin", head, binary=True)
    # دسته‌بندی عنوان‌ها: همه عنوان‌های دیده‌شده برای من
    titles = sorted(set((x.get("Title") or "")[:80] for x in letters))
    save("codal_titles_seen.txt", "\n".join(titles))
    log("   تعداد عنوان‌های یکتا:", len(titles), "(ذخیره در codal_titles_seen.txt)")
else:
    log("هیچ نامه‌ای نیامد: فیلترشکن را خاموش کنید و دوباره اجرا کنید؛ یا نام نماد درست نیست.")

# ---------------- TSETMC ----------------
log("\n=== TSETMC ===")
ins = None
r = get("https://cdn.tsetmc.com/api/Instrument/GetInstrumentSearch/" + SYM)
if r is not None:
    log("جست‌وجوی نماد: وضعیت", r.status_code)
    try:
        j = r.json(); save("tse_search.json", json.dumps(j, ensure_ascii=False, indent=1)[:20000])
        log("   کلیدها:", list(j.keys())[:10] if isinstance(j, dict) else type(j))
        items = (j.get("instrumentSearch") if isinstance(j, dict) else None) or []
        if items:
            log("   نمونه نتیجه:", {k: items[0].get(k) for k in list(items[0].keys())[:8]})
            ins = items[0].get("insCode")
    except Exception as e: log("   JSON نیست:", r.text[:150])
log("InsCode پیدا شده:", ins)
if ins:
    tests = {"اطلاعات نماد": f"https://cdn.tsetmc.com/api/Instrument/GetInstrumentInfo/{ins}",
             "تاریخچه روزانه": f"https://cdn.tsetmc.com/api/ClosingPrice/GetClosingPriceDailyList/{ins}/0",
             "سهامداران آخر": f"https://cdn.tsetmc.com/api/Shareholder/GetInstrumentShareHolderLast/{ins}"}
    for name, u in tests.items():
        r = get(u)
        if r is None: continue
        log(name, "-> وضعیت", r.status_code, "حجم", len(r.content))
        try:
            j = r.json(); save("tse_" + re.sub(r"\W+", "_", name) + ".json", json.dumps(j, ensure_ascii=False)[:60000])
            if isinstance(j, dict):
                log("   کلیدها:", list(j.keys())[:10])
                for k, v in j.items():
                    if isinstance(v, list) and v: log("   ", k, "-> تعداد", len(v), "| کلیدهای یک ردیف:", list(v[0].keys())[:14] if isinstance(v[0], dict) else v[0]); break
        except Exception: log("   JSON نیست:", r.text[:120].replace("\n", " "))
    # شاخص کل (TEDPIX): کد شناخته‌شده؛ چند نشانی را می‌آزماییم
    for name, u in {"شاخص کل (تاریخچه)": "https://cdn.tsetmc.com/api/Index/GetIndexB2History/32097828799138957",
                    "شاخص کل (تاریخچه 2)": "https://cdn.tsetmc.com/api/Index/GetIndexB1LastAll/All/1"}.items():
        r = get(u)
        if r is not None:
            log(name, "-> وضعیت", r.status_code, "حجم", len(r.content), "| ابتدا:", r.text[:150].replace("\n", " "))
            if r.status_code == 200: save("tse_index_" + re.sub(r"\W+", "_", name) + ".json", r.text[:60000])
log("\nپایان. پوشه", os.path.abspath(OUT), "را زیپ و بفرستید.")
LOG.close()
