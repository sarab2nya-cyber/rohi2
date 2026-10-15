#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
کد جامع داده‌های غیرمالی شرکت‌های بورسی (۱۳۹۰-۱۴۰۴) برای پژوهش‌های حسابداری/مالی.
خروجی همه ماژول‌ها: data_out/extra_<module>.csv با کلید Symbol, year  ← در مرحله merge به پنل شما وصل می‌شود.

فلسفه: (۱) همه نامه‌های هر نماد را بگیر؛ (۲) فقط با «عنوان» دسته‌بندی کن؛ (۳) متن دسته‌های لازم را ذخیره کن؛
(۴) از متن‌ها متغیر بساز. متن‌ها ذخیره می‌مانند تا برای پژوهش بعدی فقط الگوی جدید بنویسید.

نصب: pip install requests pandas beautifulsoup4 lxml pdfplumber
ورودی: data_out/my_symbols.csv با ستون Symbol  (و اختیاری my_panel.csv با Symbol,year)
ترتیب: list → events → download → text → audit → audpanel → gov → board → behav → tech → keywords → employees → ownership → merge
Colab: run('list') ... run('merge')   (بازار حذف شد: قیمت/بازده در صورت‌های مالی شماست)

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
    "forecast":       r"پیش.?بینی (سود|عملکرد|درآمد|هر سهم)|گزارش پیش.?بینی",
    "insider":        r"معاملات (مدیران|اشخاص مطلع|سهامداران عمده|اشخاص وابسته به مدیر)|اشخاص (مطلع|درون سازمانی)",
    "other":          r".*",
}
_PRI = ["forecast", "insider", "ceo_change", "auditor_change", "capital_incr", "dividend", "fs_interim"]
CAT_ORDER = _PRI + [c for c in CATEGORIES if c not in _PRI]

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
  # --- مالی رفتاری: لحن و اطمینان مدیریت ---
  "tone_pos":  ["بهبود", "رشد", "موفقیت", "دستاورد", "مطلوب", "پیشرفت", "فرصت", "توسعه", "تقویت", "سودآور", "افزایش فروش", "افزایش سودآوری"],
  "tone_neg":  ["کاهش", "زیان", "افت", "نامطلوب", "مشکل", "چالش", "محدودیت", "ضعف", "کسری", "رکود", "ناکارآمد", "توقف"],
  "tone_unc":  ["ابهام", "نامشخص", "احتمال", "ممکن است", "نوسان", "عدم اطمینان", "ریسک"],
  "tone_cert": ["قطعا", "حتما", "مسلما", "بدون تردید", "اطمینان", "تضمین", "قاطعانه"],
  "attrib_int":["تلاش مدیریت", "مدیریت شرکت", "برنامه ریزی", "اقدامات مدیریت", "سیاست های مدیریت", "عملکرد مناسب"],
  "attrib_ext":["تحریم", "دولت", "قیمت گذاری دستوری", "شرایط اقتصادی", "عوامل خارجی", "نرخ ارز", "تورم", "مقررات", "شرایط بازار"],
  # --- فناوری (شاخص‌های بیشتر) ---
  "tech_it":   ["erp", "سیستم یکپارچه", "امنیت سایبری", "زیرساخت فناوری اطلاعات", "مرکز داده", "سامانه", "برنامه ریزی منابع"],
  "tech_ecom": ["فروش اینترنتی", "کسب و کار الکترونیک", "فروشگاه اینترنتی", "تجارت الکترونیک", "پلتفرم"],
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
                 "auditor_change", "ceo_change", "capital_incr", "dividend", "related_party", "forecast", "insider"]
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


