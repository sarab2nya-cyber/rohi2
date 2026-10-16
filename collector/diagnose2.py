# -*- coding: utf-8 -*-
"""
تشخیص مرحله ۲ (روی سیستم شما، فیلترشکن خاموش):
  - پیوست‌ها و گزارش هیئت مدیره/حسابرس/کنترل داخلی چطور دانلود می‌شوند
  - ساختار اکسل کدال، کلیدهای کامل قیمت روزانه TSETMC، سهامداران تاریخی، شاخص‌های صنعت
  - طبقه‌بندی LetterCode روی چند شرکت و ۱۳۹۴–۱۴۰۴
  - سرعت واقعی درخواست‌ها
اجرا:  python diagnose2.py
خروجی: پوشه diag2_out (زیپ کنید و بفرستید؛ حجم معمولاً چند مگابایت)
"""
import os, re, io, json, time, csv, zipfile, collections
from urllib.parse import quote
import requests

OUT = "diag2_out"; os.makedirs(OUT, exist_ok=True)
H = {"User-Agent": "Mozilla/5.0 (research; academic use)", "Accept": "*/*"}
LOG = io.open(os.path.join(OUT, "diag2_report.txt"), "w", encoding="utf-8")
CAP = 4_000_000                                         # سقف حجم هر نمونه دانلودی (۴ مگابایت)

def log(*a):
    s = " ".join(str(x) for x in a); LOG.write(s + "\n"); LOG.flush()
    try: print(s)
    except UnicodeEncodeError: print(s.encode("ascii", "replace").decode())

def get(url, params=None, stream=False, timeout=30):
    t0 = time.time()
    try:
        r = requests.get(url, params=params, headers=H, timeout=(10, timeout), stream=stream)
        return r, time.time() - t0
    except Exception as e:
        log("   خطا:", type(e).__name__, str(e)[:140]); return None, time.time() - t0

def save(name, data):
    with open(os.path.join(OUT, name), "wb") as f: f.write(data if isinstance(data, bytes) else data.encode("utf-8"))

def search(sym, frm="1394/01/01", to="1404/12/29", pages=99):
    out, page = [], 1
    while page <= pages:
        p = {"Symbol": sym, "Length": "-1", "LetterType": "-1", "Category": "-1", "PageNumber": str(page), "search": "true",
             "Publisher": "false", "Mains": "true", "Childs": "true", "TracingNo": "-1", "AuditorRef": "-1", "CompanyState": "0",
             "CompanyType": "-1", "FromDate": frm, "ToDate": to}
        r, dt = get("https://search.codal.ir/api/search/v2/q", params=p)
        if r is None or r.status_code != 200: break
        j = r.json(); L = j.get("Letters") or []
        out += L
        if page >= int(j.get("Page", page)) or not L: break
        page += 1; time.sleep(1.0)
    return out

def candidates(u, base="https://codal.ir"):
    if u.startswith("http"): return [u]
    u2 = u.lstrip("/")
    return [f"{base}/{u2}", f"{base}/Reports/{u2}"]

def fetch_file(u, tag):
    """چند آدرس ممکن را می‌آزماید؛ ابتدای فایل (تا CAP) را ذخیره می‌کند"""
    for c in candidates(u):
        r, dt = get(c, stream=True)
        if r is None: continue
        head = next(r.iter_content(chunk_size=CAP), b"")
        ct = r.headers.get("Content-Type"); cd = r.headers.get("Content-Disposition")
        log(f"   [{tag}] {c[:90]} -> {r.status_code} | {ct} | {cd} | شروع={head[:6]!r} | طول={r.headers.get('Content-Length')} | {dt:.1f}s")
        if r.status_code == 200 and head:
            ext = "pdf" if head[:4] == b"%PDF" else ("zip" if head[:2] == b"PK" else "bin")
            save(f"{tag}.{ext}", head); return c, head
    return None, b""

