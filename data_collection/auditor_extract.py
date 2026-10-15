#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
استخراج همه اطلاعات گزارش حسابرس مستقل و بازرس قانونی از پیوست‌های کدال (۱۳۹۰ تا ۱۴۰۴).

نصب:  pip install requests pandas pdfplumber
ورودی: data_out/letters.csv (خروجی rohi_all.py list با --from 1390/01/01 --to 1404/12/29)
مراحل:
  python auditor_extract.py pdf       # دانلود PDF هر نامه (resumable)
  python auditor_extract.py text      # استخراج متن گزارش حسابرس → data_out/report_text/*.txt
  python auditor_extract.py parse     # ویژگی‌ها → data_out/auditor_reports.csv
  python auditor_extract.py panel     # دوره تصدی، تعویض، اندازه، تخصص → data_out/auditor_panel.csv

هشدار: آزمون‌شده فقط روی متن نمونه. نام ستون URL در letters.csv (PdfUrl/AttachmentUrl) و
ساختار واقعی PDFها را با ۲۰ نمونه دستی کنترل کنید. PDFهای اسکن‌شده در data_out/need_ocr.csv می‌آیند.
تمام متن گزارش ذخیره می‌شود تا برای مقاله‌های بعدی بدون دانلود دوباره قابل تحلیل باشد.
"""
import sys, re, time, unicodedata, collections, pathlib, types
import requests, pandas as pd

OUT = pathlib.Path("data_out"); PDF = OUT / "pdf"; TXT = OUT / "report_text"
BASE = "https://codal.ir"; SLEEP = 1.5
H = {"User-Agent": "Mozilla/5.0 (research; academic use)"}
for d in (OUT, PDF, TXT): d.mkdir(exist_ok=True)

_AR = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
def norm(t):
    t = unicodedata.normalize("NFKC", str(t)).translate(_AR)
    t = t.replace("ي", "ی").replace("ك", "ک").replace("‌", " ").replace("‏", "").replace("\xa0", " ")
    return re.sub(r"[ \t]+", " ", t)

def fix_visual(t):
    """بسیاری از PDFهای فارسی متن را معکوس (ترتیب بصری) استخراج می‌کنند؛ تشخیص و اصلاح."""
    t = unicodedata.normalize("NFKC", t)
    if t.count("حسابرس") == 0 and t.count("حسابرس"[::-1]) > 0:
        out = []
        for ln in t.split("\n"):
            r = ln[::-1]
            out.append(re.sub(r"\d+", lambda m: m.group()[::-1], r))
        return "\n".join(out)
    return t

# ---------------------------------------------------------------- دانلود
def pdf_url(row):
    for c in ("PdfUrl", "AttachmentUrl"):
        v = row.get(c)
        if isinstance(v, str) and v.strip():
            return v if v.startswith("http") else BASE + v
    return None

def cmd_pdf(limit=0):
    df = pd.read_csv(OUT / "letters.csv"); n = 0
    for _, r in df.iterrows():
        f = PDF / f"{r['TracingNo']}.pdf"
        if f.exists(): continue
        u = pdf_url(r)
        if not u: continue
        for i in range(4):
            try:
                resp = requests.get(u, headers=H, timeout=60)
                if resp.status_code == 200 and resp.content[:4] == b"%PDF":
                    f.write_bytes(resp.content); break
            except requests.RequestException as e:
                print("خطا", e, file=sys.stderr)
            time.sleep(2 ** (i + 1))
        n += 1; time.sleep(SLEEP)
        if limit and n >= limit: break
    print("دانلود شد:", n)

# ---------------------------------------------------------------- متن
START = re.compile(r"گزارش\s*حسابرس\s*مستقل|گزارش\s*حسابرس\s*و\s*بازرس\s*قانونی")
END = re.compile(r"صورت\s*وضعیت\s*مالی|ترازنامه|صورت\s*سود\s*و\s*زیان")

def find_report(text):
    text = norm(fix_visual(text))
    m = START.search(text)
    if not m: return ""
    seg = text[m.start(): m.start() + 25000]
    e = END.search(seg, 3000)
    return seg[: e.start()] if e else seg

def cmd_text(max_pages=15):
    import pdfplumber
    scanned = []
    for f in sorted(PDF.glob("*.pdf")):
        o = TXT / f"{f.stem}.txt"
        if o.exists(): continue
        try:
            with pdfplumber.open(f) as p:
                raw = "\n".join((pg.extract_text() or "") for pg in p.pages[:max_pages])
        except Exception as e:
            print("خطا در", f.name, e, file=sys.stderr); continue
        if len(raw.strip()) < 200:
            scanned.append(f.stem); continue
        rep = find_report(raw)
        o.write_text(rep if rep else norm(fix_visual(raw))[:25000], encoding="utf-8")
        if not rep: print("بخش گزارش حسابرس پیدا نشد (کل متن ذخیره شد):", f.name)
    pd.DataFrame({"TracingNo": scanned}).to_csv(OUT / "need_ocr.csv", index=False)
    print("اسکن‌شده (نیازمند OCR):", len(scanned))

# ---------------------------------------------------------------- ویژگی‌ها
FIRM = re.compile(r"((?:سازمان|مؤسسه|موسسه)\s*حسابرسی\s*[^\n\d:،.]{0,45}|[^\n\d]{2,30}\s*حسابداران\s*رسمی(?:\s*[^\n\d]{0,20})?)")
DATE = re.compile(r"(1[34]\d{2})/(\d{1,2})/(\d{1,2})")
FLAGS = {
    "going_concern": r"تداوم\s*فعالیت|ابهام\s*با\s*اهمیت",
    "emphasis_para": r"تأکید\s*بر\s*مطلب|بند\s*تأکید|تاکید\s*بر\s*مطلب",
    "kam": r"امور\s*عمده\s*حسابرسی|مسائل\s*عمده\s*حسابرسی",
    "related_party": r"اشخاص\s*وابسته",
    "internal_control": r"کنترل\s*های\s*داخلی|کنترل‌های\s*داخلی",
    "aml": r"پولشویی|مبارزه\s*با\s*تأمین\s*مالی\s*تروریسم",
    "other_legal_reqs": r"سایر\s*الزامات\s*قانونی\s*و\s*مقرراتی",
    "tax": r"مالیات",
    "lawsuit": r"دعاوی|دعوی|حقوقی",
    "bank_loans": r"تسهیلات\s*مالی|تسهیلات\s*بانکی|تسهیلات",
    "restated": r"تجدید\s*ارائه|تعدیل\s*سنواتی|اصلاح\s*اشتباه",
    "board_report": r"گزارش\s*هیئت\s*مدیره|گزارش\s*هیات\s*مدیره",
    "stock_exchange_rules": r"سازمان\s*بورس|دستورالعمل\s*(?:حاکمیت|افشا)",
    "corp_governance": r"حاکمیت\s*شرکتی",
    "dividend": r"سود\s*تقسیمی|تقسیم\s*سود",
    "ministry_law": r"ماده\s*\d+",
    "capital_increase": r"افزایش\s*سرمایه",
    "joint_audit": r"حسابرسان\s*مشترک|بازرسان\s*قانونی|اعضای\s*هیأت",
}

def opinion_type(t):
    if re.search(r"عدم\s*اظهار\s*نظر|اظهار\s*نظر\s*نمی\s*کنیم|اظهارنظر\s*نمی", t): return "disclaimer"
    if re.search(r"نامطلوب|به\s*نحو\s*مطلوب\s*ارائه\s*نشده|مطلوب\s*نمی\s*باشد|مطلوب\s*نیست", t): return "adverse"
    if re.search(r"به\s*استثنای|مشروط|به\s*استثناء", t): return "qualified"
    if re.search(r"به\s*نحو\s*مطلوب", t): return "unqualified"
    return "unknown"

def parse_report(t):
    t = norm(t); d = {}
    d["opinion"] = opinion_type(t)
    d["opinion_qualified_any"] = int(d["opinion"] in ("qualified", "adverse", "disclaimer"))
    # نام موسسه: بیشترین تکرار؛ ترجیح نیمه دوم متن (امضا)
    tail = t[len(t) // 2:]
    c = collections.Counter(re.sub(r"\s+", " ", x).strip(" -") for x in FIRM.findall(tail or t))
    d["auditor_firm_raw"] = c.most_common(1)[0][0] if c else None
    lines = [l.strip() for l in t.split("\n") if l.strip()]
    d["signature_block"] = " | ".join(lines[-12:])      # شریک/حسابدار رسمی را دستی از اینجا تأیید کنید
    dates = DATE.findall(t) or [(y, m, dd) for dd, m, y in re.findall(r"(\d{1,2})/(\d{1,2})/(1[34]\d{2})", t)]
    d["report_date"] = "/".join(dates[-1]) if dates else None
    d["n_dates"] = len(dates)
    for k, pat in FLAGS.items():
        n = len(re.findall(pat, t)); d[k + "_n"] = n; d[k] = int(n > 0)
    d["n_qualification_items"] = len(re.findall(r"(?:^|\n)\s*(?:\d+|[۰-۹]+)\s*[-–.)]", t))
    d["report_chars"] = len(t)
    d["report_words"] = len(t.split())
    d["has_text"] = int(len(t) > 300)
    return d

def cmd_parse():
    letters = pd.read_csv(OUT / "letters.csv"); rows = []
    for f in sorted(TXT.glob("*.txt")):
        d = parse_report(f.read_text(encoding="utf-8")); d["TracingNo"] = int(f.stem); rows.append(d)
    df = pd.DataFrame(rows).merge(letters[["TracingNo", "Symbol", "Title", "PublishDateTime"]], on="TracingNo", how="left")
    m = df["Title"].astype(str).map(norm).str.extract(r"(\d{4})/\d{2}/\d{2}")
    df["year"] = pd.to_numeric(m[0], errors="coerce")
    df.to_csv(OUT / "auditor_reports.csv", index=False, encoding="utf-8-sig")
    print("auditor_reports.csv:", df.shape)

# ---------------------------------------------------------------- پنل حسابرس
def canon(s):
    if not isinstance(s, str): return None
    s = norm(s)
    s = re.sub(r"(سازمان|مؤسسه|موسسه)\s*حسابرسی|حسابداران\s*رسمی|و\s*همکاران|\bو\s*شرکا", " ", s)
    return re.sub(r"\s+", " ", s).strip() or None

def build_panel(rep, assets=None):
    """rep: auditor_reports با Symbol,year,auditor_firm_raw؛ assets: Symbol,year,TA,sector (اختیاری)"""
    df = rep.dropna(subset=["Symbol", "year"]).sort_values("publish" if "publish" in rep else "PublishDateTime")
    df = df.drop_duplicates(["Symbol", "year"], keep="last").sort_values(["Symbol", "year"]).copy()
    df["auditor"] = df["auditor_firm_raw"].map(canon)
    # سازمان حسابرسی را قبل از canon شناسایی کن
    df.loc[df["auditor_firm_raw"].astype(str).map(norm).str.contains("سازمان حسابرسی"), "auditor"] = "سازمان حسابرسی"
    g = df.groupby("Symbol")["auditor"]
    df["auditor_prev"] = g.shift(1)
    df["AUDSWITCH"] = ((df["auditor"] != df["auditor_prev"]) & df["auditor_prev"].notna()).astype(int)
    # دوره تصدی: سال‌های متوالی با همان حسابرس (و سال‌های بدون وقفه)
    ten, last_a, last_y, cur = [], {}, {}, {}
    for s, a, y in zip(df["Symbol"], df["auditor"], df["year"]):
        if s in last_a and last_a[s] == a and y - last_y[s] == 1: cur[s] += 1
        else: cur[s] = 1
        last_a[s], last_y[s] = a, y; ten.append(cur[s])
    df["AUDTEN"] = ten; df["AUDTEN_LN"] = df["AUDTEN"].map(lambda x: __import__("math").log(x))
    df["AUDOPN"] = df["opinion_qualified_any"]
    if assets is not None:
        df = df.merge(assets, on=["Symbol", "year"], how="left")
        a = df.groupby(["year", "auditor"])["TA"].sum().rename("aud_assets").reset_index()
        tot = df.groupby("year")["TA"].sum().rename("tot_assets").reset_index()
        n = df.groupby(["year", "auditor"]).size().rename("aud_clients").reset_index()
        df = df.merge(a, on=["year", "auditor"]).merge(tot, on="year").merge(n, on=["year", "auditor"])
        df["AUD_SHARE_MKT"] = df["aud_assets"] / df["tot_assets"]
        df["AUDSIZE"] = df.groupby("year")["aud_assets"].transform(lambda x: (x >= x.quantile(0.75)).astype(int))
        df.loc[df["auditor"] == "سازمان حسابرسی", "AUDSIZE"] = 1
        if "sector" in df:
            sa = df.groupby(["year", "sector", "auditor"])["TA"].sum().rename("aud_ind").reset_index()
            st = df.groupby(["year", "sector"])["TA"].sum().rename("ind_tot").reset_index()
            df = df.merge(sa, on=["year", "sector", "auditor"]).merge(st, on=["year", "sector"])
            df["AUDSPEC"] = (df["aud_ind"] / df["ind_tot"] > 0.15).astype(int)
    return df

def cmd_panel():
    rep = pd.read_csv(OUT / "auditor_reports.csv")
    p = OUT / "panel.csv"
    assets = None
    if p.exists():
        pp = pd.read_csv(p); cols = [c for c in ("Symbol", "year", "TA", "sector") if c in pp]
        assets = pp[cols]
    out = build_panel(rep, assets)
    out.to_csv(OUT / "auditor_panel.csv", index=False, encoding="utf-8-sig")
    print("auditor_panel.csv:", out.shape, "؛ جدول نام‌ها را (auditor) برای یکسان‌سازی دستی بررسی کنید")

if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else ""
    {"pdf": cmd_pdf, "text": cmd_text, "parse": cmd_parse, "panel": cmd_panel}.get(c, lambda: print(__doc__))()
