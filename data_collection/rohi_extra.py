#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
کد جامع داده‌های غیرمالی شرکت‌های بورسی (۱۳۹۰-۱۴۰۴) برای پژوهش‌های حسابداری/مالی.
خروجی همه ماژول‌ها: data_out/extra_<module>.csv با کلید Symbol, year  ← در مرحله merge به پنل شما وصل می‌شود.

فلسفه: (۱) همه نامه‌های هر نماد را بگیر؛ (۲) فقط با «عنوان» دسته‌بندی کن؛ (۳) متن دسته‌های لازم را ذخیره کن؛
(۴) از متن‌ها متغیر بساز. متن‌ها ذخیره می‌مانند تا برای پژوهش بعدی فقط الگوی جدید بنویسید.

نصب: pip install requests pandas beautifulsoup4 lxml pdfplumber
ورودی: data_out/my_symbols.csv با ستون Symbol  (و اختیاری my_panel.csv با Symbol,year)
ترتیب: list → events → download → text → board → keywords → employees → ownership → market → merge
Colab: run('list') ... run('merge')

هشدار: فقط منطق متن‌کاوی روی نمونه مصنوعی آزمون شده؛ اتصال به کدال/TSETMC آزمون نشده.
endpointها و پارامترها را در F12 تأیید کنید. دقت متن‌کاوی را با نمونه دستی گزارش کنید.
"""
import argparse, re, sys, time, math, pathlib, unicodedata, collections
import requests, pandas as pd

OUT = pathlib.Path("data_out"); OUT.mkdir(exist_ok=True)
HTML = OUT / "xhtml"; PDFD = OUT / "xpdf"; TXT = OUT / "xtext"
for d in (HTML, PDFD, TXT): d.mkdir(exist_ok=True)
CODAL_SEARCH = "https://search.codal.ir/api/search/v2/q"; CODAL_BASE = "https://codal.ir"
TSE = "https://cdn.tsetmc.com/api"; SLEEP = 1.5
H = {"User-Agent": "Mozilla/5.0 (research; academic use)", "Accept": "application/json, text/html"}
YEARS = (1390, 1404)

# ---------------- دسته‌بندی نامه‌ها با عنوان (regex روی عنوان نرمال‌شده) ----------------
CATEGORIES = {
    "fs_interim":     r"میان.?دوره|(3|6|9) ماهه",
    "fs_annual":      r"صورت.{0,3}های مالی|گزارش حسابرس و بازرس قانونی",
    "board_report":   r"گزارش فعالیت هیئت مدیره|گزارش تفسیری مدیریت|گزارش فعالیت هیات مدیره",
    "board_members":  r"(اطلاعات|مشخصات|ترکیب|انتخاب|تغییر).{0,25}(اعضای )?هیئت مدیره|هیات مدیره",
    "ceo_change":     r"(تغییر|انتصاب|استعفا).{0,15}مدیر ?عامل",
    "internal_ctrl":  r"کنترل.{0,3}های داخلی",
    "agm":            r"مجمع عمومی|صورتجلسه",
    "ownership":      r"ترکیب سهامداران|سهامداران (عمده|بالای)|تغییر در سهامداران",
    "capital_incr":   r"افزایش سرمایه|مجمع.*فوق.?العاده.*سرمایه",
    "dividend":       r"تقسیم سود|زمان.?بندی پرداخت سود|سود (نقدی|سهام)",
    "esg":            r"پایداری|مسئولیت اجتماعی|زیست.?محیط|ESG",
    "monthly":        r"فعالیت ماهانه",
    "auditor_change": r"(تغییر|انتخاب|استعفا).{0,15}حسابرس|حسابرس و بازرس",
    "related_party":  r"اشخاص وابسته",
    "lawsuit":        r"دعاوی|دعوا|رأی|حکم قطعی|پرونده",
    "listing":        r"پذیرش|درج نماد|توقف نماد|بازگشایی نماد",
    "sanction_risk":  r"تحریم",
    "product_tech":   r"فناوری|نوآوری|تحقیق و توسعه|ثبت اختراع|دانش.?بنیان",
    "other":          r".*",
}
CAT_ORDER = list(CATEGORIES)

# ---------------- واژه‌نامه‌های متن‌کاوی (شمارش در هر ۱۰۰۰ کلمه؛ قابل ویرایش) ----------------
LEXICONS = {
  "tech":      ["فناوری", "فن آوری", "نوآوری", "تحقیق و توسعه", "دیجیتال", "هوش مصنوعی", "اتوماسیون", "نرم افزار", "دانش بنیان", "اینترنت اشیا", "داده کاوی", "تحول دیجیتال", "ثبت اختراع"],
  "innovation":["نوآوری", "اختراع", "پژوهش", "پروژه تحقیقاتی", "محصول جدید", "توسعه محصول"],
  "esg_env":   ["محیط زیست", "انرژی تجدیدپذیر", "کاهش انتشار", "پسماند", "آلودگی", "بازیافت", "صرفه جویی انرژی"],
  "esg_soc":   ["مسئولیت اجتماعی", "ایمنی", "آموزش کارکنان", "رفاه کارکنان", "حقوق بشر", "کمک های خیریه", "اشتغال"],
  "esg_gov":   ["حاکمیت شرکتی", "شفافیت", "کمیته حسابرسی", "هیئت مدیره غیرموظف", "کنترل داخلی", "مدیریت ریسک", "اخلاق حرفه ای"],
  "risk_sanction": ["تحریم", "تحریم ها"],
  "risk_fx":   ["نرخ ارز", "ارز", "نوسانات ارزی", "ارز مبادله ای", "نیما"],
  "risk_infl": ["تورم", "افزایش قیمت", "قیمت گذاری دستوری", "قیمت گذاری"],
  "export":    ["صادرات", "صادراتی", "بازار جهانی", "بازارهای هدف"],
  "going_concern": ["تداوم فعالیت", "ورشکستگی", "ماده 141", "توقف فعالیت"],
  "financing": ["تسهیلات", "وام", "بدهی بانکی", "تامین مالی", "اوراق", "صکوک"],
  "capacity":  ["ظرفیت اسمی", "ظرفیت عملی", "استفاده از ظرفیت", "تولید"],
}

# ---------------- ابزارهای متن ----------------
_AR = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
def norm(t):
    t = unicodedata.normalize("NFKC", str(t)).translate(_AR)
    t = t.replace("ي", "ی").replace("ك", "ک").replace("‌", " ").replace("‏", "").replace("\xa0", " ")
    return re.sub(r"[ \t]+", " ", t)

def g2j(gy, gm, gd):
    gdm = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = 355666 + 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400 + gd + gdm[gm - 1]
    jy = -1595 + 33 * (days // 12053); days %= 12053
    jy += 4 * (days // 1461); days %= 1461
    if days > 365: jy += (days - 1) // 365; days = (days - 1) % 365
    jm = 1 + days // 31 if days < 186 else 7 + (days - 186) // 30
    jd = 1 + days % 31 if days < 186 else 1 + (days - 186) % 30
    return jy, jm, jd

def get(url, **kw):
    for i in range(4):
        try:
            r = requests.get(url, headers=H, timeout=50, **kw)
            if r.status_code == 200: return r
            print("HTTP", r.status_code, url[:90], file=sys.stderr)
        except requests.RequestException as e:
            print("خطا", e, file=sys.stderr)
        time.sleep(2 ** (i + 1))

def symbols():
    return pd.read_csv(OUT / "my_symbols.csv", dtype=str)["Symbol"].dropna().unique().tolist()

def categorize(title):
    t = norm(title)
    for c in CAT_ORDER:
        if c != "other" and re.search(CATEGORIES[c], t): return c
    return "other"

def letter_year(title, publish):
    m = re.search(r"(13\d{2}|14\d{2})/(\d{1,2})/(\d{1,2})", norm(title))
    if m: return int(m.group(1))
    p = norm(publish); m = re.search(r"(13\d{2}|14\d{2})/", p)
    return int(m.group(1)) if m else None

# ---------------- ۱) فهرست همه نامه‌های هر نماد ----------------
def cmd_list(from_="1390/01/01", to="1404/12/29"):
    rows = []
    for s in symbols():
        page = 1
        while True:
            p = {"Symbol": s, "Length": "-1", "LetterType": "-1", "Category": "-1", "PageNumber": page,
                 "FromDate": from_, "ToDate": to, "search": "true", "Publisher": "false", "Mains": "true",
                 "Childs": "true", "TracingNo": "-1", "AuditorRef": "-1", "CompanyState": "0", "CompanyType": "-1"}
            r = get(CODAL_SEARCH, params=p)
            if r is None: break
            j = r.json(); L = j.get("Letters", [])
            if not L: break
            rows += L
            if page >= int(j.get("Page", page)): break
            page += 1; time.sleep(SLEEP)
        print(s, len(rows)); time.sleep(SLEEP)
    if not rows: sys.exit("هیچ نامه‌ای دریافت نشد: دسترسی به کدال (ایران، بدون فیلترشکن) را بررسی کنید.")
    df = pd.DataFrame(rows).drop_duplicates("TracingNo")
    df["category"] = df["Title"].map(categorize)
    df["year"] = [letter_year(t, p) for t, p in zip(df["Title"], df["PublishDateTime"])]
    df.to_csv(OUT / "letters_all.csv", index=False, encoding="utf-8-sig")
    print("letters_all.csv:", df.shape); print(df["category"].value_counts())

# ---------------- ۲) رویدادها: فقط از عنوان‌ها (بدون دانلود) ----------------
def cmd_events():
    df = pd.read_csv(OUT / "letters_all.csv").dropna(subset=["year"])
    df["year"] = df["year"].astype(int)
    pv = df.pivot_table(index=["Symbol", "year"], columns="category", values="TracingNo", aggfunc="count", fill_value=0)
    pv.columns = ["n_" + c for c in pv.columns]
    for c in pv.columns: pv["d_" + c[2:]] = (pv[c] > 0).astype(int)
    pv.reset_index().to_csv(OUT / "extra_events.csv", index=False, encoding="utf-8-sig")
    print("extra_events.csv:", pv.shape)

# ---------------- ۳) دانلود دسته‌های لازم ----------------
DOWNLOAD_CATS = ["fs_annual", "board_report", "board_members", "internal_ctrl", "ownership", "esg",
                 "auditor_change", "ceo_change", "capital_incr", "dividend", "related_party"]
def cmd_download(limit=0, cats=None):
    df = pd.read_csv(OUT / "letters_all.csv")
    df = df[df["category"].isin(cats or DOWNLOAD_CATS)]; n = 0
    for _, r in df.iterrows():
        f = HTML / f"{r['TracingNo']}.html"
        if not f.exists() and isinstance(r.get("Url"), str):
            resp = get(r["Url"] if r["Url"].startswith("http") else CODAL_BASE + r["Url"])
            if resp is not None: f.write_text(resp.text, encoding="utf-8")
            time.sleep(SLEEP)
        pu = r.get("PdfUrl"); fp = PDFD / f"{r['TracingNo']}.pdf"
        if isinstance(pu, str) and pu.strip() and not fp.exists():
            resp = get(pu if pu.startswith("http") else CODAL_BASE + pu)
            if resp is not None and resp.content[:4] == b"%PDF": fp.write_bytes(resp.content)
            time.sleep(SLEEP)
        n += 1
        if limit and n >= limit: break
    print("پردازش‌شده:", n)

# ---------------- ۴) تبدیل به متن ----------------
def html_text(h):
    try:
        from bs4 import BeautifulSoup
        return BeautifulSoup(h, "lxml").get_text("\n")
    except Exception:
        return re.sub(r"<[^>]+>", "\n", h)

def reverse_fix(t):
    t = unicodedata.normalize("NFKC", t)
    if t.count("هیئت") + t.count("حسابرس") == 0 and (t.count("حسابرس"[::-1]) + t.count("هیئت"[::-1])) > 0:
        return "\n".join(re.sub(r"\d+", lambda m: m.group()[::-1], ln[::-1]) for ln in t.split("\n"))
    return t

def cmd_text():
    n = 0; scanned = []
    for f in HTML.glob("*.html"):
        o = TXT / f"{f.stem}.txt"
        if not o.exists():
            o.write_text(norm(html_text(f.read_text(encoding="utf-8"))), encoding="utf-8"); n += 1
    try:
        import pdfplumber
        for f in PDFD.glob("*.pdf"):
            o = TXT / f"{f.stem}_pdf.txt"
            if o.exists(): continue
            try:
                with pdfplumber.open(f) as p:
                    raw = "\n".join((pg.extract_text() or "") for pg in p.pages[:60])
            except Exception as e:
                print("pdf خطا", f.name, e, file=sys.stderr); continue
            if len(raw.strip()) < 200: scanned.append(f.stem); continue
            o.write_text(norm(reverse_fix(raw)), encoding="utf-8"); n += 1
    except ImportError:
        print("pdfplumber نصب نیست؛ فقط HTML خوانده شد")
    pd.DataFrame({"TracingNo": scanned}).to_csv(OUT / "extra_need_ocr.csv", index=False)
    print("متن ساخته شد:", n, "؛ اسکن‌شده:", len(scanned))

def load_texts(cats):
    L = pd.read_csv(OUT / "letters_all.csv"); L = L[L["category"].isin(cats)]
    for _, r in L.iterrows():
        t = ""
        for suf in ("", "_pdf"):
            f = TXT / f"{r['TracingNo']}{suf}.txt"
            if f.exists(): t += "\n" + f.read_text(encoding="utf-8")
        if t.strip(): yield r["Symbol"], r["year"], r["category"], r["TracingNo"], t

# ---------------- ۵) هیئت مدیره (متن‌کاوی خط‌به‌خط؛ دقت متوسط) ----------------
ROLE = re.compile(r"رئیس هیئت مدیره|رییس هیئت مدیره|نایب رییس|نائب رئیس|مدیر ?عامل|عضو هیئت مدیره|عضو موظف|عضو غیر ?موظف|عضو اصلی|عضو علی البدل")
EDU = {"phd": r"دکتری|دکترا|PhD", "msc": r"کارشناسی ارشد|فوق لیسانس", "bsc": r"کارشناسی(?! ارشد)|لیسانس", "dip": r"دیپلم|فوق دیپلم"}
MAJ = {"acc_fin": r"حسابداری|مالی|حسابرسی|اقتصاد|بانکداری", "eng": r"مهندسی|صنایع|مکانیک|برق|شیمی|عمران|نفت|معدن",
       "mgmt": r"مدیریت|بازرگانی|MBA", "law": r"حقوق|وکالت"}
def parse_board(t):
    t = norm(t); d = collections.Counter(); raw = []
    for ln in t.split("\n"):
        ln = ln.strip()
        if len(ln) < 8 or not ROLE.search(ln): continue
        raw.append(ln)
        if re.search(r"غیر ?موظف", ln): d["n_nonexec"] += 1
        elif re.search(r"موظف", ln): d["n_exec"] += 1
        if re.search(r"رئیس هیئت مدیره|رییس هیئت مدیره", ln): d["has_chair"] += 1
        if re.search(r"مدیر ?عامل", ln): d["has_ceo"] += 1
        if re.search(r"رئیس هیئت مدیره|رییس هیئت مدیره", ln) and re.search(r"مدیر ?عامل", ln): d["ceo_duality"] = 1
        for k, p in EDU.items():
            if re.search(p, ln): d["edu_" + k] += 1
        for k, p in MAJ.items():
            if re.search(p, ln): d["major_" + k] += 1
        if re.search(r"خانم|سرکار", ln): d["n_female_marker"] += 1
        if re.search(r"شخص حقوقی|نماینده", ln): d["n_legal_rep"] += 1
    d = dict(d); d["board_lines"] = len(raw); d["board_raw"] = " || ".join(raw[:40])
    return d

def cmd_board():
    rows = []
    for s, y, c, tn, t in load_texts(["board_members", "board_report"]):
        d = parse_board(t); d.update(Symbol=s, year=y, TracingNo=tn, cat=c); rows.append(d)
    df = pd.DataFrame(rows)
    if df.empty: print("متنی نبود"); return
    df = df.sort_values("board_lines").drop_duplicates(["Symbol", "year"], keep="last")
    df.to_csv(OUT / "extra_board.csv", index=False, encoding="utf-8-sig"); print("extra_board.csv:", df.shape)

# ---------------- ۶) واژه‌نامه (فناوری، ESG، ریسک ...) ----------------
def lex_counts(t):
    t = norm(t); w = max(len(t.split()), 1); d = {"words": w}
    for k, terms in LEXICONS.items():
        n = sum(len(re.findall(re.escape(norm(x)), t)) for x in terms)
        d[k + "_n"] = n; d[k + "_per1000"] = round(1000 * n / w, 4)
    return d

def cmd_keywords():
    rows = []
    for s, y, c, tn, t in load_texts(["board_report", "esg", "fs_annual"]):
        d = lex_counts(t); d.update(Symbol=s, year=y, cat=c); rows.append(d)
    df = pd.DataFrame(rows)
    if df.empty: print("متنی نبود"); return
    num = [c for c in df if c.endswith("_n") or c.endswith("_per1000") or c == "words"]
    g = df.groupby(["Symbol", "year", "cat"])[num].max().reset_index()
    w = g.pivot_table(index=["Symbol", "year"], columns="cat", values=[c for c in num if c.endswith("_per1000")])
    w.columns = [f"{a}_{b}" for a, b in w.columns]
    w.reset_index().to_csv(OUT / "extra_keywords.csv", index=False, encoding="utf-8-sig"); print("extra_keywords.csv:", w.shape)

# ---------------- ۷) نیروی انسانی ----------------
EMP = [r"(?:تعداد|میانگین)[^\n\d]{0,40}کارکنان[^\n\d]{0,40}([\d,]{1,9})", r"([\d,]{1,9})\s*نفر\s*(?:کارکن|پرسنل)",
       r"تعداد\s*پرسنل[^\n\d]{0,30}([\d,]{1,9})"]
def parse_emp(t):
    t = norm(t); vals = []
    for p in EMP:
        for m in re.finditer(p, t):
            try: v = int(m.group(1).replace(",", ""))
            except ValueError: continue
            if 1 <= v <= 500000: vals.append(v)
    d = {"n_employees": vals[0] if vals else None, "n_emp_mentions": len(vals)}
    for k, p in {"emp_phd": r"دکتری[^\n\d]{0,20}(\d+)", "emp_msc": r"کارشناسی ارشد[^\n\d]{0,20}(\d+)",
                 "emp_bsc": r"(?<!ارشد )کارشناسی[^\n\d]{0,20}(\d+)", "emp_contract": r"قراردادی[^\n\d]{0,20}(\d+)",
                 "emp_permanent": r"(?:رسمی|دائم)[^\n\d]{0,20}(\d+)"}.items():
        m = re.search(p, t); d[k] = int(m.group(1)) if m else None
    return d

def cmd_employees():
    rows = []
    for s, y, c, tn, t in load_texts(["board_report", "fs_annual"]):
        d = parse_emp(t); d.update(Symbol=s, year=y); rows.append(d)
    df = pd.DataFrame(rows)
    if df.empty: print("متنی نبود"); return
    df = df.sort_values("n_emp_mentions").drop_duplicates(["Symbol", "year"], keep="last")
    df.to_csv(OUT / "extra_employees.csv", index=False, encoding="utf-8-sig"); print("extra_employees.csv:", df.shape)

# ---------------- ۸) مالکیت (از خروجی tse_holders.csv در rohi_all.py: Symbol,date,holder,pct) ----------------
OWNER_TYPES = {
  "state":  r"وزارت|سازمان (?:تامین اجتماعی|خصوصی سازی|گسترش)|دولت|شرکت ملی|بنیاد|ستاد|سپاه|بانک (?:ملی|صادرات|سپه|ملت|تجارت|رفاه|کشاورزی|مسکن)|صندوق بازنشستگی|بازنشستگی کشوری|تامین اجتماعی|شستا|ایدرو|ایمیدرو|هلدینگ.*(?:دولت|ملی)",
  "inst":   r"صندوق سرمایه ?گذاری|سرمایه ?گذاری|بیمه|بانک|لیزینگ|کارگزاری|هلدینگ|گروه",
  "fund":   r"صندوق",
  "foreign":r"خارجی|Ltd|Limited|Inc|GmbH",
}
def cmd_ownership():
    f = OUT / "tse_holders.csv"
    if not f.exists(): print("tse_holders.csv نیست (rohi_all.py tse را اجرا کنید)"); return
    h = pd.read_csv(f); h["pct"] = pd.to_numeric(h["pct"], errors="coerce")
    d = pd.to_datetime(h["date"].astype(str), format="%Y%m%d", errors="coerce")
    h["year"] = [g2j(x.year, x.month, x.day)[0] if pd.notna(x) else None for x in d]
    for k, p in OWNER_TYPES.items(): h["is_" + k] = h["holder"].astype(str).map(norm).str.contains(p, regex=True).astype(int)
    h = h.dropna(subset=["year", "pct"]); rows = []
    for (s, y), g in h.groupby(["Symbol", "year"]):
        g = g.sort_values("pct", ascending=False)
        r = {"Symbol": s, "year": int(y), "TOP1": g["pct"].iloc[0], "TOP3": g["pct"].head(3).sum(), "TOP5": g["pct"].head(5).sum(),
             "HHI5": ((g["pct"].head(5) / 100) ** 2).sum(), "N_HOLD_5PCT": int((g["pct"] >= 5).sum())}
        for k in OWNER_TYPES: r[k.upper() + "_PCT"] = (g["pct"] * g["is_" + k]).sum()
        rows.append(r)
    pd.DataFrame(rows).to_csv(OUT / "extra_ownership.csv", index=False, encoding="utf-8-sig")
    print("extra_ownership.csv:", len(rows), "(طبقه‌بندی نام‌ها را با نمونه دستی کنترل کنید)")

# ---------------- ۹) بازار (از tse_prices.csv: Symbol,date,close) ----------------
def cmd_market():
    f = OUT / "tse_prices.csv"
    if not f.exists(): print("tse_prices.csv نیست"); return
    p = pd.read_csv(f); p["close"] = pd.to_numeric(p["close"], errors="coerce")
    d = pd.to_datetime(p["date"].astype(str), format="%Y%m%d", errors="coerce")
    p["year"] = [g2j(x.year, x.month, x.day)[0] if pd.notna(x) else None for x in d]
    p = p.dropna(subset=["year", "close"]).sort_values(["Symbol", "date"]); rows = []
    for (s, y), g in p.groupby(["Symbol", "year"]):
        r = g["close"].pct_change().dropna()
        rows.append({"Symbol": s, "year": int(y), "price_end": g["close"].iloc[-1], "price_start": g["close"].iloc[0],
                     "RET": g["close"].iloc[-1] / g["close"].iloc[0] - 1, "VOL": r.std() * math.sqrt(len(r)) if len(r) > 1 else None,
                     "n_trading_days": len(g)})
    pd.DataFrame(rows).to_csv(OUT / "extra_market.csv", index=False, encoding="utf-8-sig")
    print("extra_market.csv:", len(rows), "(جزئیات حجم و ارزش معاملات را در صورت نیاز به tse_collector بیفزایید)")

# ---------------- ۱۰) ادغام با پنل شما + متغیرهای کلان (اختیاری: macro.csv با ستون year) ----------------
def cmd_merge():
    p = OUT / "my_panel.csv"
    if not p.exists(): sys.exit("data_out/my_panel.csv (ستون‌های Symbol,year) را بگذارید")
    base = pd.read_csv(p)
    for f in sorted(OUT.glob("extra_*.csv")):
        if f.name == "extra_need_ocr.csv": continue
        x = pd.read_csv(f)
        if {"Symbol", "year"} <= set(x.columns):
            x = x.drop(columns=[c for c in x.columns if c in base.columns and c not in ("Symbol", "year")])
            base = base.merge(x, on=["Symbol", "year"], how="left")
    m = OUT / "macro.csv"
    if m.exists(): base = base.merge(pd.read_csv(m), on="year", how="left")
    base.to_csv(OUT / "panel_full.csv", index=False, encoding="utf-8-sig")
    sd = base.drop(columns=[c for c in base if c in ("board_raw", "signature_block", "cat", "TracingNo")], errors="ignore")
    sd = sd.dropna(axis=1, how="all"); seen = set(); ren = {}
    for c in sd.columns:
        n = re.sub(r"\W", "_", str(c))[:32]; k = 1
        while n in seen: n = n[:30] + f"{k}"; k += 1
        seen.add(n); ren[c] = n
    try: sd.rename(columns=ren).to_stata(OUT / "panel_full.dta", write_index=False, version=118)
    except Exception as e: print("dta ذخیره نشد:", e)
    cov = base.notna().mean().sort_values()
    print("panel_full:", base.shape); print("کمترین پوشش:\n", cov.head(25))

# ---------------- CLI / Colab ----------------
def run(cmd, from_="1390/01/01", to="1404/12/29", limit=0):
    {"list": lambda: cmd_list(from_, to), "events": cmd_events, "download": lambda: cmd_download(limit),
     "text": cmd_text, "board": cmd_board, "keywords": cmd_keywords, "employees": cmd_employees,
     "ownership": cmd_ownership, "market": cmd_market, "merge": cmd_merge}[cmd]()

if __name__ == "__main__" and "ipykernel" not in sys.modules:
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--from", dest="f", default="1390/01/01")
    ap.add_argument("--to", default="1404/12/29"); ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args(); run(a.cmd, a.f, a.to, a.limit)
