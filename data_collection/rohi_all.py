#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
جمع‌آوری داده کدال و TSETMC و ساخت پنل برای دو مقاله (DIV و بندهای پیمان) - فایل یکپارچه.
نصب:  pip install requests pandas openpyxl beautifulsoup4 lxml
ترتیب اجرا (از شبکه ایران):
  python rohi_all.py list --from 1393/01/01 --to 1402/12/29
  python rohi_all.py fetch --limit 20      # ابتدا آزمایشی؛ بعد بدون limit
  python rohi_all.py parse
  python rohi_all.py symbols
  python rohi_all.py tse
  python rohi_all.py build
هشدار: اتصال به سایت‌ها آزمون نشده؛ endpointها را در F12 تأیید و در بخش CONFIG اصلاح کنید.
"""
import argparse, json, re, sys, time, pathlib, types
import requests, numpy as np, pandas as pd

# ====================== CONFIG ======================
OUT = pathlib.Path("data_out"); OUT.mkdir(exist_ok=True)

# ---------- شرایط غربالگری (مطابق بخش ۴-۲ مقاله‌ها؛ قابل ویرایش) ----------
SCREEN = {
    "year_from": 1393, "year_to": 1402,
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


# ====================== CLI / استفاده در Colab ======================
def run(cmd, from_="1393/01/01", to="1402/12/29", limit=0):
    """در Colab/Jupyter به‌جای خط فرمان: run('list'), run('fetch', limit=20), run('parse'),
    run('symbols'), run('tse'), run('build')"""
    a = types.SimpleNamespace(from_=from_, to=to, limit=limit)
    {"list": lambda: cmd_list(a), "fetch": lambda: cmd_fetch(a), "parse": lambda: cmd_parse(a),
     "symbols": make_symbols, "tse": tse_main, "build": build_main}[cmd]()

if __name__ == "__main__" and "ipykernel" not in sys.modules:
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="c", required=True)
    l = sp.add_parser("list"); l.add_argument("--from", dest="from_", default="1393/01/01"); l.add_argument("--to", default="1402/12/29")
    f = sp.add_parser("fetch"); f.add_argument("--limit", type=int, default=0)
    for n in ("parse", "symbols", "tse", "build"): sp.add_parser(n)
    a = ap.parse_args()
    run(a.c, getattr(a, "from_", "1393/01/01"), getattr(a, "to", "1402/12/29"), getattr(a, "limit", 0))