# ---------------- حسابرس (از گزارش حسابرس داخل صورت‌های مالی سالانه) ----------------
A_START = re.compile(r"گزارش\s*حسابرس\s*مستقل|گزارش\s*حسابرس\s*و\s*بازرس\s*قانونی")
A_END = re.compile(r"صورت\s*وضعیت\s*مالی|ترازنامه|صورت\s*سود\s*و\s*زیان")
A_FIRM = re.compile(r"((?:سازمان|مؤسسه|موسسه)\s*حسابرسی\s*[^\n\d:،.]{0,45}|[^\n\d]{2,30}\s*حسابداران\s*رسمی(?:\s*[^\n\d]{0,20})?)")
A_DATE = re.compile(r"(1[34]\d{2})/(\d{1,2})/(\d{1,2})")
A_FLAGS = {
    "going_concern": r"تداوم\s*فعالیت|ابهام\s*با\s*اهمیت", "emphasis_para": r"تأکید\s*بر\s*مطلب|بند\s*تأکید|تاکید\s*بر\s*مطلب",
    "kam": r"امور\s*عمده\s*حسابرسی|مسائل\s*عمده\s*حسابرسی", "related_party": r"اشخاص\s*وابسته",
    "internal_control": r"کنترل\s*های\s*داخلی", "aml": r"پولشویی|تأمین\s*مالی\s*تروریسم",
    "other_legal_reqs": r"سایر\s*الزامات\s*قانونی\s*و\s*مقرراتی", "tax": r"مالیات", "lawsuit": r"دعاوی|دعوی",
    "bank_loans": r"تسهیلات", "restated": r"تجدید\s*ارائه|تعدیل\s*سنواتی|اصلاح\s*اشتباه",
    "board_report": r"گزارش\s*هیئت\s*مدیره", "stock_exchange_rules": r"سازمان\s*بورس|دستورالعمل\s*(?:حاکمیت|افشا)",
    "corp_governance": r"حاکمیت\s*شرکتی", "dividend": r"سود\s*تقسیمی|تقسیم\s*سود", "capital_increase": r"افزایش\s*سرمایه",
    "joint_audit": r"حسابرسان\s*مشترک|بازرسان\s*قانونی", "inventory_count": r"مشاهده\s*(?:فیزیکی|موجودی)|انبارگردانی",
    "confirmations": r"تأییدیه|تاییدیه", "limitation_scope": r"محدودیت\s*در\s*دامنه|عدم\s*امکان\s*(?:دسترسی|بررسی)",
}
def a_find_report(text):
    text = norm(reverse_fix(text)); m = A_START.search(text)
    if not m: return ""
    seg = text[m.start(): m.start() + 25000]; e = A_END.search(seg, 3000)
    return seg[: e.start()] if e else seg

def opinion_type(t):
    if re.search(r"عدم\s*اظهار\s*نظر|اظهار\s*نظر\s*نمی\s*کنیم|اظهارنظر\s*نمی", t): return "disclaimer"
    if re.search(r"نامطلوب|به\s*نحو\s*مطلوب\s*ارائه\s*نشده|مطلوب\s*نمی\s*باشد|مطلوب\s*نیست", t): return "adverse"
    if re.search(r"به\s*استثنای|مشروط|به\s*استثناء", t): return "qualified"
    if re.search(r"به\s*نحو\s*مطلوب", t): return "unqualified"
    return "unknown"

