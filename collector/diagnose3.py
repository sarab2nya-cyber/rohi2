# -*- coding: utf-8 -*-
"""
تشخیص ۳ (بسیار آهسته و مؤدب؛ حدود ۱۵ درخواست به کدال با فاصله ۵–۸ ثانیه، و چند درخواست به TSETMC).
پیش از اجرا: ۳۰–۶۰ دقیقه از آخرین اجرا صبر کنید؛ در مرورگر codal.ir را باز کنید و اگر کپچا خواست حل کنید.
اگر وسط کار کپچا/۴۲۹ دید، همان‌جا متوقف می‌شود (دور زدن نمی‌کند).
اجرا: python diagnose3.py          خروجی: diag3_out  (زیپ و بفرستید)
"""
import os, re, io, json, time, random
import requests

OUT = "diag3_out"; os.makedirs(OUT, exist_ok=True)
H = {"User-Agent": "Mozilla/5.0 (research; academic use)", "Accept": "*/*"}
LOG = io.open(os.path.join(OUT, "diag3_report.txt"), "w", encoding="utf-8")
CAP = 4_000_000
class Stop(Exception): pass

def log(*a):
    s = " ".join(str(x) for x in a); LOG.write(s + "\n"); LOG.flush()
    try: print(s)
    except UnicodeEncodeError: print(s.encode("ascii", "replace").decode())

def polite(lo=5.0, hi=8.0): time.sleep(random.uniform(lo, hi))

def is_captcha(r):
    if r.status_code == 429: return True
    t = r.text[:6000] if "text" in dir(r) else ""
    return ("تأیید کاربر" in t) or ("captcha" in t.lower())

def cget(url, params=None, stream=False):
    """درخواست به کدال؛ در صورت کپچا/۴۲۹ فوراً متوقف می‌شود"""
    polite()
    try:
        r = requests.get(url, params=params, headers=H, timeout=(10, 40), stream=stream)
    except Exception as e:
        log("   خطا:", type(e).__name__, str(e)[:120]); return None
    ct = r.headers.get("Content-Type", "")
    if r.status_code == 429 or ("html" in ct and not stream and is_captcha(r)):
        log("   !!! کپچا/۴۲۹ دیده شد (%s) → توقف. ۱ ساعت صبر کنید و در مرورگر کپچا را حل کنید." % r.status_code); raise Stop()
    return r

def save(name, data):
    with open(os.path.join(OUT, name), "wb") as f: f.write(data if isinstance(data, bytes) else data.encode("utf-8"))

def search(sym, **kw):
    p = {"Symbol": sym, "Length": "-1", "LetterType": "-1", "Category": "-1", "PageNumber": "1", "search": "true", "Publisher": "false",
         "Mains": "true", "Childs": "true", "TracingNo": "-1", "AuditorRef": "-1", "CompanyState": "0", "CompanyType": "-1",
         "FromDate": "1398/01/01", "ToDate": "1404/12/29"}; p.update(kw)
    r = cget("https://search.codal.ir/api/search/v2/q", params=p)
    return r.json() if r is not None and r.status_code == 200 else {}