log("=== تشخیص ۲ ===", time.strftime("%Y-%m-%d %H:%M:%S"))
# ---------------- ۱) طبقه‌بندی LetterCode روی چند شرکت ----------------
log("\n--- ۱) طبقه‌بندی LetterCode (۳ شرکت، ۱۳۹۴–۱۴۰۴) ---")
codes = collections.defaultdict(lambda: [0, ""]); allL = {}
for sym in ("فمراد", "لابسا", "فولاد"):
    L = search(sym); allL[sym] = L
    log(sym, "تعداد نامه:", len(L))
    for x in L:
        c = (x.get("LetterCode") or "").strip(); codes[c][0] += 1
        if not codes[c][1]: codes[c][1] = (x.get("Title") or "")[:90]
with io.open(os.path.join(OUT, "lettercodes.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(["LetterCode", "count", "example_title"])
    for c, (n, t) in sorted(codes.items(), key=lambda kv: -kv[1][0]): w.writerow([c, n, t])
log("تعداد کدهای متفاوت:", len(codes), "(lettercodes.csv)")
titles = sorted({(x.get("Title") or "") for L in allL.values() for x in L})
save("all_titles.txt", "\n".join(titles))
# عنوان‌های صورت مالی سالانه لابسا (سال مالی اسفند)
lab = [x for x in allL.get("لابسا", []) if "صورت" in (x.get("Title") or "") and "سال مالی" in (x.get("Title") or "")][:6]
for x in lab: log("   لابسا:", x.get("PublishDateTime"), "|", x.get("LetterCode"), "|", x.get("Title"))

# ---------------- ۲) نمونه نامه‌های کلیدی ----------------
log("\n--- ۲) دانلود نمونه نامه‌های کلیدی (فمراد) ---")
FM = allL.get("فمراد", [])
def pick(pred): return next((x for x in FM if pred(x)), None)
samples = {
  "annual_audited_FS": pick(lambda x: x.get("LetterCode") == "ن-۱۰" and "سال مالی" in (x.get("Title") or "") and "حسابرسی شده" in (x.get("Title") or "")),
  "board_report": pick(lambda x: x.get("LetterCode") == "ن-۱۱"),
  "internal_control": pick(lambda x: x.get("LetterCode") == "ن-۱۲"),
  "audit_opinion_capinc": pick(lambda x: x.get("LetterCode") == "ن-۶۱"),
}
for tag, x in samples.items():
    log(f"\n## {tag}:", (x or {}).get("Title"))
    if not x: continue
    log("   TracingNo:", x.get("TracingNo"), "| HasHtml:", x.get("HasHtml"), "HasPdf:", x.get("HasPdf"), "HasExcel:", x.get("HasExcel"), "HasAttachment:", x.get("HasAttachment"))
    # صفحه HTML (Decision یا Attachment)
    u = x.get("Url") or ""
    pg = None
    if u:
        for c in candidates(u):
            r, dt = get(c)
            if r is not None and r.status_code == 200:
                pg = r.text; save(f"{tag}_page.html", pg[:3_000_000]); log(f"   صفحه: {c[:80]} حجم {len(r.content)} در {dt:.1f}s")
                log("   datasource دارد:", bool(re.search(r"var\s+datasource\s*=", pg)))
                hrefs = sorted(set(re.findall(r'href=["\']([^"\']+)["\']', pg)))
                keep = [h for h in hrefs if re.search(r"(?i)download|attachment|\.pdf|\.docx?|\.xlsx?|\.zip|\.rar|file", h)]
                log("   لینک‌های پیوست/فایل در صفحه:", keep[:12])
                if "Attachment.aspx" in c and keep:
                    for i, h in enumerate(keep[:2]):
                        fetch_file(h if h.startswith("http") else ("https://codal.ir/Reports/" + h.lstrip("/")) , f"{tag}_att{i}")
                break
    if x.get("PdfUrl"): fetch_file(x["PdfUrl"], f"{tag}_pdf")
    if x.get("ExcelUrl"):
        c, head = fetch_file(x["ExcelUrl"], f"{tag}_excel")
        if head[:2] == b"PK":
            try:
                z = zipfile.ZipFile(io.BytesIO(head)); wbx = [n for n in z.namelist() if n.endswith("workbook.xml")]
                if wbx:
                    names = re.findall(rb'<sheet [^>]*name="([^"]+)"', z.read(wbx[0])); log("   نام شیت‌های اکسل:", [n.decode("utf-8", "replace") for n in names][:40])
            except Exception as e: log("   (اکسل ناقص برای خواندن شیت‌ها؛ حجم سقف ۴MB)", str(e)[:60])

# ---------------- ۳) TSETMC ----------------
log("\n--- ۳) TSETMC (فمراد: 18004480270695404) ---")
ins = "18004480270695404"
r, dt = get(f"https://cdn.tsetmc.com/api/Instrument/GetInstrumentInfo/{ins}")
if r is not None and r.status_code == 200:
    save("tse_instrumentInfo.json", r.content); log("اطلاعات نماد:", r.text[:900])
r, dt = get(f"https://cdn.tsetmc.com/api/ClosingPrice/GetClosingPriceDailyList/{ins}/0")
if r is not None and r.status_code == 200:
    j = r.json(); rows = j.get("closingPriceDaily", [])
    log("تاریخچه روزانه:", len(rows), "ردیف | همه کلیدهای یک ردیف:", list(rows[-1].keys()) if rows else None, f"| {dt:.1f}s")
    if rows: log("   نمونه ردیف آخر:", json.dumps(rows[-1], ensure_ascii=False)[:600]); save("tse_daily_last10.json", json.dumps(rows[-10:], ensure_ascii=False))
for d in ("20240320", "20230321"):
    for name, u in {"سهامداران در تاریخ": f"https://cdn.tsetmc.com/api/Shareholder/GetInstrumentShareHolder/{ins}/{d}",
                    "سهامداران تاریخی (روش ۲)": f"https://cdn.tsetmc.com/api/Shareholder/GetShareHolderHistory/{ins}/{d}"}.items():
        r, dt = get(u)
        if r is not None: log(name, d, "->", r.status_code, "|", r.text[:200].replace("\n", " "))
for name, u in {"فهرست شاخص‌ها": "https://cdn.tsetmc.com/api/Index/GetIndexB1LastAll/All/1",
                "فهرست صنایع": "https://cdn.tsetmc.com/api/StaticData/GetStaticData"}.items():
    r, dt = get(u)
    if r is not None:
        log(name, "->", r.status_code, "حجم", len(r.content)); save("tse_" + re.sub(r"\W+", "_", name) + ".json", r.content[:300000])
        log("   ابتدا:", r.text[:300].replace("\n", " "))

# ---------------- ۴) سرعت ----------------
log("\n--- ۴) سرعت واقعی ---")
ts = []
for i in range(1, 9):
    r, dt = get("https://search.codal.ir/api/search/v2/q", params={"Symbol": "لابسا", "Length": "-1", "LetterType": "-1", "Category": "-1", "PageNumber": str(i), "search": "true", "Publisher": "false", "Mains": "true", "Childs": "true", "TracingNo": "-1", "AuditorRef": "-1", "CompanyState": "0", "CompanyType": "-1", "FromDate": "1394/01/01", "ToDate": "1404/12/29"})
    ts.append(dt)
    if r is not None: log(f"   جست‌وجو صفحه {i}: {r.status_code} در {dt:.2f}s")
x = samples.get("annual_audited_FS")
if x:
    for i in range(5):
        r, dt = get(("https://codal.ir" + x["Url"]) if x["Url"].startswith("/") else x["Url"]); ts.append(dt)
        if r is not None: log(f"   صفحه صورت مالی #{i+1}: {r.status_code} حجم {len(r.content)} در {dt:.2f}s")
if ts: log("میانگین زمان درخواست: %.2f ثانیه (n=%d)" % (sum(ts) / len(ts), len(ts)))
log("\nپایان. پوشه", os.path.abspath(OUT), "را زیپ و بفرستید.")
LOG.close()