def parse_report(t):
    t = norm(t); d = {"opinion": opinion_type(t)}
    d["opinion_qualified_any"] = int(d["opinion"] in ("qualified", "adverse", "disclaimer"))
    c = collections.Counter(re.sub(r"\s+", " ", x).strip(" -") for x in A_FIRM.findall(t[len(t) // 2:] or t))
    d["auditor_firm_raw"] = c.most_common(1)[0][0] if c else None
    d["signature_block"] = " | ".join([l.strip() for l in t.split("\n") if l.strip()][-12:])
    dates = A_DATE.findall(t) or [(y, m, dd) for dd, m, y in re.findall(r"(\d{1,2})/(\d{1,2})/(1[34]\d{2})", t)]
    d["report_date"] = "/".join(dates[-1]) if dates else None
    for k, pat in A_FLAGS.items():
        n = len(re.findall(pat, t)); d["aud_" + k + "_n"] = n; d["aud_" + k] = int(n > 0)
    d["n_qualification_items"] = len(re.findall(r"(?:^|\n)\s*\d+\s*[-–.)]", t))
    d["aud_report_words"] = len(t.split())
    return d

def cmd_audit():
    rows = []
    for s_, y, c, tn, t in load_texts(["fs_annual"]):
        rep = a_find_report(t)
        if len(rep) < 300: continue
        d = parse_report(rep); d.update(Symbol=s_, year=y, TracingNo=tn); rows.append(d)
    df = pd.DataFrame(rows)
    if df.empty: print("گزارش حسابرسی پیدا نشد (extra_need_ocr.csv را ببینید)"); return
    df = df.sort_values("aud_report_words").drop_duplicates(["Symbol", "year"], keep="last")
    df.to_csv(OUT / "extra_audit.csv", index=False, encoding="utf-8-sig"); print("extra_audit.csv:", df.shape)

def canon(s_):
    if not isinstance(s_, str): return None
    s_ = norm(s_); s_ = re.sub(r"(سازمان|مؤسسه|موسسه)\s*حسابرسی|حسابداران\s*رسمی|و\s*همکاران|\bو\s*شرکا", " ", s_)
    return re.sub(r"\s+", " ", s_).strip() or None

def build_audpanel(rep, assets=None):
    df = rep.dropna(subset=["Symbol", "year"]).sort_values(["Symbol", "year"]).copy()
    df["auditor"] = df["auditor_firm_raw"].map(canon)
    df.loc[df["auditor_firm_raw"].astype(str).map(norm).str.contains("سازمان حسابرسی"), "auditor"] = "سازمان حسابرسی"
    df["auditor_prev"] = df.groupby("Symbol")["auditor"].shift(1)
    df["AUDSWITCH"] = ((df["auditor"] != df["auditor_prev"]) & df["auditor_prev"].notna()).astype(int)
    ten, la, ly, cur = [], {}, {}, {}
    for s_, a, y in zip(df["Symbol"], df["auditor"], df["year"]):
        cur[s_] = cur[s_] + 1 if (s_ in la and la[s_] == a and y - ly[s_] == 1) else 1
        la[s_], ly[s_] = a, y; ten.append(cur[s_])
    df["AUDTEN"] = ten; df["AUDTEN_LN"] = df["AUDTEN"].map(math.log); df["AUDOPN"] = df["opinion_qualified_any"]
    if assets is not None and "TA" in assets:
        df = df.merge(assets, on=["Symbol", "year"], how="left")
        for k, by in (("aud", ["year", "auditor"]),):
            df = df.merge(df.groupby(by)["TA"].sum().rename("aud_assets").reset_index(), on=by)
            df = df.merge(df.groupby("year")["TA"].sum().rename("tot_assets").reset_index(), on="year")
            df = df.merge(df.groupby(by).size().rename("aud_clients").reset_index(), on=by)
        df["AUD_SHARE_MKT"] = df["aud_assets"] / df["tot_assets"]
        df["AUDSIZE"] = df.groupby("year")["aud_assets"].transform(lambda x: (x >= x.quantile(0.75)).astype(int))
        df.loc[df["auditor"] == "سازمان حسابرسی", "AUDSIZE"] = 1
        if "sector" in df:
            df = df.merge(df.groupby(["year", "sector", "auditor"])["TA"].sum().rename("aud_ind").reset_index(), on=["year", "sector", "auditor"])
            df = df.merge(df.groupby(["year", "sector"])["TA"].sum().rename("ind_tot").reset_index(), on=["year", "sector"])
            df["AUDSPEC"] = (df["aud_ind"] / df["ind_tot"] > 0.15).astype(int)
    return df

def cmd_audpanel():
    rep = pd.read_csv(OUT / "extra_audit.csv"); pth = OUT / "my_panel.csv"; assets = None
    if pth.exists():
        pp = pd.read_csv(pth); cols = [c for c in ("Symbol", "year", "TA", "sector") if c in pp]; assets = pp[cols]
    build_audpanel(rep, assets).to_csv(OUT / "extra_audpanel.csv", index=False, encoding="utf-8-sig")
    print("extra_audpanel.csv ؛ ستون auditor را برای یکسان‌سازی نام‌ها دستی بررسی کنید (TA/sector را در my_panel بگذارید)")

# ---------------- حاکمیت شرکتی، کمیته حسابرسی، حسابرس داخلی ----------------
def _win(t, pat, n=300):
    return [t[m.end(): m.end() + n] for m in re.finditer(pat, t)]
def _num_before(w, unit):
    m = re.search(r"(\d{1,3})\s*" + unit, w); return int(m.group(1)) if m else None

def parse_gov(t):
    t = norm(t); d = {}
    ac = _win(t, r"کمیته\s*حسابرسی")
    d["has_audit_cmte"] = int(len(ac) > 0); d["audit_cmte_mentions"] = len(ac)
    mt = [_num_before(w[:60], r"جلسه") for w in ac]; mt = [x for x in mt if x]
    d["audit_cmte_meetings"] = mt[0] if mt else None
    d["audit_cmte_indep"] = int(any(re.search(r"مستقل", w) for w in ac))
    d["audit_cmte_finexp"] = int(any(re.search(r"تخصص\s*مالی|حسابدار|حسابرس|مالی", w) for w in ac))
    d["audit_cmte_raw"] = (ac[0][:400] if ac else None)
    for k, p in {"risk_cmte": r"کمیته\s*مدیریت\s*ریسک|کمیته\s*ریسک", "nom_rem_cmte": r"کمیته\s*(?:انتصابات|جبران|حقوق\s*و\s*مزایا|تعیین\s*حقوق)",
                 "investment_cmte": r"کمیته\s*سرمایه\s*گذاری", "governance_cmte": r"کمیته\s*حاکمیت", "compliance_unit": r"مسئول\s*انطباق|واحد\s*انطباق|تطبیق"}.items():
        d[k] = int(bool(re.search(p, t)))
    d["n_cmte_types"] = len(set(re.findall(r"کمیته\s*([^\s،.:\d]{2,15}(?:\s*[^\s،.:\d]{2,12})?)", t)))
    ia = _win(t, r"حسابرسی\s*داخلی|حسابرس\s*داخلی|واحد\s*حسابرسی")
    d["has_internal_audit"] = int(len(ia) > 0)
    st = [re.search(r"(\d{1,3})\s*نفر", w[:120]) for w in ia]; st = [int(m.group(1)) for m in st if m]
    d["internal_audit_staff"] = max(st) if st else None
    d["internal_audit_outsourced"] = int(bool(re.search(r"برون\s*سپاری|خارج\s*از\s*شرکت", " ".join(w[:150] for w in ia))))
    d["internal_audit_to_board"] = int(bool(re.search(r"گزارش.{0,20}(کمیته\s*حسابرسی|هیئت\s*مدیره)", " ".join(w[:200] for w in ia))))
    d["ic_effective"] = int(bool(re.search(r"کنترل.{0,3}های\s*داخلی.{0,40}(اثربخش|مؤثر|مطلوب)", t)))
    d["ic_weakness_n"] = len(re.findall(r"ضعف|نقطه\s*ضعف|ضعف\s*عمده|نارسایی", t))
    bm = [_num_before(w[:120], r"جلسه") for w in _win(t, r"هیئت\s*مدیره", 120)]; bm = [x for x in bm if x and x <= 100]
    d["board_meetings"] = max(bm) if bm else None
    for k, p in {"cg_directive": r"دستورالعمل\s*حاکمیت\s*شرکتی", "code_of_ethics": r"منشور\s*اخلاق|کد\s*اخلاق|اخلاق\s*حرفه", "whistleblow": r"گزارش\s*دهی\s*تخلف|افشاگر|خط\s*ارتباطی\s*امین",
                 "disclosure_policy": r"سیاست\s*افشا|سیاست\s*تقسیم\s*سود", "independent_dir": r"عضو\s*مستقل|مدیر\s*مستقل", "risk_policy": r"مدیریت\s*ریسک",
                 "shareholder_rights": r"حقوق\s*سهامداران|سهامداران\s*اقلیت", "esop": r"سهام\s*کارکنان|طرح\s*مشارکت\s*کارکنان|پاداش\s*مبتنی\s*بر\s*سهام",
                 "mgmt_comp_disclosed": r"پاداش\s*(?:هیئت\s*مدیره|مدیران)|حقوق\s*و\s*مزایای\s*مدیران"}.items():
        d[k] = int(bool(re.search(p, t)))
    return d

def cmd_gov():
    rows = []
    for s_, y, c, tn, t in load_texts(["board_report", "internal_ctrl", "board_members"]):
        d = parse_gov(t); d.update(Symbol=s_, year=y, cat=c); rows.append(d)
    df = pd.DataFrame(rows)
    if df.empty: print("متنی نبود"); return
    num = [c for c in df if c not in ("Symbol", "year", "cat", "audit_cmte_raw")]
    g = df.groupby(["Symbol", "year"])[num].max().reset_index()
    raw = df.dropna(subset=["audit_cmte_raw"]).drop_duplicates(["Symbol", "year"])[["Symbol", "year", "audit_cmte_raw"]]
    g.merge(raw, on=["Symbol", "year"], how="left").to_csv(OUT / "extra_gov.csv", index=False, encoding="utf-8-sig")
    print("extra_gov.csv:", g.shape)

# ---------------- مالی رفتاری: لحن مدیریت، اطمینان، نسبت‌دادن، پیش‌بینی سود، معاملات مطلعین ----------------
def tone(t):
    c = lex_counts(t); pos, neg = c["tone_pos_n"], c["tone_neg_n"]
    d = {"TONE_NET": (pos - neg) / (pos + neg) if pos + neg else None,
         "TONE_UNC": c["tone_unc_per1000"], "TONE_CERT": c["tone_cert_per1000"],
         "ATTRIB_INT": c["attrib_int_n"], "ATTRIB_EXT": c["attrib_ext_n"],
         "SELF_SERVING": (c["attrib_int_n"] - c["attrib_ext_n"]) / max(c["attrib_int_n"] + c["attrib_ext_n"], 1),
         "OVERCONF_PROXY": c["tone_cert_per1000"] - c["tone_unc_per1000"], "tone_words": c["words"]}
    return d

def _paren_num(x):
    x = x.replace(",", "").strip(); neg = x.startswith("(") or x.startswith("-")
    x = re.sub(r"[()\-]", "", x)
    try: v = float(x)
    except ValueError: return None
    return -v if neg else v

def parse_forecast(t):
    t = norm(t); m = re.search(r"(?:سود|زیان)\s*(?:\(زیان\)\s*)?(?:خالص\s*)?هر\s*سهم[^\d\-\(]{0,40}(\(?-?[\d,]+\)?)", t)
    return _paren_num(m.group(1)) if m else None

def cmd_behav():
    rows = []
    for s_, y, c, tn, t in load_texts(["board_report", "esg"]):
        d = tone(t); d.update(Symbol=s_, year=y); rows.append(d)
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values("tone_words").drop_duplicates(["Symbol", "year"], keep="last")
    fr = []
    for s_, y, c, tn, t in load_texts(["forecast"]):
        fr.append({"Symbol": s_, "year": y, "TracingNo": tn, "f_eps": parse_forecast(t)})
    if fr:
        f = pd.DataFrame(fr).sort_values("TracingNo"); g = f.groupby(["Symbol", "year"])
        agg = g.agg(n_forecast=("TracingNo", "count"), forecast_eps_first=("f_eps", "first"), forecast_eps_last=("f_eps", "last")).reset_index()
        agg["forecast_revision"] = agg["forecast_eps_last"] - agg["forecast_eps_first"]
        out = agg if out.empty else out.merge(agg, on=["Symbol", "year"], how="outer")
    ev = OUT / "extra_events.csv"
    if ev.exists():
        e = pd.read_csv(ev); cols = [c for c in e if c in ("Symbol", "year", "n_insider", "d_insider", "n_dividend", "n_capital_incr")]
        out = out.merge(e[cols], on=["Symbol", "year"], how="outer") if not out.empty else e[cols]
    out.to_csv(OUT / "extra_behav.csv", index=False, encoding="utf-8-sig")
    print("extra_behav.csv:", out.shape, "(خطای پیش‌بینی FE در مرحله merge از ستون EPS پنل شما ساخته می‌شود)")

# ---------------- فناوری ----------------
def parse_tech(t):
    t = norm(t); d = {}
    m = re.findall(r"(\d{1,4})\s*(?:مورد\s*)?(?:گواهی\s*)?ثبت\s*اختراع|ثبت\s*اختراع[^\n\d]{0,20}(\d{1,4})", t)
    d["n_patents"] = max([int(a or b) for a, b in m]) if m else None
    for k, p in {"has_rd_unit": r"واحد\s*تحقیق\s*و\s*توسعه|مرکز\s*تحقیق|R&D|آزمایشگاه\s*تحقیق", "knowledge_based": r"دانش\s*بنیان",
                 "has_erp": r"\bERP\b|برنامه\s*ریزی\s*منابع\s*سازمان", "cyber": r"امنیت\s*سایبری|امنیت\s*اطلاعات",
                 "ecommerce": r"فروش\s*اینترنتی|تجارت\s*الکترونیک|فروشگاه\s*اینترنتی", "ai_bigdata": r"هوش\s*مصنوعی|کلان\s*داده|یادگیری\s*ماشین|اینترنت\s*اشیا",
                 "automation": r"اتوماسیون|رباتیک|خط\s*تولید\s*هوشمند", "iso_cert": r"ISO|استاندارد\s*ملی", "tech_transfer": r"انتقال\s*فناوری|دانش\s*فنی|لیسانس\s*تولید"}.items():
        d[k] = int(bool(re.search(p, t, re.I)))
    m = re.search(r"(?:هزینه|مخارج)\s*تحقیق\s*و\s*توسعه[^\d\(]{0,30}(\(?[\d,]+\)?)", t); d["rd_expense_text"] = _paren_num(m.group(1)) if m else None
    c = lex_counts(t); d["TECH_IDX"] = c["tech_per1000"]; d["TECH_IT_IDX"] = c["tech_it_per1000"]; d["TECH_ECOM_IDX"] = c["tech_ecom_per1000"]
    return d

def cmd_tech():
    rows = []
    for s_, y, c, tn, t in load_texts(["board_report", "esg", "fs_annual"]):
        d = parse_tech(t); d.update(Symbol=s_, year=y); rows.append(d)
    df = pd.DataFrame(rows)
    if df.empty: print("متنی نبود"); return
    num = [c for c in df if c not in ("Symbol", "year")]
    df.groupby(["Symbol", "year"])[num].max().reset_index().to_csv(OUT / "extra_tech.csv", index=False, encoding="utf-8-sig")
    print("extra_tech.csv:", df.groupby(["Symbol", "year"]).ngroups)

# ---------------- ۱۰) ادغام با پنل شما + متغیرهای کلان (اختیاری: macro.csv با ستون year) ----------------
def cmd_merge():
    p = OUT / "my_panel.csv"
    if not p.exists(): sys.exit("data_out/my_panel.csv (ستون‌های Symbol,year) را بگذارید")
    base = pd.read_csv(p)
    for f in sorted(OUT.glob("extra_*.csv")):
        if f.name in ("extra_need_ocr.csv", "extra_audit.csv"): continue   # extra_audpanel جایگزین extra_audit است
        x = pd.read_csv(f)
        if {"Symbol", "year"} <= set(x.columns):
            x = x.drop(columns=[c for c in x.columns if c in base.columns and c not in ("Symbol", "year")])
            base = base.merge(x, on=["Symbol", "year"], how="left")
    base = base.copy()
    if {"forecast_eps_first", "EPS"} <= set(base.columns):     # EPS واقعی در پنل شما
        base["FE_FIRST"] = (base["EPS"] - base["forecast_eps_first"]) / base["forecast_eps_first"].abs()
        base["FE_LAST"] = (base["EPS"] - base["forecast_eps_last"]) / base["forecast_eps_last"].abs()
        base["FORECAST_OPTIMISM"] = (base["forecast_eps_first"] > base["EPS"]).astype(float)
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
     "text": cmd_text, "audit": cmd_audit, "audpanel": cmd_audpanel, "gov": cmd_gov, "board": cmd_board,
     "behav": cmd_behav, "tech": cmd_tech, "keywords": cmd_keywords, "employees": cmd_employees,
     "ownership": cmd_ownership, "merge": cmd_merge}[cmd]()

if __name__ == "__main__" and "ipykernel" not in sys.modules:
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--from", dest="f", default="1390/01/01")
    ap.add_argument("--to", default="1404/12/29"); ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args(); run(a.cmd, a.f, a.to, a.limit)