log("=== تشخیص ۳ ===", time.strftime("%Y-%m-%d %H:%M:%S"))
try:
    # ---- ۱) فیلتر LetterType در جست‌وجو (برای کاهش تعداد صفحه‌ها)
    log("\n--- ۱) آیا فیلتر LetterType کار می‌کند؟ ---")
    j = search("لابسا", LetterType="6")
    L = j.get("Letters") or []
    log("لابسا با LetterType=6 → کل:", j.get("Total"), "صفحه‌ها:", j.get("Page"), "| عنوان‌های ۸ نامه اول:")
    for x in L[:8]: log("   ", x.get("LetterCode"), "|", (x.get("Title") or "")[:90])
    # ---- ۲) صفحه Decision صورت مالی سالانه حسابرسی‌شده
    log("\n--- ۲) صفحه HTML صورت مالی سالانه (ساختار داده و اطلاعات حسابرس) ---")
    fs = next((x for x in L if "سال مالی" in (x.get("Title") or "") and "حسابرسی شده" in (x.get("Title") or "") and "تلفیقی" in (x.get("Title") or "")), None) \
         or next((x for x in L if "سال مالی" in (x.get("Title") or "") and "حسابرسی شده" in (x.get("Title") or "")), None)
    if fs:
        log("   نامه:", fs.get("Title"), "| TracingNo", fs.get("TracingNo"))
        r = cget("https://codal.ir" + fs["Url"])
        if r is not None:
            log("   صفحه Decision: وضعیت", r.status_code, "حجم", len(r.content)); save("FS_decision_page.html", r.text[:3_000_000])
            m = re.search(r"var\s+datasource\s*=\s*(\{.*?\});\s*(?:var|</script>)", r.text, re.S)
            log("   datasource:", bool(m))
            if m:
                try:
                    ds = json.loads(m.group(1)); log("   عنوان شیت‌ها:", [(s.get("title") or s.get("code")) for s in ds.get("sheets", [])][:60])
                    save("FS_datasource.json", json.dumps(ds, ensure_ascii=False)[:2_500_000])
                except Exception as e: log("   JSON datasource خوانده نشد:", str(e)[:80])
            for kw in ("حسابرس", "اظهارنظر", "حق الزحمه", "حق‌الزحمه", "بازرس"):
                log("   تعداد «%s» در صفحه:" % kw, r.text.count(kw))
        # اکسل
        if fs.get("ExcelUrl"):
            r = cget(fs["ExcelUrl"], stream=True)
            if r is not None and r.status_code == 200:
                b = next(r.iter_content(chunk_size=CAP), b""); save("FS_excel.bin", b); log("   اکسل:", len(b), "بایت")
    # ---- ۳) نامه‌های ساختاریافته: کمیته حسابرسی (ن-۴۱) و تغییر هیئت‌مدیره (ن-۴۵)
    log("\n--- ۳) نامه‌های ن-۴۱ و ن-۴۵ و کمیته ریسک (فمراد) ---")
    for tag, kw in (("N41_audit_committee", dict(Category="-1")), ):
        j = search("فمراد", FromDate="1400/01/01")
        for x in (j.get("Letters") or []):
            pass
    j = search("فمراد", FromDate="1400/01/01"); pool = j.get("Letters") or []
    for p in (2, 3):
        jj = search("فمراد", FromDate="1400/01/01", PageNumber=str(p)); pool += jj.get("Letters") or []
    want = {"N41": "ن-۴۱", "N45": "ن-۴۵", "N86": "ن-۸۶", "N11_board_report": "ن-۱۱", "N12_internal_control": "ن-۱۲"}
    for tag, code in want.items():
        x = next((y for y in pool if (y.get("LetterCode") or "").strip() == code), None)
        log("\n##", tag, ":", (x or {}).get("Title"))
        if not x: continue
        r = cget("https://codal.ir" + x["Url"])
        if r is None: continue
        log("   HTML: وضعیت", r.status_code, "حجم", len(r.content), "| HasHtml", x.get("HasHtml"), "| HasAttachment", x.get("HasAttachment"))
        save(f"{tag}_page.html", r.text[:2_000_000])
        m = re.search(r"var\s+datasource\s*=\s*(\{.*?\});\s*(?:var|</script>)", r.text, re.S)
        log("   datasource:", bool(m))
        links = sorted(set(re.findall(r'href=["\']([^"\']+)["\']', r.text)))
        log("   لینک‌های فایل در صفحه:", [l for l in links if re.search(r"(?i)download|attachment|\.pdf|\.docx?|\.xlsx?|\.zip|file", l)][:10])
    # ---- ۴) اکسل سال قدیمی‌تر (گزارش تفسیری کی شروع شده؟)
    log("\n--- ۴) آیا اکسل سال‌های قدیمی‌تر هم گزارش تفسیری دارد؟ (لابسا ۱۳۹۸) ---")
    j = search("لابسا", LetterType="6", FromDate="1398/01/01", ToDate="1399/12/29"); LL = j.get("Letters") or []
    old = next((x for x in LL if "سال مالی" in (x.get("Title") or "") and "حسابرسی شده" in (x.get("Title") or "") and x.get("ExcelUrl")), None)
    log("   نامه:", (old or {}).get("Title"))
    if old:
        r = cget(old["ExcelUrl"], stream=True)
        if r is not None and r.status_code == 200:
            b = next(r.iter_content(chunk_size=CAP), b""); t = b.decode("utf-8", "replace"); save("FS_excel_1398.bin", b)
            log("   اکسل ۱۳۹۸:", len(b), "بایت | عنوان‌ها:", re.findall(r"<h3>\s*(.*?)\s*</h3>", t, re.S)[:20])
