#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
جمع‌آوری داده کدال و TSETMC و ساخت پنل برای دو مقاله (DIV و بندهای پیمان) - فایل یکپارچه.
نصب:  pip install requests pandas openpyxl beautifulsoup4 lxml
ترتیب اجرا (از شبکه ایران):
  python rohi_all.py list --from 1390/01/01 --to 1404/12/29
  python rohi_all.py fetch --limit 20      # ابتدا آزمایشی؛ بعد بدون limit
  python rohi_all.py parse
  python rohi_all.py symbols
  python rohi_all.py tse
  python rohi_all.py build
  # گزارش حسابرس: pdf (--limit)، text، aparse، apanel   (نیازمند: pip install pdfplumber)
هشدار: اتصال به سایت‌ها آزمون نشده؛ endpointها را در F12 تأیید و در بخش CONFIG اصلاح کنید.
"""
import argparse, json, re, sys, time, pathlib, types, unicodedata, collections
import requests, numpy as np, pandas as pd

# ====================== CONFIG ======================
OUT = pathlib.Path("data_out"); OUT.mkdir(exist_ok=True)

# ---------- شرایط غربالگری (مطابق بخش ۴-۲ مقاله‌ها؛ قابل ویرایش) ----------
SCREEN = {
    "year_from": 1390, "year_to": 1404,
    "fiscal_year_end": "12/29",          # پایان سال مالی ۲۹ اسفند
    "min_consecutive_years": 3,
    "require_loans_any_year": True,      # حداقل در یک سال تسهیلات دریافتی/بازپرداخت دارد
    "min_total_assets": 0,               # در صورت تمایل حداقل دارایی (میلیون ریال)
    # صنایع حذف‌شونده (بر پایه نام گروه صنعت در TSETMC؛ پس از دیدن فهرست واقعی اصلاح شود)
    "exclude_sectors": ["بانک", "بیمه", "لیزینگ", "سرمایه گذاری", "سرمایه‌گذاری", "هلدینگ",
                        "واسطه گری مالی", "واسطه‌گری مالی", "فعالیتهای کمکی به نهادهای مالی",
                        "چند رشته ای صنعتی", "چند رشته‌ای صنعتی", "صندوق"],
    "only_audited": True,
}

# ---------- endpointها (در F12 تأیید شود) ----------
CODAL_SEARCH = "https://search.codal.ir/api/search/v2/q"
CODAL_BASE = "https://codal.ir"
CODAL_PARAMS = {"Audited": "true", "AuditorRef": "-1", "Category": "1", "Childs": "true",
                "CompanyState": "0", "CompanyType": "1", "Consolidatable": "true",
                "IsNotAudited": "false", "Length": "-1", "LetterType": "6", "Mains": "true",
                "NotAudited": "false", "NotConsolidatable": "true", "Publisher": "false",
                "TracingNo": "-1", "search": "true"}
TSE = "https://cdn.tsetmc.com/api"
TSE_ENDPOINTS = {
    "search": TSE + "/Instrument/GetInstrumentSearch/{q}",
    "instrument": TSE + "/Instrument/GetInstrumentInfo/{ins}",
    "shareholders": TSE + "/Shareholder/GetInstrumentShareHolderLast/{ins}",
    "prices": TSE + "/ClosingPrice/GetClosingPriceDailyList/{ins}/0",
}
SLEEP = 1.5

# ---------- کلیدواژه ردیف‌ها (regex روی برچسب نرمال‌شده) و صفحه مربوط ----------
# sheet: bs=ترازنامه، is=سود و زیان، cf=جریان وجوه نقد
ITEMS = {
  "TA":        ("bs", r"^جمع دارایی"),
  "CA":        ("bs", r"^جمع دارایی های جاری"),
  "CL":        ("bs", r"^جمع بدهی های جاری"),
  "TL":        ("bs", r"^جمع بدهی ها$|^جمع بدهی"),
  "EQUITY":    ("bs", r"^جمع حقوق مالکانه|^جمع حقوق صاحبان سهام"),
  "CAPITAL":   ("bs", r"^سرمایه$"),
  "RETEARN":   ("bs", r"^سود \(زیان\) انباشته|^سود و زیان انباشته|^زیان انباشته|^سود انباشته"),
  "CASH":      ("bs", r"^موجودی نقد"),
  "INVENTORY": ("bs", r"^موجودی مواد و کالا"),
  "INTANG":    ("bs", r"^دارایی های نامشهود"),
  "PPE":       ("bs", r"^دارایی های ثابت مشهود"),
  "ST_INV":    ("bs", r"^سرمایه گذاری های کوتاه مدت"),
  "LT_INV":    ("bs", r"^سرمایه گذاری های بلند مدت"),
  "INV_PROP":  ("bs", r"^سرمایه گذاری در املاک|^املاک سرمایه گذاری"),
  "REL_REC":   ("bs", r"دریافتنی.*(اشخاص وابسته|وابسته)"),
  "LOAN_BAL":  ("bs", r"^تسهیلات مالی"),
  "SALES":     ("is", r"^درآمدهای عملیاتی|^فروش خالص"),
  "EBIT":      ("is", r"^سود \(زیان\) عملیاتی|^سود عملیاتی"),
  "FINCOST":   ("is", r"^هزینه های مالی"),
  "NI":        ("is", r"^سود \(زیان\) خالص|^سود خالص"),
  "CFO":       ("cf", r"فعالیت های عملیاتی"),
  "LOAN_IN":   ("cf", r"^دریافت تسهیلات مالی|^دریافت تسهیلات"),
  "LOAN_REPAY":("cf", r"^پرداخت اصل تسهیلات|^بازپرداخت اصل تسهیلات|^پرداخت تسهیلات"),
  "DEPRECIATION":("cf", r"^استهلاک"),
}
# اقلام یادداشتی که باید دستی/نیمه‌خودکار تکمیل شوند (فقط جست‌وجوی متنی در html):
NOTE_PATTERNS = {
  "OVERDUE": r"سررسید\s*گذشته",
  "PENALTY": r"جرائم\s*دیرکرد|جریمه\s*دیرکرد",
  "ART141": r"ماده\s*۱۴۱|ماده\s*141",
}

C = types.SimpleNamespace(**{k: v for k, v in dict(globals()).items() if k.isupper()})

# ====================== TEXT UTILS ======================
_DIG = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
def norm(s):
    s = str(s).translate(_DIG).replace("ي", "ی").replace("ك", "ک").replace("‌", " ").replace("‏", "").replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()
def to_num(v):
    s = norm(v).replace(",", "").replace("٬", "")
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        x = float(s)
        return -x if neg else x
    except ValueError:
        return None

# ====================== CODAL ======================

CODAL_CFG = {
    "search_url": CODAL_SEARCH,
    "base": CODAL_BASE,
    # LetterType=6 معمولاً «اطلاعات و صورت‌های مالی سالانه» است؛ در سایت بررسی کنید
    "sleep": 1.5,           # مکث مؤدبانه بین درخواست‌ها
    "out": OUT,
}
HDR = {"User-Agent": "Mozilla/5.0 (research; academic use)", "Accept": "application/json, text/html"}


def get(url, **kw):
    for i in range(4):
        try:
            r = requests.get(url, headers=HDR, timeout=40, **kw)
            if r.status_code == 200:
                return r
            print("HTTP", r.status_code, url[:100], file=sys.stderr)
        except requests.RequestException as e:
            print("خطا:", e, file=sys.stderr)
        time.sleep(2 ** (i + 1))
    return None

def cmd_list(a):
    rows, page = [], 1
    while True:
        p = dict(CODAL_PARAMS, PageNumber=page, FromDate=a.from_, ToDate=a.to)
        r = get(CODAL_CFG["search_url"], params=p)
        if r is None: break
        j = r.json()
        letters = j.get("Letters", [])
        if not letters: break
        rows += letters
        print(f"صفحه {page}: {len(letters)} نامه، جمع {len(rows)} از {j.get('Total')}")
        if page >= int(j.get("Page", page)): break
        page += 1; time.sleep(CODAL_CFG["sleep"])
    if not rows:
        sys.exit("هیچ نامه‌ای دریافت نشد: احتمالاً دسترسی به codal.ir از این شبکه مسدود است (Colab). روی رایانه‌ای در ایران اجرا کنید.")
    df = pd.DataFrame(rows)
    df.to_csv(CODAL_CFG["out"] / "letters.csv", index=False, encoding="utf-8-sig")
    print("ذخیره شد:", CODAL_CFG["out"] / "letters.csv", len(df))

def cmd_fetch(a):
    df = pd.read_csv(CODAL_CFG["out"] / "letters.csv")
    d = CODAL_CFG["out"] / "html"; d.mkdir(exist_ok=True)
    n = 0
    for _, r in df.iterrows():
        f = d / f"{r['TracingNo']}.html"
        if f.exists(): continue
        url = r["Url"] if str(r["Url"]).startswith("http") else CODAL_CFG["base"] + str(r["Url"])
        resp = get(url)
        if resp is not None:
            f.write_text(resp.text, encoding="utf-8")
        n += 1; time.sleep(CODAL_CFG["sleep"])
        if a.limit and n >= a.limit: break
    print("دانلود شد:", n)

# --- استخراج: صفحه تصمیم کدال داده‌ها را معمولاً در متغیر جاوااسکریپت datasource می‌گذارد ---
def extract_datasource(html):
    m = re.search(r"var\s+datasource\s*=\s*(\{.*?\});\s*(?:var|</script>)", html, re.S)
    return json.loads(m.group(1)) if m else None

def cells_from_datasource(ds):
    out = []
    for sh in ds.get("sheets", []):
        for tb in sh.get("tables", []):
            for c in tb.get("cells", []):
                v = c.get("value")
                if v not in (None, ""):
                    out.append({"sheet": sh.get("title") or sh.get("code"), "row": c.get("rowSequence"),
                                "col": c.get("columnSequence"), "address": c.get("address"), "value": v})
    return pd.DataFrame(out)

ITEMS = {  # واژه‌های کلیدی ردیف‌ها (برای تطبیق متنی با برچسب ردیف؛ پس از دیدن داده واقعی اصلاح کنید)
    "TA": ["جمع دارایی‌ها", "جمع دارایی ها"],
    "ST_INV": ["سرمایه‌گذاری‌های کوتاه‌مدت", "سرمایه گذاری های کوتاه مدت"],
    "LT_INV": ["سرمایه‌گذاری‌های بلندمدت", "سرمایه گذاری های بلند مدت"],
    "INV_PROP": ["املاک سرمایه‌گذاری"],
    "LOAN_IN": ["دریافت تسهیلات مالی"],
    "LOAN_REPAY": ["پرداخت اصل تسهیلات", "بازپرداخت اصل تسهیلات"],
    "CFO": ["جریان خالص ورود (خروج) وجه نقد حاصل از فعالیت‌های عملیاتی", "جریان خالص ورود وجه نقد حاصل از فعالیت"],
    "OVERDUE": ["سررسید گذشته", "سررسید‌ گذشته"],
}

def cmd_parse(a):
    d = CODAL_CFG["out"] / "html"; res = []
    for f in sorted(d.glob("*.html")):
        html = f.read_text(encoding="utf-8")
        ds = extract_datasource(html)
        if not ds:
            print("datasource یافت نشد:", f.name); continue
        cells = cells_from_datasource(ds)
        if cells.empty: continue
        cells["TracingNo"] = f.stem
        cells.to_csv(CODAL_CFG["out"] / f"cells_{f.stem}.csv", index=False, encoding="utf-8-sig")
        # حسابرس: جست‌وجوی متنی در صفحه (باید دستی بررسی شود)
        m = re.search(r"(سازمان حسابرسی|مؤسسه حسابرسی\s+[^\s<]+(?:\s+[^\s<]+){0,2})", html)
        res.append({"TracingNo": f.stem, "auditor_guess": m.group(1) if m else None, "n_cells": len(cells)})
    pd.DataFrame(res).to_csv(CODAL_CFG["out"] / "parsed_index.csv", index=False, encoding="utf-8-sig")
    print("پایان. سپس با ITEMS ردیف‌ها را به متغیر تبدیل و در استتا ادغام کنید.")

def tsetmc_shareholders(inscode):
    """سهامداران عمده؛ endpoint را در مرورگر تأیید کنید."""
    r = get(f"https://cdn.tsetmc.com/api/Shareholder/GetInstrumentShareHolderLast/{inscode}")
    return r.json() if r is not None else None


# ====================== TSETMC ======================
TH = {"User-Agent": "Mozilla/5.0 (research; academic use)"}

def tget(url):
    for i in range(4):
        try:
            r = requests.get(url, headers=TH, timeout=40)
            if r.status_code == 200: return r.json()
            print("HTTP", r.status_code, url, file=sys.stderr)
        except Exception as e:
            print("خطا", e, file=sys.stderr)
        time.sleep(2 ** (i + 1))

def make_symbols():
    """از Symbolهای letters.csv، کد InsCode را با جست‌وجوی TSETMC می‌سازد (endpoint تأیید شود)."""
    sy = sorted(pd.read_csv(C.OUT / "letters.csv")["Symbol"].dropna().unique())
    rows = []
    for q in sy:
        j = tget(C.TSE_ENDPOINTS["search"].format(q=q))
        for it in (j or {}).get("instrumentSearch", [])[:1]:
            rows.append({"Symbol": q, "InsCode": it.get("insCode"), "name": it.get("lVal30")})
        time.sleep(C.SLEEP)
    pd.DataFrame(rows).to_csv(C.OUT / "symbols.csv", index=False, encoding="utf-8-sig")
    print("symbols.csv:", len(rows), "از", len(sy), "- موارد جاافتاده را دستی کامل کنید")

def tse_main():
    sy = pd.read_csv(C.OUT / "symbols.csv", dtype=str)
    inst, hold, px = [], [], []
    for _, r in sy.iterrows():
        ins = r["InsCode"]
        j = tget(C.TSE_ENDPOINTS["instrument"].format(ins=ins))
        if j:
            i = j.get("instrumentInfo", j)
            inst.append({"Symbol": r["Symbol"], "InsCode": ins,
                         "sector": (i.get("sector") or {}).get("lSecVal"),
                         "shares": i.get("zTitad")})
        time.sleep(C.SLEEP)
        j = tget(C.TSE_ENDPOINTS["shareholders"].format(ins=ins))
        for s in (j or {}).get("shareShareholder", []):
            hold.append({"Symbol": r["Symbol"], "date": s.get("dEven"), "holder": s.get("shareHolderName"),
                         "pct": s.get("perOfShares"), "shares": s.get("numberOfShares")})
        time.sleep(C.SLEEP)
        j = tget(C.TSE_ENDPOINTS["prices"].format(ins=ins))
        for p in (j or {}).get("closingPriceDaily", []):
            px.append({"Symbol": r["Symbol"], "date": p.get("dEven"), "close": p.get("pClosing")})
        time.sleep(C.SLEEP)
    for name, rows in (("instruments", inst), ("holders", hold), ("prices", px)):
        pd.DataFrame(rows).to_csv(C.OUT / f"tse_{name}.csv", index=False, encoding="utf-8-sig")
    print("پایان")

# ====================== BUILD PANEL ======================
import glob

SHEET_KEYS = {"bs": ["وضعیت مالی", "ترازنامه"], "is": ["سود و زیان", "سود (زیان)"], "cf": ["جریان", "وجوه نقد"]}

def sheet_kind(title):
    t = norm(title or "")
    for k, keys in SHEET_KEYS.items():
        if any(norm(x) in t for x in keys): return k

def extract_items(cells):
    """cells: sheet,row,col,value -> {var: مقدار سال جاری (اولین عدد ردیف)}"""
    out = {}
    cells = cells.copy(); cells["kind"] = cells["sheet"].map(sheet_kind)
    for (sh, kind, row), g in cells.groupby(["sheet", "kind", "row"]):
        if kind is None: continue
        g = g.sort_values("col")
        label = next((norm(v) for v in g["value"] if to_num(v) is None and str(v).strip()), None)
        nums = [to_num(v) for v in g["value"] if to_num(v) is not None]
        if not label or not nums: continue
        for var, (k, pat) in C.ITEMS.items():
            if k == kind and var not in out and re.search(pat, label):
                out[var] = nums[0]
    return out

def fiscal_end(title):
    m = re.search(r"(\d{4})/(\d{2}/\d{2})", norm(title))
    return (int(m.group(1)), m.group(2)) if m else (None, None)

def build_main():
    letters = pd.read_csv(C.OUT / "letters.csv")
    rows = []
    for f in glob.glob(str(C.OUT / "cells_*.csv")):
        cells = pd.read_csv(f)
        tn = cells["TracingNo"].iloc[0]
        meta = letters[letters["TracingNo"] == tn].iloc[0]
        yr, md = fiscal_end(meta["Title"])
        d = {"TracingNo": tn, "Symbol": meta["Symbol"], "year": yr, "fy_end": md,
             "publish": meta.get("PublishDateTime")}
        d.update(extract_items(cells)); rows.append(d)
    df = pd.DataFrame(rows)
    for v in C.ITEMS:
        if v not in df: df[v] = np.nan   # ردیف پیدا نشده: NaN (بعداً دستی کنترل شود)
    # اصلاحیه‌ها: آخرین انتشار هر نماد-سال
    df = df.sort_values("publish").drop_duplicates(["Symbol", "year"], keep="last")

    # ---- غربالگری ----
    s = C.SCREEN
    df = df[df["year"].between(s["year_from"] - 1, s["year_to"])]
    df = df[df["fy_end"] == s["fiscal_year_end"]]
    tse = C.OUT / "tse_instruments.csv"
    if tse.exists():
        ins = pd.read_csv(tse)[["Symbol", "sector", "shares"]]
        df = df.merge(ins, on="Symbol", how="left")
        bad = "|".join(map(re.escape, s["exclude_sectors"]))
        df = df[~df["sector"].fillna("").map(norm).str.contains(bad)]
    need = ["TA", "TL", "EQUITY", "CA", "CL", "CFO"]
    df = df.dropna(subset=need)
    df = df.sort_values(["Symbol", "year"])
    # حداقل سال‌های متوالی
    def run_ok(g):
        y = g["year"].to_numpy(); best = cur = 1
        for a, b in zip(y[:-1], y[1:]):
            cur = cur + 1 if b == a + 1 else 1; best = max(best, cur)
        return best >= s["min_consecutive_years"]
    df = df.groupby("Symbol").filter(run_ok)
    if s["require_loans_any_year"]:
        df = df.groupby("Symbol").filter(lambda g: (g[["LOAN_IN", "LOAN_REPAY"]].abs().sum().sum() > 0))

    # ---- ساخت متغیرها ----
    g = df.groupby("Symbol")
    for v in ["TA", "ST_INV", "LT_INV", "INV_PROP", "REL_REC", "LOAN_BAL"]:
        if v in df: df["L_" + v] = g[v].shift(1)
    z = lambda c: df[c].fillna(0) if c in df else 0
    df["LOAN"] = (z("LOAN_IN") - z("LOAN_REPAY").abs()) / df["L_TA"]
    nonop = z("ST_INV") + z("LT_INV") + z("INV_PROP") + z("REL_REC")
    df["NONOP_AMT"] = nonop
    df["NONOP"] = (nonop - nonop.groupby(df["Symbol"]).shift(1)) / df["L_TA"]
    d_nonop = nonop - nonop.groupby(df["Symbol"]).shift(1)
    net = z("LOAN_IN") - z("LOAN_REPAY").abs()
    df["DIV"] = np.where(df["LOAN"] >= 0.02, (d_nonop / net).clip(0, 1), 0.0)
    df["LARGE"] = (df["LOAN"] >= 0.05).astype(int)
    df["SIZE"] = np.log(df["TA"]); df["LEV"] = df["TL"] / df["TA"]
    df["ROA"] = df["EBIT"] / df["L_TA"]; df["CFO_TA"] = df["CFO"] / df["L_TA"]
    df["CASH_TA"] = df["CASH"] / df["TA"]; df["TANG"] = df["PPE"] / df["TA"]
    df["GROW"] = df["SALES"] / g["SALES"].shift(1) - 1
    df["LOSS"] = (df["NI"] < 0).astype(int)
    df["AGE_PROXY"] = g.cumcount() + 1
    # معیارهای مقاله ۲
    df["CR"] = df["CA"] / df["CL"]; df["QR"] = (df["CA"] - df["INVENTORY"]) / df["CL"]
    df["WC"] = (df["CA"] - df["CL"]) / df["TA"]
    df["ICR"] = df["EBIT"] / df["FINCOST"].abs()
    df["EBITDA"] = df["EBIT"] + z("DEPRECIATION")
    df["DEBT_EBITDA"] = df["TL"] / df["EBITDA"]       # جایگزین: فقط بدهی بهره‌دار پس از ورود یادداشت
    df["CFO_TD"] = df["CFO"] / df["TL"]
    df["TNW"] = (df["EQUITY"] - z("INTANG")) / df["TA"]
    df["ZSCORE"] = (6.56 * df["WC"] + 3.26 * df["RETEARN"] / df["TA"] +
                    6.72 * df["EBIT"] / df["TA"] + 1.05 * df["EQUITY"] / df["TL"])
    # متغیر وابسته ماده ۱۴۱: زیان انباشته >= نصف سرمایه
    df["DEF_141"] = ((-df["RETEARN"]).clip(lower=0) >= 0.5 * df["CAPITAL"]).astype(int)
    df["F_DEF_141"] = df.groupby("Symbol")["DEF_141"].shift(-1)
    df["F_DEF_Z"] = (df.groupby("Symbol")["ZSCORE"].shift(-1) < 1.1).astype(float)
    df["F_ROA"] = df.groupby("Symbol")["ROA"].shift(-1)
    # مالکیت و حسابرس (در صورت وجود فایل‌ها)
    h = C.OUT / "tse_holders.csv"
    if h.exists():
        hd = pd.read_csv(h)
        hd["pct"] = pd.to_numeric(hd["pct"], errors="coerce")
        top = hd.sort_values("pct", ascending=False).groupby("Symbol").head(5)
        conc = top.groupby("Symbol")["pct"].apply(lambda x: ((x / 100) ** 2).sum()).rename("CONC")
        df = df.merge(conc, on="Symbol", how="left")
    df.to_csv(C.OUT / "panel.csv", index=False, encoding="utf-8-sig")
    try: df.to_stata(C.OUT / "panel.dta", write_index=False, version=118)
    except Exception as e: print("dta ذخیره نشد:", e)
    print("پنل:", df.shape, "شرکت:", df["Symbol"].nunique())
    print("متغیرهای دستی/نیمه‌خودکار: AUDQ، STATE، OVERDUE، PENALTY، DEF_BANK، REL_REC (از یادداشت‌ها)")



# ====================== گزارش حسابرس (۱۳۹۰ تا ۱۴۰۴) ======================
PDF = OUT / "pdf"; TXT = OUT / "report_text"
ASLEEP = 1.5
AH = {"User-Agent": "Mozilla/5.0 (research; academic use)"}
for _d in (PDF, TXT): _d.mkdir(exist_ok=True)
_AR = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
def anorm(t):
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
            return v if v.startswith("http") else CODAL_BASE + v
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
                resp = requests.get(u, headers=AH, timeout=60)
                if resp.status_code == 200 and resp.content[:4] == b"%PDF":
                    f.write_bytes(resp.content); break
            except requests.RequestException as e:
                print("خطا", e, file=sys.stderr)
            time.sleep(2 ** (i + 1))
        n += 1; time.sleep(ASLEEP)
        if limit and n >= limit: break
    print("دانلود شد:", n)

# ---------------------------------------------------------------- متن
START = re.compile(r"گزارش\s*حسابرس\s*مستقل|گزارش\s*حسابرس\s*و\s*بازرس\s*قانونی")
END = re.compile(r"صورت\s*وضعیت\s*مالی|ترازنامه|صورت\s*سود\s*و\s*زیان")

def find_report(text):
    text = anorm(fix_visual(text))
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
        o.write_text(rep if rep else anorm(fix_visual(raw))[:25000], encoding="utf-8")
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
    t = anorm(t); d = {}
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

def cmd_aparse():
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
    s = anorm(s)
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

def cmd_apanel():
    rep = pd.read_csv(OUT / "auditor_reports.csv")
    p = OUT / "panel.csv"
    assets = None
    if p.exists():
        pp = pd.read_csv(p); cols = [c for c in ("Symbol", "year", "TA", "sector") if c in pp]
        assets = pp[cols]
    out = build_panel(rep, assets)
    out.to_csv(OUT / "auditor_panel.csv", index=False, encoding="utf-8-sig")
    print("auditor_panel.csv:", out.shape, "؛ جدول نام‌ها را (auditor) برای یکسان‌سازی دستی بررسی کنید")



# ====================== CLI / استفاده در Colab ======================
COMMANDS = ["list", "fetch", "parse", "symbols", "tse", "build",      # صورت‌های مالی + TSETMC
            "pdf", "text", "aparse", "apanel"]                       # گزارش حسابرس

def run(cmd, from_="1390/01/01", to="1404/12/29", limit=0):
    """Colab: run('list'); run('fetch', limit=20); run('build'); run('pdf', limit=20); run('apanel') ..."""
    a = types.SimpleNamespace(from_=from_, to=to, limit=limit)
    {"list": lambda: cmd_list(a), "fetch": lambda: cmd_fetch(a), "parse": lambda: cmd_parse(a),
     "symbols": make_symbols, "tse": tse_main, "build": build_main,
     "pdf": lambda: cmd_pdf(limit), "text": cmd_text, "aparse": cmd_aparse, "apanel": cmd_apanel}[cmd]()

if __name__ == "__main__" and "ipykernel" not in sys.modules:
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="c", required=True)
    l = sp.add_parser("list"); l.add_argument("--from", dest="from_", default="1390/01/01"); l.add_argument("--to", default="1404/12/29")
    for n in ("fetch", "pdf"):
        sp.add_parser(n).add_argument("--limit", type=int, default=0)
    for n in COMMANDS:
        if n not in ("list", "fetch", "pdf"): sp.add_parser(n)
    a = ap.parse_args()
    run(a.c, getattr(a, "from_", "1390/01/01"), getattr(a, "to", "1404/12/29"), getattr(a, "limit", 0))