except Stop:
    log("\nبخش کدال متوقف شد (کپچا). خروجی تا همین‌جا را بفرستید.")

# ---------------- TSETMC (بدون کپچا؛ فاصله ۱ ثانیه) ----------------
log("\n--- TSETMC: آدرس‌های ممکن برای سهامداران تاریخی و شاخص صنعت ---")
ins = "18004480270695404"
def tget(u):
    time.sleep(1.0)
    try:
        r = requests.get(u, headers=H, timeout=(10, 30)); return r
    except Exception as e: log("   خطا:", type(e).__name__); return None
cands = {
 "ShareHolder/GetInstrumentShareHolderLast": f"https://cdn.tsetmc.com/api/Shareholder/GetInstrumentShareHolderLast/{ins}",
 "ShareHolder history A": f"https://cdn.tsetmc.com/api/Shareholder/GetInstrumentShareHolderHistory/{ins}",
 "ShareHolder history B": f"https://cdn.tsetmc.com/api/Shareholder/GetInstrumentShareHolderAtDate/{ins}/20240320",
 "ShareHolder history C": f"https://cdn.tsetmc.com/api/Shareholder/GetShareHolder/{ins}/20240320",
 "ShareChange (افزایش سرمایه)": f"https://cdn.tsetmc.com/api/Instrument/GetInstrumentShareChange/{ins}",
 "ClientType (حقیقی/حقوقی)": f"https://cdn.tsetmc.com/api/ClientType/GetClientTypeAll/{ins}/1/0",
 "Identity": f"https://cdn.tsetmc.com/api/Instrument/GetInstrumentIdentity/{ins}",
 "Holder": f"https://cdn.tsetmc.com/api/Instrument/GetInstrumentHolder/{ins}",
}
for name, u in cands.items():
    r = tget(u)
    if r is not None:
        log(name, "->", r.status_code, "حجم", len(r.content), "|", r.text[:200].replace("\n", " "))
        if r.status_code == 200: save("tse_" + re.sub(r"\W+", "_", name) + ".json", r.content[:200000])
# شاخص صنعت: اولین شاخص صنعتی از فهرست
r = tget("https://cdn.tsetmc.com/api/Index/GetIndexB1LastAll/All/1")
if r is not None and r.status_code == 200:
    idx = r.json().get("indexB1", []); log("تعداد شاخص‌ها:", len(idx), "| نمونه نام‌ها:", [i.get("lVal30") for i in idx[:12]])
    save("tse_index_names.json", json.dumps([{"insCode": i.get("insCode"), "name": i.get("lVal30")} for i in idx], ensure_ascii=False))
    metal = next((i for i in idx if "فلزات" in (i.get("lVal30") or "")), idx[0] if idx else None)
    if metal:
        r2 = tget(f"https://cdn.tsetmc.com/api/Index/GetIndexB2History/{metal['insCode']}")
        if r2 is not None: log("تاریخچه", metal.get("lVal30"), "->", r2.status_code, "حجم", len(r2.content), r2.text[:160].replace("\n", " "))
log("\nپایان. پوشه", os.path.abspath(OUT), "را زیپ و بفرستید.")
LOG.close()
