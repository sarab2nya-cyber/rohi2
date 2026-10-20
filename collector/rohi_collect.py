# -*- coding: utf-8 -*-
"""
rohi_collect.py — جمع‌آوری یک‌مرحله‌ای و جریانی داده‌های کدال + TSETMC برای شرکت‌های نمونه (۱۳۹۴–۱۴۰۴)

 • به ازای هر شرکت، همه‌چیز در یک عبور: TSETMC (بازار) + فهرست نامه‌های کدال (رویدادها) + اکسل صورت مالی سالانه
   حسابرسی‌شده (هیئت مدیره، کمیته‌ها، مدیرعامل، کارکنان، فروش صادراتی، وضعیت ارزی، برآوردها).
 • هیچ سندی روی دیسک نگه داشته نمی‌شود (فقط جدول ویژگی‌ها).
 • مؤدب و کپچا-آگاه: فاصله بین درخواست‌های کدال، سقف روزانه، و توقف فوری در صورت کپچا/۴۲۹ (دور زدن نمی‌کند).
 • ادامه‌پذیر: هر شرکت/نامه پس از پردازش ثبت می‌شود؛ اجرای دوباره از همان‌جا ادامه می‌دهد.

اجرا (ویندوز، فیلترشکن خاموش):
   python rohi_collect.py --symbols my_symbols.csv --pilot 3          # آزمایشی: ۳ شرکت
   python rohi_collect.py --symbols my_symbols.csv                    # اجرای کامل (ادامه‌پذیر)
   python rohi_collect.py --build                                     # ساخت جدول نهایی از نتایج ذخیره‌شده
فایل my_symbols.csv: ستون‌های Symbol (نماد) ,company ,firm_id
نصب: pip install requests pandas numpy lxml openpyxl
"""
import sys as _sys
try: _sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
import argparse, csv, io, json, math, os, random, re, sys, time, unicodedata, collections
import numpy as np, pandas as pd, requests

CODAL_SEARCH = "https://search.codal.ir/api/search/v2/q"; CODAL = "https://codal.ir"; TSE = "https://cdn.tsetmc.com/api"
UA = {"User-Agent": "Mozilla/5.0 (research; academic use)", "Accept": "*/*"}
_DIG = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

def norm(s):
    s = unicodedata.normalize("NFKC", str(s)).translate(_DIG)
    s = s.replace("ي", "ی").replace("ك", "ک").replace("‌", " ").replace("‏", "").replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()

def num(x):
    s = norm(x).replace(",", "").replace("٬", "")
    neg = s.startswith("(") and s.endswith(")"); s = s.strip("()")
    try: v = float(s); return -v if neg else v
    except ValueError: return None

# ------------------------------------------------------------------ تاریخ شمسی/میلادی
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

def j2g(jy, jm, jd):
    jy += 1595
    days = -355668 + 365 * jy + (jy // 33) * 8 + ((jy % 33) + 3) // 4 + jd + ((jm - 1) * 31 if jm < 7 else (jm - 7) * 30 + 186)
    gy = 400 * (days // 146097); days %= 146097
    if days > 36524:
        days -= 1; gy += 100 * (days // 36524); days %= 36524
        if days >= 365: days += 1
    gy += 4 * (days // 1461); days %= 1461
    if days > 365: gy += (days - 1) // 365; days = (days - 1) % 365
    gd = days + 1
    sal = [0, 31, 29 if (gy % 4 == 0 and gy % 100 != 0) or gy % 400 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 0
    while gm < 13 and gd > sal[gm]: gd -= sal[gm]; gm += 1
    return gy, gm, gd

def jdate(s):
    m = re.search(r"(1[34]\d{2})/(\d{1,2})/(\d{1,2})", norm(s))
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None

def to_ord(y, m, d):  # ترتیب‌پذیر
    return y * 10000 + m * 100 + d

# ------------------------------------------------------------------ عنوان نامه‌ها
CODES = {  # LetterCode → دسته
 "ن-10": "fs", "ن-11": "board_report", "ن-12": "internal_control", "ن-13": "dividend", "ن-30": "monthly", "ن-41": "audit_committee_unit",
 "ن-45": "board_change", "ن-86": "nomination_committee", "ن-20": "material_info", "ن-21": "clarify_rumor", "ن-22": "clarify_price", "ن-26": "fs_explain",
 "ن-23": "conference", "ب-9": "conference_need", "ن-50": "agm_invite", "ن-51": "agm_summary", "ن-52": "agm_decision", "ن-42": "agm_register",
 "ن-53": "agm_invite", "ن-54": "agm_invite", "ن-55": "agm_decision", "ن-56": "egm_invite", "ن-57": "egm_decision", "ن-58": "agm_cancel",
 "ن-60": "capinc", "ن-61": "capinc", "ن-62": "capinc", "ن-67": "capinc", "ن-81": "shareholder_info", "ن-74": "energy_cost", "ن-84": "land_buildings",
 "ن-69": "share_transfer", "ن-43": "articles", "ن-80": "address_change", "س-5": "trading_halt", "س-7": "trading_halt",
}
def lcode(c):
    c = norm(c).split("،")[0].strip().replace("ف ", ""); return c
def classify(code, title):
    c = lcode(code); t = norm(title)
    if c in CODES: return CODES[c]
    if c.startswith("ب-"): return "regulator_warning"
    if c.startswith("س-"): return "trading_halt"
    if "کمیته ریسک" in t: return "risk_committee"
    if "کمیته حسابرسی" in t: return "audit_committee_unit"
    if "کمیته" in t: return "committee_other"
    return "other"

def parse_title(title):
    t = norm(title); d = {}
    m = re.search(r"منتهی به (\d{4}/\d{2}/\d{2})", t); d["fye"] = m.group(1) if m else None
    d["fiscal_year"] = int(m.group(1)[:4]) if m else None
    d["interim"] = int(bool(re.search(r"میان ?دوره|دوره (3|6|9) ماهه", t)))
    d["audited"] = int("حسابرسی شده" in t); d["unaudited"] = int("حسابرسی نشده" in t)
    d["consolidated"] = int("تلفیقی" in t); d["amendment"] = int("اصلاحیه" in t)
    d["other_company"] = int(bool(re.search(r"\(شرکت [^)]+\)", t)))
    d["annual"] = int(("سال مالی" in t or "دوره 12 ماهه" in t) and not d["interim"])
    return d

# ------------------------------------------------------------------ مشتری مؤدب کدال
NO_EXTRACT = False   # حالت فقط‌دانلود: متن PDF/اکسل استخراج نمی‌شود

class Blocked(Exception): pass

class Codal:
    def __init__(self, min_interval=7.0, max_requests=700, log=print, cookie=None, user_agent=None, search_interval=None):
        self.min_interval, self.max_requests, self.n, self.last, self.log = min_interval, max_requests, 0, 0.0, log
        self.search_interval = search_interval if search_interval is not None else min_interval
        self.s = requests.Session(); self.s.headers.update(UA)
        if user_agent: self.s.headers["User-Agent"] = user_agent
        if cookie: self.s.headers["Cookie"] = cookie
    def _wait(self, interval=None):
        dt = time.time() - self.last; need = (interval if interval is not None else self.min_interval) * random.uniform(1.0, 1.5)
        if dt < need: time.sleep(need - dt)
        self.last = time.time()
    def get(self, url, params=None, stream=False, expect_json=False, interval=None):
        if self.n >= self.max_requests: raise Blocked("سقف درخواست این اجرا (%d) تمام شد؛ دوباره اجرا کنید (ادامه می‌دهد)." % self.max_requests)
        self._wait(interval); self.n += 1
        try: r = self.s.get(url, params=params, timeout=(10, 40), stream=stream)
        except Exception as e: self.log("   خطای شبکه:", type(e).__name__); return None
        ct = r.headers.get("Content-Type", "")
        if r.status_code == 429: raise Blocked("کدال ۴۲۹ داد (محدودیت نرخ) برای: " + str(url)[:90])
        if "html" in ct and not stream and re.search(r"<title>\s*تأیید کاربر", r.text[:3000]): raise Blocked("کدال صفحهٔ کپچا (تأیید کاربر) داد برای: %s (%d بایت)" % (str(url)[:90], len(r.text)))
        return r
    def search(self, symbol, fy_from, fy_to, page, letter_type="-1"):
        p = {"Symbol": symbol, "Length": "-1", "LetterType": str(letter_type), "Category": "-1", "PageNumber": str(page), "search": "true", "Publisher": "false",
             "Mains": "true", "Childs": "true", "TracingNo": "-1", "AuditorRef": "-1", "CompanyState": "0", "CompanyType": "-1",
             "FromDate": f"{fy_from}/01/01", "ToDate": f"{fy_to + 1}/12/29"}
        r = self.get(CODAL_SEARCH, params=p, interval=self.search_interval)
        if r is None or r.status_code != 200: return None
        try: return r.json()
        except Exception: raise Blocked("پاسخ جست‌وجو JSON نبود (احتمالاً محدودیت).")
    def list_letters(self, symbol, fy_from, fy_to, types=("-1",), state=None, save=None):
        """فهرست نامه‌ها؛ با state/save پیشرفت صفحه‌به‌صفحه ذخیره می‌شود تا بعد از توقف از همان صفحه ادامه یابد"""
        state = state if state is not None else {}
        out = state.setdefault("out", []); seen = {x.get("TracingNo") for x in out}
        for ti in range(state.get("ti", 0), len(types)):
            page = state.get("page", 1) if ti == state.get("ti", 0) else 1
            while True:
                j = self.search(symbol, fy_from, fy_to, page, types[ti])
                if j is None: raise Blocked(f"صفحهٔ {page} جست‌وجوی {symbol} (نوع {types[ti]}) خوانده نشد؛ پیشرفت ذخیره است")
                L = j.get("Letters") or []
                for x in L:
                    if x.get("TracingNo") not in seen: seen.add(x.get("TracingNo")); out.append(x)
                last = (not L) or page >= int(j.get("Page", page))
                state["ti"], state["page"] = (ti + 1, 1) if last else (ti, page + 1)
                if save: save()
                if last: break
                page += 1
        return out
    def excel(self, url):
        self.excel_err = None
        r = self.get(url, stream=True)
        if r is None or r.status_code != 200: self.excel_err = "HTTP " + (str(r.status_code) if r is not None else "None"); return None
        data = r.content
        ok = data[:20].lstrip().lower().startswith((b"<html", b"<!doc", b"<?xml")) or b"<table" in data[:5000]
        if not ok: self.excel_err = "نوع=%s حجم=%d شروع=%r" % (r.headers.get("Content-Type"), len(data), data[:40])
        return data.decode("utf-8", "replace") if ok else None

# ------------------------------------------------------------------ پارس اکسل کدال (HTML-xls)
def split_sections(html_text):
    parts = re.split(r"<h3>\s*(.*?)\s*</h3>", html_text, flags=re.S)
    return [(norm(re.sub(r"<[^>]+>", " ", parts[i])), parts[i + 1]) for i in range(1, len(parts) - 1, 2)]

def read_tables(body):
    try: tabs = pd.read_html(io.StringIO(body))
    except Exception: return []
    out = []
    for t in tabs:
        t = t.copy()
        t.columns = [" ".join(norm(x) for x in (c if isinstance(c, tuple) else (c,)) if not str(x).startswith("Unnamed")).strip() for c in t.columns]
        out.append(t)
    return out

def txt(body): return norm(re.sub(r"<[^>]+>", " ", body))

def find_col(df, *keys):
    for c in df.columns:
        if all(k in norm(c) for k in keys): return c
    return None

def parse_excel(html_text):
    """خروجی: dict ویژگی‌ها + فهرست اعضای هیئت‌مدیره"""
    f = {}; members = []
    secs = split_sections(html_text)
    f["xl_sections"] = len(secs); f["interp_report"] = int(any("گزارش تفسیر" in t for t, _ in secs))
    full = txt(html_text)
    for title, body in secs:
        tabs = read_tables(body); T = txt(body)
        if "اعضا" in title and "هیئت" in norm(title).replace("ئ", "ئ"):
            for df in tabs:
                role = find_col(df, "سمت"); ex = find_col(df, "موظف"); edu = find_col(df, "مقطع"); maj = find_col(df, "رشته"); nm = find_col(df, "نماینده", "جدید"); nm2 = find_col(df, "نام عضو", "جدید"); idc = find_col(df, "ثبت")
                if role is None or ex is None: continue
                if len(df) and not all(str(v) for v in df[role]): continue
                members = []
                for _, r in df.iterrows():
                    if not isinstance(r[role], str): continue
                    members.append({"role": norm(r[role]), "exec": norm(r[ex]), "edu": norm(r[edu]) if edu else "", "major": norm(r[maj]) if maj else "",
                                    "member": norm(r[nm2]) if nm2 else "", "rep": norm(r[nm]) if nm and isinstance(r[nm], str) else "", "id": norm(r[idc]) if idc else ""})
        # جزئیات اعضا: تاریخ عضویت، مالکیت، عضویت همزمان، حضور در جلسات
        for df in tabs:
            c_date = find_col(df, "تاریخ عضویت"); c_nonex = find_col(df, "غیرموظف"); c_own = find_col(df, "مالکیت"); c_inter = find_col(df, "همزمان")
            if c_date and c_inter:
                f["bd_detail_rows"] = len(df); f["bd_interlock_n"] = int(sum(norm(v) in ("بلی", "بله") for v in df[c_inter]))
                own = [num(v) for v in df[c_own]] if c_own else []; f["bd_own_sum_shares"] = float(sum(x for x in own if x))
                ca = find_col(df, "کمیته حسابرسی"); cb = [c for c in df.columns if "هیات مدیره" in c and "حضور" in c]
                if ca: v = [num(x) for x in df[ca]]; f["ac_attend_total"] = float(sum(x for x in v if x)); f["ac_members_attending"] = int(sum(1 for x in v if x))
                dates = [jdate(x) for x in df[c_date] if jdate(x)]
                if dates: f["bd_tenure_min_year"] = min(d[0] for d in dates)
            # مدیرعامل
            c_resume = find_col(df, "سوابق"); c_edu2 = find_col(df, "تحصیلات"); c_nm = find_col(df, "نام و نام")
            if c_resume and c_edu2 and c_nm and len(df):
                f["ceo_name"] = norm(df[c_nm].iloc[0]); f["ceo_edu"] = norm(df[c_edu2].iloc[0]); f["ceo_resume_len"] = len(norm(df[c_resume].iloc[0]))
                o = find_col(df, "مالکیت"); f["ceo_own_shares"] = num(df[o].iloc[0]) if o else None
            # کارکنان
            c0 = df.columns[0] if len(df.columns) else None
            if c0 is not None and df[c0].astype(str).str.contains("تعداد پرسنل").any():
                for _, r in df.iterrows():
                    k = norm(r[c0]); vals = [num(v) for v in r.iloc[1:]]; vals = [v for v in vals if v is not None]
                    if "غیر تولیدی" in k and vals: f["staff_nonprod"] = vals[-2] if len(vals) >= 2 else vals[-1]
                    elif "تولیدی" in k and vals: f["staff_prod"] = vals[-2] if len(vals) >= 2 else vals[-1]
            # فروش صادراتی/داخلی
            if c0 is not None:
                col0 = df[c0].astype(str).map(norm)
                for key, nm_ in (("جمع فروش صادراتی", "export_total_row"), ("جمع فروش داخلی", "domestic_total_row")):
                    rows = df[col0.str.contains(key)]
                    if len(rows):
                        vals = [num(v) for v in rows.iloc[0, 1:]]; f[nm_] = json.dumps([v for v in vals if v is not None])
                if col0.str.contains("فروش صادراتی").any(): f["export_section"] = 1
                # جدول چندساله: مبلغ فروش و برآورد
                for key, nm_ in (("مبلغ فروش", "fc_sales"), ("سود خالص", "fc_ni"), ("سود هر سهم", "fc_eps"), ("سود ناخالص", "fc_gp"), ("سود عملیاتی", "fc_ebit")):
                    rows = df[col0.str.fullmatch(key + r"( .*)?") ]
                    if len(rows) and any("برآورد" in c for c in df.columns):
                        est_cols = [c for c in df.columns if "برآورد" in c]; cur_cols = [c for c in df.columns if "برآورد" not in c and "شرح" not in c]
                        f[nm_ + "_est"] = num(rows.iloc[0][est_cols[-1]]); f[nm_ + "_last_actual"] = num(rows.iloc[0][cur_cols[-1]]) if cur_cols else None
        # وضعیت ارزی (جدول)
        if "وضعیت ارزی" in T and "fx_section" not in f: f["fx_section"] = 1
        m = re.search(r"تعداد جلسات هیات مدیره برگزار شده[^۰-۹0-9]{0,60}?(\d+)\s*جلسه", T); f["bd_meetings"] = int(m.group(1)) if m else f.get("bd_meetings")
        for key, nm_ in (("کمیته حسابرسی", "ac_meetings"), ("کمیته انتصابات", "nom_meetings"), ("کمیته ریسک", "risk_meetings")):
            m = re.search(r"تعداد جلسات " + key + r" برگزار شده[^0-9]{0,60}?(\d+)\s*جلسه", T)
            if m: f[nm_] = int(m.group(1))
    # عضو هیئت‌مدیره: ویژگی‌ها
    if members:
        n = len(members); ne = [m for m in members if "غیر" in m["exec"]]
        f["bd_size"] = n; f["bd_nonexec_n"] = len(ne); f["bd_exec_n"] = n - len(ne); f["bd_nonexec_ratio"] = len(ne) / n
        f["bd_phd_n"] = sum("دکترا" in m["edu"] for m in members); f["bd_msc_n"] = sum("ارشد" in m["edu"] for m in members)
        f["bd_bsc_n"] = sum(("کارشناسی" in m["edu"] and "ارشد" not in m["edu"]) for m in members)
        for k, pat in {"fin": r"مالی|حسابدار|حسابرس|اقتصاد|بانک", "eng": r"مهندس|صنایع|مکانیک|برق|شیمی|عمران|نفت|معدن|فیزیک", "mgmt": r"مدیریت|بازرگانی", "law": r"حقوق"}.items():
            f["bd_major_%s_n" % k] = sum(bool(re.search(pat, m["major"])) for m in members)
        f["bd_legal_members_n"] = sum(len(re.sub(r"\D", "", m["id"])) >= 11 for m in members)
        chair = [m for m in members if "رئیس هیئت" in m["role"] and "نایب" not in m["role"]]
        f["chair_name"] = (chair[0]["rep"] or chair[0]["member"]) if chair else None
        f["ceo_is_member"] = int(any("مدیر عامل" in m["role"] or "مدیرعامل" in m["role"] for m in members))
        if f.get("ceo_name") and f.get("chair_name"): f["ceo_chair_duality"] = int(norm(f["ceo_name"]) == norm(f["chair_name"]))
    f["fx_text_mentions"] = len(re.findall(r"ارز مرجع|ارز نیمایی|ارز ترجیحی|ارز توافقی|نرخ نیما", full))
    f["export_text_mentions"] = len(re.findall(r"صادر", full))
    return f, members

# ------------------------------------------------------------------ TSETMC: بازار
class Tse:
    def __init__(self, min_interval=1.0, log=print):
        self.s = requests.Session(); self.s.headers.update(UA); self.min_interval, self.last, self.log = min_interval, 0.0, log
        self._idx_list = None; self._idx_cache = {}
    def get(self, url):
        dt = time.time() - self.last
        if dt < self.min_interval: time.sleep(self.min_interval - dt)
        self.last = time.time()
        self.err = None
        for i in range(3):
            try:
                r = requests.get(url, headers={**UA, "Connection": "close"}, timeout=(10, 45))
                if r.status_code == 200:
                    try: return r.json()
                    except Exception: self.err = "پاسخ JSON نبود: " + r.text[:80].replace("\n", " "); time.sleep(5 * (i + 1)); continue
                self.err = f"HTTP {r.status_code}"
                if r.status_code in (403, 429, 500, 502, 503, 504): time.sleep(15 * (i + 1)); continue
                return None
            except Exception as ex: self.err = str(ex)[:100]; self.log(f"    … تی‌اس‌ای‌سی پاسخ نداد ({type(ex).__name__})، تلاش {i + 1}/3"); time.sleep(10 * (i + 1))
        return None
    def codal_list(self, ins):
        """فهرست کامل اطلاعیه‌های کدال یک نماد از تی‌اس‌ای‌سی (یک درخواست، بدون کپچا)"""
        j = self.get(f"{TSE}/Codal/GetPreparedDataByInsCode/99999/{ins}")
        return (j or {}).get("preparedData") or []
    def raw(self, url):
        """بایت‌های خام؛ (وضعیت, محتوا, نوع). برای فایل‌های کدال روی تی‌اس‌ای‌سی (بدون کپچا)"""
        dt = time.time() - self.last
        if dt < self.min_interval: time.sleep(self.min_interval - dt)
        self.last = time.time(); st_, data, ct = None, b"", ""
        for i in range(3):
            try:
                r = requests.get(url, headers={**UA, "Connection": "close"}, timeout=(15, 120)); st_, data, ct = r.status_code, r.content, r.headers.get("Content-Type", "")
                if st_ in (429, 502, 503, 504): time.sleep(8 * (i + 1)); continue
                return st_, data, ct
            except Exception as ex: self.err = str(ex)[:100]; time.sleep(8 * (i + 1))
        return st_, data, ct
    def find(self, ticker):
        j = self.get(f"{TSE}/Instrument/GetInstrumentSearch/{requests.utils.quote(ticker)}")
        items = (j or {}).get("instrumentSearch") or []
        t = norm(ticker)
        for it in items:
            if norm(it.get("lVal18AFC", "")) == t: return it
        return items[0] if items else None
    def info(self, ins): return ((self.get(f"{TSE}/Instrument/GetInstrumentInfo/{ins}") or {}).get("instrumentInfo")) or {}
    def daily(self, ins): return (self.get(f"{TSE}/ClosingPrice/GetClosingPriceDailyList/{ins}/0") or {}).get("closingPriceDaily") or []
    def client_type(self, ins): return (self.get(f"{TSE}/ClientType/GetClientTypeHistory/{ins}/0") or {}).get("clientType") or []
    def share_change(self, ins): return (self.get(f"{TSE}/Instrument/GetInstrumentShareChange/{ins}") or {}).get("instrumentShareChange") or []
    def identity(self, ins): return (self.get(f"{TSE}/Instrument/GetInstrumentIdentity/{ins}") or {}).get("instrumentIdentity") or {}
    def holders(self, ins): return (self.get(f"{TSE}/Shareholder/GetInstrumentShareHolderLast/{ins}") or {}).get("shareHolder") or []
    def index_list(self):
        if self._idx_list is None: self._idx_list = (self.get(f"{TSE}/Index/GetIndexB1LastAll/All/1") or {}).get("indexB1") or []
        return self._idx_list
    def index_hist(self, code):
        if code not in self._idx_cache:
            rows = (self.get(f"{TSE}/Index/GetIndexB2History/{code}") or {}).get("indexB2") or []
            s = pd.Series({int(r["dEven"]): float(r["xNivInuClMresIbs"]) for r in rows if r.get("xNivInuClMresIbs") is not None}).sort_index()
            self._idx_cache[code] = s
        return self._idx_cache[code]
    def industry_code(self, sector_code):
        c = norm(sector_code).strip().zfill(2)
        for it in self.index_list():
            if norm(it.get("lVal30", "")).startswith(c + "-"): return it.get("insCode"), it.get("lVal30")
        return None, None

TEDPIX = "32097828799138957"

def _to_dt(d): d = int(d); return pd.Timestamp(year=d // 10000, month=d // 100 % 100, day=d % 100)

def _weekly(series_by_date):
    s = series_by_date.copy(); s.index = pd.to_datetime(s.index.map(lambda d: _to_dt(d)))
    return s

def _ols(y, X):
    X1 = np.column_stack([np.ones(len(y)), X]); b, *_ = np.linalg.lstsq(X1, y, rcond=None); e = y - X1 @ b
    r2 = 1 - (e @ e) / max(((y - y.mean()) @ (y - y.mean())), 1e-12); return b, e, r2

def market_vars(daily, w_start, w_end, mkt_idx, ind_idx, shares=None):
    """متغیرهای بازار برای پنجره [w_start, w_end] (عدد میلادی yyyymmdd)"""
    if not daily: return {}
    df = pd.DataFrame(daily); df = df[(df["dEven"] >= w_start) & (df["dEven"] <= w_end)].sort_values("dEven")
    df = df[df["zTotTran"] > 0] if "zTotTran" in df else df
    out = {}
    if len(df) < 10: return {"mk_trade_days": int(len(df))}
    r = (df["pClosing"] / df["priceYesterday"].where(df["priceYesterday"] > 0) - 1).replace([np.inf, -np.inf], np.nan)
    out.update(mk_trade_days=int(len(df)), mk_price_close=float(df["pClosing"].iloc[-1]), mk_price_high=float(df["priceMax"].max()), mk_price_low=float(df["priceMin"][df["priceMin"] > 0].min()),
               mk_vol_sum=float(df["qTotTran5J"].sum()), mk_vol_avg=float(df["qTotTran5J"].mean()), mk_val_sum=float(df["qTotCap"].sum()), mk_trades_n=float(df["zTotTran"].sum()),
               mk_zero_ret_share=float((r.fillna(0) == 0).mean()), mk_volat_daily=float(r.std()), mk_volat_ann=float(r.std() * math.sqrt(len(df))))
    amihud = (r.abs() / (df["qTotCap"].where(df["qTotCap"] > 0) / 1e6)).replace([np.inf, -np.inf], np.nan); out["mk_amihud"] = float(amihud.mean())
    if shares: out["mk_turnover"] = float(df["qTotTran5J"].sum() / shares)
    # بازده ماهانه شمسی
    jm = df["dEven"].map(lambda d: g2j(d // 10000, d // 100 % 100, d % 100)[:2]); rr = (1 + r.fillna(0)).groupby(jm.values).prod() - 1
    out["mk_ret_m_mean"] = float(rr.mean()); out["mk_ret_m_sd"] = float(rr.std()); out["mk_months"] = int(len(rr))
    # هفتگی: همزمانی و چولگی منفی
    try:
        d = df.set_index(df["dEven"].map(_to_dt)); rw = (1 + r.set_axis(d.index).fillna(0)).resample("W").prod() - 1
        def widx(s):
            s = s[(s.index >= w_start) & (s.index <= w_end)] if len(s) else s
            return _weekly(s)
        mk = widx(mkt_idx).resample("W").last().pct_change() if mkt_idx is not None and len(mkt_idx) else None
        ind = widx(ind_idx).resample("W").last().pct_change() if ind_idx is not None and len(ind_idx) else None
        if mk is not None:
            D = pd.concat([rw.rename("r"), mk.rename("m")] + ([ind.rename("i")] if ind is not None else []), axis=1, sort=False).dropna()
            if len(D) >= 30:
                _, e1, r2a = _ols(D["r"].values, D[["m"] + (["i"] if "i" in D else [])].values)
                out["mk_r2"] = float(r2a); out["mk_synch"] = float(math.log(max(r2a, 1e-6) / max(1 - r2a, 1e-6)))
                m = D["m"].values; n = len(D)
                if n >= 40:  # مدل بازار گسترش‌یافته با پیش‌رو/پس‌رو (چن-هونگ-استین)
                    Y = D["r"].values[2:-2]; X = np.column_stack([m[0:-4], m[1:-3], m[2:-2], m[3:-1], m[4:]])
                    _, e, _ = _ols(Y, X); W = np.log(1 + np.clip(e, -0.99, None)); k = len(W)
                    out["mk_ncskew"] = float(-(k * (k - 1) ** 1.5 * (W ** 3).sum()) / ((k - 1) * (k - 2) * ((W ** 2).sum()) ** 1.5))
                    up, dn = W[W > W.mean()], W[W <= W.mean()]
                    if len(up) > 2 and len(dn) > 2: out["mk_duvol"] = float(math.log(((len(up) - 1) * ((dn - W.mean()) ** 2).sum()) / ((len(dn) - 1) * ((up - W.mean()) ** 2).sum())))
                    out["mk_crash"] = int((W < W.mean() - 3.09 * W.std()).any()); out["mk_jump"] = int((W > W.mean() + 3.09 * W.std()).any())
                out["mk_beta"] = float(np.polyfit(D["m"].values, D["r"].values, 1)[0])
    except Exception as e: out["mk_err"] = str(e)[:60]
    return out

# ------------------------------------------------------------------ خوانایی و متن (اختیاری)
def readability(text):
    t = norm(text); words = re.findall(r"[؀-ۿA-Za-z0-9]+", t)
    if len(words) < 50: return {}
    sents = [s for s in re.split(r"[.؟!؛\n]+", t) if len(s.split()) >= 3]; ns = max(len(sents), 1); nw = len(words)
    chars = sum(len(w) for w in words); longw = sum(len(w) > 6 for w in words)
    asl, awl = nw / ns, chars / nw
    return {"rd_words": nw, "rd_sentences": ns, "rd_asl": asl, "rd_awl": awl, "rd_longw": longw / nw, "rd_lix": asl + 100 * longw / nw,
            "rd_ari": 4.71 * awl + 0.5 * asl - 21.43, "rd_cli": 0.0588 * (100 * chars / nw) - 0.296 * (100 * ns / nw) - 15.8,
            "rd_ttr": len(set(words[:10000])) / min(nw, 10000)}


# ------------------------------------------------------------------ اسناد کدال: گزارش حسابرس، گزارش هیئت‌مدیره، کنترل داخلی (متن در حافظه، ذخیره نمی‌شود)
def pdf_text(data, max_pages=150):
    try: from pypdf import PdfReader
    except Exception: return None
    try:
        rd = PdfReader(io.BytesIO(data)); return norm("\n".join((p.extract_text() or "") for p in rd.pages[:max_pages]))
    except Exception: return None

def _text_of(data):
    if NO_EXTRACT: return "", "downloaded"
    if data[:4] == b"%PDF":
        t = pdf_text(data); return (t, "pdf_ok") if t and len(t) > 200 else (t, "pdf_بدون_متن")
    t = norm(re.sub(r"<[^>]+>", " ", data.decode("utf-8", "replace")))
    return (t, "html_ok") if len(t) > 200 else (t, "html_کوتاه")

def doc_text(codal, u, base=None):
    """متن یک سند؛ اگر base داده شود فایل خام روی دیسک ذخیره/از دیسک خوانده می‌شود (base بدون پسوند). (متن, وضعیت)"""
    if base:
        for ext in (".pdf", ".html"):
            if os.path.exists(base + ext) and os.path.getsize(base + ext) > 0: return _text_of(open(base + ext, "rb").read())
    if codal is None: return None, "فایل_موجود_نیست"
    if not u: return None, "بدون_آدرس"
    u = str(u); cands = [u] if u.startswith("http") else [CODAL + "/" + u.lstrip("/")] + ([CODAL + "/Reports/" + u.lstrip("/")] if "Reports" not in u else [])
    for c in cands:
        r = codal.get(c)
        if r is None or r.status_code != 200: continue
        data = r.content
        if len(data) < 5000: raise Blocked("سند خالی/مشکوک (%d بایت) — کدال PDF خالی داد؛ احتمالاً محدودیت." % len(data))
        if base:
            os.makedirs(os.path.dirname(base), exist_ok=True); open(base + (".pdf" if data[:4] == b"%PDF" else ".html"), "wb").write(data)
        return _text_of(data)
    return None, "دریافت_نشد"

def file_base(args, st, fy, kind, no):
    if getattr(args, "no_save", False): return None
    d = os.path.join(args.files_dir, "%s_%s" % (st["firm_id"], re.sub(r'[\\/:*?"<>|]', "_", st["symbol"])), str(fy))
    return os.path.join(d, "%s_%s" % (kind, no))


def letter_serial(x):
    for key in ("url", "pdf"):
        m = re.search(r"(?:LetterSerial|hs)=([^&]+)", str(x.get(key) or ""))
        if m: return m.group(1)
    return None

def attachment_texts(codal, x, base_dir, prefix):
    """پیوست‌های یک نامه (صفحهٔ Attachment.aspx): فایل‌ها را ذخیره و متنشان را برمی‌گرداند. صفحهٔ پیوست هم برای اشکال‌یابی ذخیره می‌شود."""
    ls = letter_serial(x)
    if not ls: return "", "بدون_شناسه_پیوست", []
    page_path = os.path.join(base_dir, prefix + "_attachment_page.html") if base_dir else None; texts, files = [], []
    if page_path and os.path.exists(page_path): html = open(page_path, "rb").read().decode("utf-8", "replace")
    else:
        if codal is None: return "", "فایل_موجود_نیست", []
        r = codal.get(CODAL + "/Reports/Attachment.aspx?LetterSerial=" + ls)
        if r is None or r.status_code != 200: return "", "دریافت_نشد", []
        html = r.text
        if page_path: os.makedirs(base_dir, exist_ok=True); open(page_path, "wb").write(html.encode("utf-8"))
    links = []
    for m in re.finditer(r"""(?:href|src|data-url|data-href)\s*=\s*["']([^"']+)["']""", html):
        u = m.group(1).replace("&amp;", "&")
        if re.search(r"DownloadFile|\.pdf|\.xls|\.doc|\.zip|\.rar|GetFile|Attachment/Get|Download", u, re.I) and "Attachment.aspx?LetterSerial" not in u and u not in links: links.append(u)
    for k, u in enumerate(links[:8]):
        stem = os.path.join(base_dir, "%s_att%d" % (prefix, k + 1)) if base_dir else None; t, stt = doc_text(codal, u if u.startswith("http") else (u if u.startswith("/") else "/" + u), stem)
        files.append((u, stt))
        if t: texts.append(t)
    if NO_EXTRACT and any(stt in ("downloaded",) for _, stt in files): return "", "downloaded", files
    return "\n".join(texts), ("پیوست_ok" if texts else ("پیوست_بدون_لینک" if not links else "پیوست_بدون_متن")), files

def _cnt(pat, t): return len(re.findall(pat, t))

def audit_features(t):
    """گزارش حسابرس مستقل: نوع اظهارنظر، بندهای تأکیدی، تداوم فعالیت، حسابرس، عدم رعایت مقررات"""
    f = {"audit_text_len": len(t)}
    disc, adv = bool(re.search(r"عدم اظهار ?نظر|اظهار ?نظر نمی ?کنیم|اظهار ?نظر نمی ?نماییم", t)), bool(re.search(r"اظهار ?نظر مردود|نظر مردود|مردود", t))
    qual = bool(re.search(r"اظهار ?نظر مشروط|نظر مشروط|به استثنای|به استثناء|به جز آثار|به غیر از آثار", t))
    f["audit_opinion"] = 3 if disc else 2 if adv else 1 if qual else (0 if re.search(r"مطلوب|مقبول|به نحو مطلوب", t) else None)
    f["audit_qualified"] = int(qual and not disc and not adv) if f["audit_opinion"] is not None else None
    f["audit_disclaimer"] = int(disc) if f["audit_opinion"] is not None else None; f["audit_adverse"] = int(adv and not disc) if f["audit_opinion"] is not None else None
    f["audit_emphasis"] = int(bool(re.search(r"تاکید بر مطلب خاص|تأکید بر مطلب خاص|تاکید بر مطلب|تأکید بر مطلب", t)))
    f["audit_emphasis_n"] = _cnt(r"تاکید بر|تأکید بر", t)
    f["audit_going_concern"] = int(bool(re.search(r"ابهام (با اهمیت|بااهمیت)? ?(در خصوص|درخصوص|نسبت به)? ?تداوم فعالیت|تداوم فعالیت.{0,60}ابهام", t)))
    f["audit_other_resp"] = int("سایر مسئولیت" in t)
    f["audit_noncompl_n"] = _cnt(r"عدم رعایت|رعایت نشده|رعایت نگردیده|رعایت نشدن|مغایرت با", t)
    f["audit_icfr_weak"] = int(bool(re.search(r"ضعف.{0,40}کنترل|کنترل.{0,60}ضعف|نقاط ضعف", t)))
    f["audit_bourse_rules"] = int("سازمان بورس" in t and bool(re.search(r"دستورالعمل|مقررات", t)))
    f["audit_aml"] = int(bool(re.search(r"مبارزه با پولشویی|پول ?شویی", t)))
    f["audit_art141"] = int(bool(re.search(r"ماده ?141|ماده ۱۴۱", t)))
    m = re.search(r"((?:موسسه|مؤسسه) حسابرسی\s+[^\n.،:;()\d]{2,45}?)(?=\s+(?:شماره|ثبت|حسابداران|حسابرس|مستقل|و بازرس|\d|$)|[\n.،:;(])", t)
    f["audit_firm"] = m.group(1).strip() if m else None
    f["audit_org"] = int("سازمان حسابرسی" in t)
    return f

KW = {
    "env": r"محیط زیست|آلودگی|پسماند|بازیافت|گازهای گلخانه|انرژی پاک|انرژی تجدید|بهینه ?سازی مصرف انرژی|پساب|تصفیه",
    "soc": r"مسئولیت اجتماعی|مسوولیت اجتماعی|ایمنی|بهداشت|آموزش کارکنان|خیریه|اشتغال|رفاه کارکنان|حوادث ناشی از کار",
    "gov": r"حاکمیت شرکتی|کمیته حسابرسی|شفافیت|ذی ?نفعان|مدیریت ریسک|کنترل داخلی|حسابرسی داخلی|منشور",
    "inn": r"نوآوری|دانش ?بنیان|تحقیق و توسعه|هوش مصنوعی|دیجیتال|فناوری اطلاعات|فناوری نوین|اتوماسیون",
    "risk": r"ریسک|عدم اطمینان|عدم قطعیت|تحریم|نوسان نرخ ارز|تورم",
    "opt": r"بهبود|افزایش فروش|رشد|موفق|توسعه|بهینه",
    "pes": r"کاهش فروش|زیان|توقف|کمبود|مشکلات|تعلیق|افت",
    "fx": r"ارز|نرخ ارز|صادرات|ارز نیمایی|ارز مرجع",
}
def text_features(t, prefix):
    nw = max(len(re.findall(r"[؀-ۿA-Za-z0-9]+", t)), 1); f = {prefix + "_len": nw}
    for k, pat in KW.items(): n = _cnt(pat, t); f[f"{prefix}_{k}_n"] = n; f[f"{prefix}_{k}_per1k"] = 1000.0 * n / nw
    f[prefix + "_tone"] = (f[prefix + "_opt_n"] - f[prefix + "_pes_n"]) / max(f[prefix + "_opt_n"] + f[prefix + "_pes_n"], 1)
    f.update({prefix + "_" + k: v for k, v in readability(t).items()})
    return f

def ic_features(t):
    return {"ic_text_len": len(t), "ic_weak_n": _cnt(r"ضعف|نواقص|نقطه ضعف|کاستی", t), "ic_effective": int(bool(re.search(r"اثربخش|کارآمد", t)) and not re.search(r"اثربخش نبوده|اثربخش نیست|فاقد اثربخشی|ناکارآمد", t)),
            "ic_ineffective": int(bool(re.search(r"اثربخش نبوده|اثربخش نیست|فاقد اثربخشی|ناکارآمد", t)))}


NOTE_KW = {
    "rp": r"اشخاص وابسته|معاملات با اشخاص وابسته|طرف های وابسته|طرف‌های وابسته",
    "cont": r"بدهی های احتمالی|بدهی‌های احتمالی|تعهدات سرمایه ای|تعهدات سرمایه‌ای|دارایی های احتمالی",
    "subseq": r"رویدادهای بعد از تاریخ|رویدادهای پس از تاریخ|رویدادهای بعد از دوره",
    "gc": r"تداوم فعالیت",
    "loan": r"تسهیلات مالی|تسهیلات دریافتی|وام|اوراق مرابحه|اوراق صکوک|اسناد پرداختنی",
    "collat": r"وثیقه|رهن|ضمانت|تضمین|سفته|بازداشت",
    "covenant": r"تعهدات مالی|شرایط قرارداد|محدودیت|الزامات قراردادی|نسبت بدهی|نسبت جاری|نسبت پوشش",
    "default": r"معوق|سررسید گذشته|جرایم تاخیر|جریمه تأخیر|عدم ایفا|نکول|بازپرداخت نشده",
    "restr": r"تجدید ساختار|تمدید|بازتعیین|بازپرداخت مجدد|زمانبندی مجدد",
    "legal": r"دعاوی حقوقی|دعوی|پرونده قضایی|حکم دادگاه|مالیات تشخیصی|اختلاف مالیاتی",
    "tax": r"مالیات|رسیدگی مالیاتی|برگ تشخیص|قطعی",
    "fx": r"ارز|دلار|یورو|درهم|نرخ تسعیر|سامانه نیما|نیمایی",
    "estimate": r"برآورد|قضاوت|ذخیره کاهش ارزش|کاهش ارزش",
    "restate": r"تعدیل سنواتی|اصلاح اشتباه|تغییر در رویه حسابداری|تجدید ارائه",
}
def notes_features(t):
    nw = max(len(re.findall(r"[؀-ۿA-Za-z0-9]+", t)), 1); f = {"nt_len": nw}
    for k, pat in NOTE_KW.items(): n = _cnt(pat, t); f["nt_%s_n" % k] = n; f["nt_%s_per1k" % k] = 1000.0 * n / nw
    f["nt_restated"] = int(f["nt_restate_n"] > 0 and bool(re.search(r"تعدیل سنواتی|تجدید ارائه", t)))
    return f

def split_fs_pdf(t):
    """بخش گزارش حسابرس (قبل از صورت‌ها) و یادداشت‌های توضیحی (بعد از صورت‌ها)"""
    m = re.search(r"صورت سود و زیان|صورت وضعیت مالی|ترازنامه", t[800:]) if t else None
    if not m: return (t or "")[:15000], ""
    i = 800 + m.start(); j = t.find("یادداشت", i + 2000)
    return t[:i], (t[j:] if j > 0 else t[i:])

def fs_candidates(letters):
    """صورت‌های مالی سالانهٔ خود شرکت (نه زیرمجموعه‌ها) به تفکیک سال مالی: [(p, x)]، حسابرسی‌شده‌ها جلوتر"""
    out = collections.defaultdict(list)
    for x in letters:
        if lcode(x["code"]) != "ن-10": continue
        p = parse_title(x["title"])
        other = bool(p["other_company"]) and x.get("other_co", True)   # پرانتز «(شرکت ...)» در عنوان و نام ناشر متفاوت از نام اصلی
        if p["annual"] and p["fiscal_year"] and not other: out[p["fiscal_year"]].append((p, x))
    for fy in out:   # جدیدترین اول، سپس: حسابرسی‌شده، دارای پیوست/اکسل، غیرتلفیقی، بدون اصلاحیه
        out[fy].sort(key=lambda px: norm(px[1]["pub"] or ""), reverse=True)
        out[fy].sort(key=lambda px: (-px[0]["audited"], -int(bool(px[1].get("n_att", 1) or px[1].get("pdf"))), px[0]["consolidated"], px[0]["amendment"]))
    return out

def letter_fy(x, fye_md):
    """سال مالی نامه: اول از تاریخ پایان دورهٔ داخل عنوان؛ وگرنه سال انتشار منهای ۱ (گزارش‌های سالانه پس از پایان سال منتشر می‌شوند)"""
    p = parse_title(x["title"])
    if p["fiscal_year"]: return p["fiscal_year"]
    y = fiscal_year_of(x["pub"], fye_md); return y - 1 if y else None

def fye_of(letters):
    mds = collections.Counter()
    for x in letters:
        p = parse_title(x["title"])
        if p["annual"] and p["audited"] and p["fye"]: mds[tuple(int(v) for v in p["fye"].split("/")[1:])] += 1
    return mds.most_common(1)[0][0] if mds else (12, 29)

def unwrap_payload(data):
    """اگر پاسخ JSON با فایل base64 بود، بایت‌های فایل را درمی‌آورد"""
    import base64
    if data[:1] not in (b"{", b"["): return data, None
    try: j = json.loads(data.decode("utf-8", "replace"))
    except Exception: return data, None
    best = []
    def walk(o):
        if isinstance(o, dict): [walk(v) for v in o.values()]
        elif isinstance(o, list): [walk(v) for v in o]
        elif isinstance(o, str) and len(o) > 500: best.append(o)
    walk(j)
    for sv in sorted(best, key=len, reverse=True):
        try:
            b = base64.b64decode(sv + "=" * (-len(sv) % 4), validate=False)
            if b[:4] == b"%PDF" or b[:2] in (b"PK", b"\xd0\xcf"): return b, None
        except Exception: pass
    return data, "json_ناشناخته"

def _ext(data, ct=""):
    if data[:4] == b"%PDF": return ".pdf"
    if data[:2] == b"PK": return ".zip"
    if data[:2] == b"\xd0\xcf": return ".xls"
    if data[:1] in (b"<",) or "html" in ct: return ".html"
    if data[:1] in (b"{", b"["): return ".json"
    return ".bin"

def tse_letter_files(tse, no, base_dir, prefix, max_rows=6, include_notice=False, extract=True):
    """PDF اطلاعیه و پیوست‌های یک نامه از cdn.tsetmc.com (بر اساس TracingNo). متن PDFها را برمی‌گرداند. (متن, وضعیت, فایل‌ها)"""
    texts, files = [], []
    def put(name, data, ct):
        if base_dir:
            os.makedirs(base_dir, exist_ok=True); open(os.path.join(base_dir, name), "wb").write(data)
    def locate(name_stem):
        """فایل را در پوشهٔ همین سال یا (برای فایل‌های جابه‌جاشده) در پوشهٔ سال‌های دیگر همین شرکت پیدا و به پوشهٔ درست منتقل می‌کند"""
        if not base_dir: return None
        dirs = [base_dir] + ([os.path.join(os.path.dirname(base_dir), d) for d in os.listdir(os.path.dirname(base_dir)) if os.path.join(os.path.dirname(base_dir), d) != base_dir] if os.path.isdir(os.path.dirname(base_dir)) else [])
        for d_ in dirs:
            if not os.path.isdir(d_): continue
            for f in os.listdir(d_):
                if f.startswith(name_stem) and os.path.getsize(os.path.join(d_, f)) > 0:
                    if d_ != base_dir:
                        import shutil; os.makedirs(base_dir, exist_ok=True); shutil.move(os.path.join(d_, f), os.path.join(base_dir, f))
                    return os.path.join(base_dir, f)
        return None
    def cached(name_stem):
        p_ = locate(name_stem + ".")
        return open(p_, "rb").read() if p_ else None
    man_path = os.path.join(base_dir, prefix + "_manifest.json") if base_dir else None
    done = bool(base_dir and locate(prefix + "_manifest.json"))
    jobs = ([("notice", f"{TSE}/Codal/GetContentFileByTracingNo/{no}/1")] if include_notice else []) + [("att%d" % r, f"{TSE}/Codal/GetAttachmentContentFileByTracingNoAndRowOrder/{no}/{r}") for r in range(1, max_rows + 1)]
    for tag, url in jobs:
        stem = prefix + "_" + tag; data = cached(stem)
        if data is None:
            if done or tse is None: continue
            st_, data, ct = tse.raw(url)
            if st_ != 200 or len(data) < 200:
                if tag != "notice": break          # ردیف پیوست بعدی وجود ندارد
                continue
            data, note = unwrap_payload(data); put(stem + _ext(data, ct), data, ct)
        files.append((tag, len(data), _ext(data)))
        if not extract: continue
        if data[:4] == b"%PDF" and len(data) > 5000: t = pdf_text(data); t and texts.append(t)
        elif data[:1] == b"<" and len(data) > 3000: texts.append(norm(re.sub(r"<[^>]+>", " ", data.decode("utf-8", "replace"))))
    if tse is not None and not done and man_path:
        os.makedirs(base_dir, exist_ok=True); json.dump({"files": files}, open(man_path, "w", encoding="utf-8"))
    txt = "\n".join(t for t in texts if t)
    if not extract: return "", ("tse_downloaded" if files else "tse_بدون_فایل"), files
    return txt, ("tse_ok" if len(txt) > 200 else ("tse_بدون_متن" if files else "tse_بدون_فایل")), files

def title_code(title):
    """کد نوع نامه از روی عنوان (پاسخ تی‌اس‌ای‌سی کد ندارد)"""
    t = norm(title)
    for pat, c in ((r"گزارش کنترل|کنترل ?های داخلی", "ن-12"), (r"گزارش فعالیت ماهانه", "ن-30"), (r"گزارش فعالیت هیئت", "ن-11"), (r"توضیحات در خصوص اطلاعات", "ن-26"),
                   (r"صورت ?های مالی", "ن-10"), (r"کمیته حسابرسی", "ن-41"), (r"تغییر در ترکیب اعضای", "ن-45"), (r"کمیته انتصابات", "ن-86"),
                   (r"آگهی ثبت تصمیمات مجمع", "ن-42"), (r"تصمیمات مجمع", "ن-52"), (r"دعوت به مجمع عمومی فوق", "ن-56"), (r"دعوت به مجمع", "ن-50"),
                   (r"افزایش سرمایه", "ن-60"), (r"اظهارنظر حسابرس", "ن-61")):
        if re.search(pat, t): return c
    return None

def letters_from_tse(rows):
    """ردیف‌های GetPreparedDataByInsCode (هر ردیف = یک پیوست) → فهرست نامه‌ها با ساختار سازگار با کدال"""
    by = collections.OrderedDict()
    for r_ in rows:
        no = str(r_.get("tracingNo")); e = by.setdefault(no, {"co_name": r_.get("name"), "no": int(no) if no.isdigit() else no, "code": title_code(r_.get("title") or ""), "title": r_.get("title"),
              "pub": None, "excel": None, "has_excel": int(r_.get("hasExcelReport") or 0) == 1, "url": "", "pdf": "", "att": "", "atts": []})
        pg = r_.get("publishDateTime_Gregorian")
        if pg and not e["pub"]:
            m = re.match(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}:\d{2}:\d{2})", pg)
            if m: jy, jm, jd = g2j(int(m.group(1)), int(m.group(2)), int(m.group(3))); e["pub"] = "%04d/%02d/%02d %s" % (jy, jm, jd, m.group(4))
        if r_.get("attachmentID"): e["atts"].append({"id": r_.get("attachmentID"), "name": r_.get("fileName"), "ext": r_.get("fileExtension"), "ctype": r_.get("contentType")})
    main = collections.Counter(e["co_name"] for e in by.values() if e["co_name"]).most_common(1)
    main = main[0][0] if main else None
    for e in by.values():
        e["atts"].sort(key=lambda a: a["id"]); e["n_att"] = len(e["atts"]); e["other_co"] = bool(main and e["co_name"] and e["co_name"] != main)
    return list(by.values())

def tse_excel(tse, no, types=(2, 3, 4, 0, 5, 6)):
    """تلاش برای گرفتن اکسل نامه از تی‌اس‌ای‌سی بر اساس TracingNo (نوع فایل را حدس می‌زند). متن HTML-xls یا None"""
    for t in types:
        st_, data, ct = tse.raw(f"{TSE}/Codal/GetContentFileByTracingNo/{no}/{t}")
        if st_ == 200 and len(data) > 20000:
            data, _ = unwrap_payload(data)
            txt = data.decode("utf-8", "replace")
            if "<table" in txt[:20000].lower() and "<h3" in txt.lower(): return txt
    return None

OKSTAT = {"tse_ok", "tse_downloaded", "pdf_ok", "html_ok", "پیوست_ok", "downloaded"}
def doc_gaps(st, args):
    gaps = []
    for fy in range(max(args.fy_from, args.docs_from), args.fy_to + 1):
        d = st.get("docs", {}).get(str(fy), {})
        for k, key in (("audit", "audit_status"), ("board", "br_status"), ("ic", "ic_status")):
            if (d.get(k) or {}).get(key) not in OKSTAT: gaps.append((fy, k))
    return gaps

def merge_codal_letters(st, L):
    idx = {str(x["no"]): x for x in st["letters"]}; added = 0
    for x in L:
        k = str(x.get("TracingNo")); new = {"no": x.get("TracingNo"), "code": x.get("LetterCode"), "title": x.get("Title"), "pub": x.get("PublishDateTime"), "excel": x.get("ExcelUrl"),
                                           "url": x.get("Url"), "pdf": x.get("PdfUrl"), "att": x.get("AttachmentUrl"), "src": "codal"}
        if k in idx:
            e = idx[k]
            for f in ("excel", "url", "pdf", "att"):
                if not e.get(f) and new.get(f): e[f] = new[f]
            if not e.get("code") and new["code"]: e["code"] = new["code"]
        else: st["letters"].append(new); added += 1
    return added

RETRY = {"فایل_موجود_نیست", "دریافت_نشد", "پیوست_بدون_لینک", "پیوست_بدون_متن", "pdf_بدون_متن", "بدون_pdf", "tse_بدون_فایل", "tse_بدون_متن"}
def collect_docs(st, cand, args, codal, log, save, tse=None, retry=False, source=None):
    docs = st.setdefault("docs", {}); letters = st["letters"]; fye_md = fye_of(letters); fs_all = fs_candidates(letters)
    by = {"board": collections.defaultdict(list), "ic": collections.defaultdict(list)}
    for x in letters:
        cat = classify(x["code"], x["title"]); fy = letter_fy(x, fye_md)
        if fy and cat == "board_report": by["board"][fy].append(x)
        elif fy and cat == "internal_control": by["ic"][fy].append(x)
    EXTRACT = bool(args.reparse or args.extract or (args.stage != "docs-tse" and not args.download_only))
    def need(entry, key):
        if not entry: return True
        return (args.retry_failed or retry) and entry.get(key) in RETRY
    def letter_text(x, kind, fy):
        """متن‌های یک نامه: ابتدا تی‌اس‌ای‌سی (بدون کپچا)، سپس در صورت --docs-source both از کدال"""
        fb = file_base(args, st, fy, kind, x["no"]); d_ = os.path.dirname(fb) if fb else None
        src_ = source or args.docs_source
        if src_ in ("tse", "both") and (tse is not None or fb):
            t, stt, _ = tse_letter_files(tse, x["no"], d_, os.path.basename(fb) if fb else kind + "_" + str(x["no"]), max_rows=min(max(x.get("n_att", 6), 1), 8), include_notice=(x.get("n_att") == 0), extract=EXTRACT)
            if t or src_ == "tse": return t, stt
        t, stt = doc_text(codal, x.get("pdf"), fb) if x.get("pdf") else (None, "بدون_pdf")
        if stt == "downloaded": return t, stt
        if not t: t, stt, _ = attachment_texts(codal, x, d_, "%s_%s" % (kind, x["no"]))
        return t, stt
    def mark(entry): entry["tries"] = entry.get("tries", 0) + (1 if codal is not None else 0); return entry
    for fy in range(max(args.fy_from, args.docs_from), args.fy_to + 1):
        d = docs.setdefault(str(fy), {})
        # گزارش حسابرس (از PDF صورت مالی حسابرسی‌شدهٔ سالانه)
        if need(d.get("audit"), "audit_status") and fs_all.get(fy):
            for px_ in fs_all[fy][:4]:                      # حسابرسی‌شده‌ها اول؛ اگر فایل نداشت نسخهٔ بعدی
                x = px_[1]; t, stt = letter_text(x, "audit_FS", fy)
                if (t and len(t) > 500) or stt in ("tse_downloaded", "downloaded"): break
            rep, nts = split_fs_pdf(t); d["audit"] = {**(audit_features(rep) if t else {}), **(notes_features(nts) if len(nts) > 500 else {}), "audit_status": stt, "audit_src_no": x["no"], "audit_fs_audited": px_[0]["audited"], "audit_fs_consol": px_[0]["consolidated"]}; save(); log(f"  حسابرس FY{fy}: {stt} | اظهارنظر={d['audit'].get('audit_opinion')} | {d['audit'].get('audit_firm')}")
        if need(d.get("board"), "br_status") and by["board"].get(fy):
            x = sorted(by["board"][fy], key=lambda z: norm(z["pub"]))[-1]; t, stt = letter_text(x, "board_report", fy)
            d["board"] = {**(text_features(t, "br") if t else {}), "br_status": stt, "br_src_no": x["no"]}; save(); log(f"  گزارش هیئت‌مدیره FY{fy}: {stt}")
        if need(d.get("ic"), "ic_status") and by["ic"].get(fy):
            x = sorted(by["ic"][fy], key=lambda z: norm(z["pub"]))[-1]; t, stt = letter_text(x, "internal_control", fy)
            d["ic"] = {**(ic_features(t) if t else {}), "ic_status": stt, "ic_src_no": x["no"]}; save(); log(f"  کنترل داخلی FY{fy}: {stt}")


def wait_enter(timeout_s):
    """منتظر Enter می‌ماند؛ اگر زمان تمام شد False برمی‌گرداند (ویندوز و غیرویندوز)"""
    t0 = time.time()
    try:
        import msvcrt
        buf = ""
        while time.time() - t0 < timeout_s:
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ("\r", "\n"): return buf.strip().lower() or True
                buf += ch
            time.sleep(0.2)
        return False
    except ImportError:
        import select
        r, _, _ = select.select([sys.stdin], [], [], timeout_s)
        return (sys.stdin.readline().strip().lower() or True) if r else False

# ------------------------------------------------------------------ هماهنگ‌کننده
def fiscal_year_of(pub, fye_md):
    j = jdate(pub)
    if not j: return None
    y, m, d = j; fm, fd = fye_md
    return y if (m, d) <= (fm, fd) else y + 1

def load_state(path):
    """خواندن امن فایل وضعیت شرکت؛ اگر خراب بود به .corrupt منتقل می‌شود و None برمی‌گردد"""
    if not os.path.exists(path): return None
    try: return json.load(open(path, encoding="utf-8"))
    except Exception as e:
        try: os.replace(path, path + ".corrupt")
        except Exception: pass
        print(f"  ⚠ فایل وضعیت خراب بود و کنار گذاشته شد: {os.path.basename(path)} ({type(e).__name__})"); return None

def dump_state(path, st):
    """نوشتن اتمیک: اول فایل موقت، بعد جایگزینی؛ تا قطع ناگهانی فایل را خراب نکند"""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(st, f, ensure_ascii=False)
    os.replace(tmp, path)

def repair_firms(out_dir):
    d = os.path.join(out_dir, "firms"); bad = []
    for fn in os.listdir(d):
        if fn.endswith(".json") and load_state(os.path.join(d, fn)) is None and not os.path.exists(os.path.join(d, fn)): bad.append(fn)
        if fn.endswith(".tmp"):
            try: os.remove(os.path.join(d, fn))
            except Exception: pass
    return bad

def process_firm(sym, company, firm_id, args, codal, tse, out_dir, log):
    path = os.path.join(out_dir, "firms", f"{re.sub(r'[^0-9A-Za-z_]', '_', sym) or 'x'}_{firm_id}.json")
    st = load_state(path) or {"symbol": sym, "company": company, "firm_id": int(firm_id)}
    def save(): dump_state(path, st)
    sig = "%s-%s-%d-%s" % (args.fy_from, args.fy_to, int(args.docs), args.docs_from)
    if args.stage not in ("tse", "docs-tse") and not args.reparse and not args.force and st.get("complete_sig") == sig:
        log("  ✓ از قبل کامل است؛ رد شد (بدون درخواست)"); return st
    if args.reparse: st.pop("excel", None); st.pop("docs", None)
    # --- ۱) TSETMC (بدون کپچا) ---
    if tse is not None and not st.get("_daily") and st.get("tse", {}).get("error") != "نماد پیدا نشد":
        st.pop("tse", None)
        it = tse.find(sym)
        if it:
            ins = it["insCode"]; info = tse.info(ins); daily = tse.daily(ins)
            sec = (info.get("sector") or {}).get("cSecVal"); icode, iname = tse.industry_code(sec) if sec else (None, None)
            st["tse"] = {"insCode": ins, "name": it.get("lVal30"), "sector_code": norm(sec or ""), "sector": (info.get("sector") or {}).get("lSecVal"),
                         "market": info.get("flowTitle"), "board": info.get("cgrValCotTitle"), "shares": info.get("zTitad"), "isin": info.get("cIsin"), "industry_index": iname,
                         "holders_snapshot": [{"name": h.get("shareHolderName"), "pct": h.get("perOfShares"), "shares": h.get("numberOfShares"), "date": h.get("dEven")} for h in tse.holders(ins)]}
            st["_daily"] = [[r["dEven"], r.get("pClosing"), r.get("priceYesterday"), r.get("priceMin"), r.get("priceMax"), r.get("zTotTran"), r.get("qTotTran5J"), r.get("qTotCap")] for r in daily]
            st["_ind_code"] = icode
            if not daily or not info:
                log(f"  ⚠ TSETMC پاسخ خالی داد ({tse.err}) — بعداً دوباره تلاش می‌شود"); st.pop("tse", None); st.pop("_daily", None); return st
            st["tse"]["info_raw"] = info                                   # همهٔ فیلدهای اطلاعات نماد
            try: st["tse"]["identity_raw"] = tse.identity(ins)
            except Exception: pass
            try: st["_share_change"] = tse.share_change(ins)               # تاریخچهٔ افزایش سرمایه/تغییر تعداد سهام
            except Exception: st["_share_change"] = []
            try: st["_client"] = [] if args.no_client else [{k: r.get(k) for k in ("recDate", "buy_CountI", "buy_CountN", "buy_I_Volume", "buy_N_Volume", "sell_CountI", "sell_CountN", "sell_I_Volume", "sell_N_Volume")} for r in tse.client_type(ins)]
            except Exception: st["_client"] = []
        else:
            log(f"  ⚠ نماد پیدا نشد ({tse.err})")
            if tse.err: return st
            st["tse"] = {"error": "نماد پیدا نشد"}
        save(); log(f"  TSETMC ✓ {sym} ({st['tse'].get('sector')}), روز معاملاتی: {len(st.get('_daily', []))}")
    if args.stage == "tse": return st
    # --- ۲) کدال: فهرست نامه‌ها ---
    if "letters" not in st:
        lst = st.setdefault("_list", {})
        if lst.get("out"): log(f"  ادامهٔ فهرست‌گیری از صفحهٔ {lst.get('page', 1)} ({len(lst['out'])} نامه تا اینجا)")
        if args.list_source == "tse" and tse is not None and st.get("tse", {}).get("insCode"):
            rows_ = tse.codal_list(st["tse"]["insCode"])
            if rows_:
                st["letters"] = letters_from_tse(rows_); st["letters_src"] = "tse"; st.pop("_list", None); save()
                log(f"  فهرست از تی‌اس‌ای‌سی: {len(st['letters'])} نامه ({len(rows_)} ردیف پیوست)")
        if "letters" not in st:
            if codal is None: return st
            L = codal.list_letters(sym, args.fy_from, args.fy_to, tuple(args.letter_types.split(",")) if args.fast_list else ("-1",), state=lst, save=save)
            st["letters"] = [{"no": x.get("TracingNo"), "code": x.get("LetterCode"), "title": x.get("Title"), "pub": x.get("PublishDateTime"), "excel": x.get("ExcelUrl"), "url": x.get("Url"), "pdf": x.get("PdfUrl"), "att": x.get("AttachmentUrl")} for x in L]
            st.pop("_list", None); save(); log(f"  کدال: {len(L)} نامه")
    if args.docs and st.get("docs_v") != 2: st["docs"] = {}; st["docs_v"] = 2            # تخصیص سال بر اساس عنوان (نسخهٔ ۲)
    merged_now = False
    if args.fill_codal and codal is not None and not st.get("codal_merged") and doc_gaps(st, args):
        lstf = st.setdefault("_listfull", {})
        log(f"  ⟲ تکمیل از کدال: {len(doc_gaps(st, args))} مورد ناقص؛ فهرست کامل کدال گرفته می‌شود")
        Lc = codal.list_letters(sym, args.fy_from, args.fy_to, ("-1",), state=lstf, save=save)
        n_add = merge_codal_letters(st, Lc); st["codal_merged"] = True; st.pop("_listfull", None); save(); merged_now = True
        log(f"  فهرست کدال: {len(Lc)} نامه، {n_add} نامهٔ جدید به فهرست اضافه شد")
    # --- ۳) اکسل صورت مالی سالانه حسابرسی‌شده برای هر سال مالی ---
    cand = collections.defaultdict(list)
    for fy_, lst_ in fs_candidates(st["letters"]).items():
        lst_ = [px for px in lst_ if px[1].get("excel") or px[1].get("has_excel")]
        if lst_: cand[fy_] = lst_
    st.setdefault("excel", {})
    for fy, lst in (sorted(cand.items()) if args.stage != "docs-tse" else []):
        e0 = st["excel"].get(str(fy), {})
        if "f" in e0 or fy < args.fy_from or fy > args.fy_to: continue
        if e0 and not args.retry_failed and e0.get("tries", 1) >= 1 and codal is not None: continue   # قبلاً یک بار امتحان شده
        best = lst[0][1]
        xb0 = file_base(args, st, fy, "FS_excel", best["no"]); xb = (xb0 + ".xls") if xb0 else None; html = None
        if xb and os.path.exists(xb) and os.path.getsize(xb) > 0: html = open(xb, "rb").read().decode("utf-8", "replace")
        else:
            url_ = best.get("excel")
            if not url_ and best.get("has_excel") and codal is not None:
                # فهرست تی‌اس‌ای‌سی آدرس اکسل ندارد: فقط صورت‌های مالی (LetterType=6) را از کدال بگیر و با شمارهٔ پیگیری وصل کن
                if "codal_fs" not in st:
                    L6 = codal.list_letters(sym, args.fy_from, args.fy_to, ("6",), state=st.setdefault("_list6", {}), save=save)
                    st["codal_fs"] = {str(x.get("TracingNo")): x.get("ExcelUrl") for x in L6}; st.pop("_list6", None); save(); log(f"  کدال (فقط صورت مالی): {len(L6)} نامه برای آدرس اکسل")
                url_ = st["codal_fs"].get(str(best["no"]))
            if url_ and codal is not None:
                html = codal.excel(url_)
                if html and xb: os.makedirs(os.path.dirname(xb), exist_ok=True); open(xb, "wb").write(html.encode("utf-8"))
        if html and args.download_only and not args.reparse:
            st["excel"][str(fy)] = {"downloaded": True, "source_no": best["no"]}; log(f"  اکسل FY{fy}: دانلود شد (استخراج بعداً)")
        elif html:
            f, members = parse_excel(html); f.update(source_no=best["no"], source_title=norm(best["title"])[:120]); st["excel"][str(fy)] = {"f": f, "members": members}
            log(f"  اکسل FY{fy}: هیئت {f.get('bd_size')}، کارکنان {f.get('staff_prod')}/{f.get('staff_nonprod')}، تفسیری={f.get('interp_report')}")
        else: st["excel"][str(fy)] = {"error": "اکسل خوانده نشد: " + str(codal.excel_err if codal is not None else "اکسل از تی‌اس‌ای‌سی/دیسک در دسترس نبود"), "source_no": best["no"], "title": norm(best["title"])[:100], "tries": e0.get("tries", 0) + (1 if codal is not None else 0)}; log(f"  ⚠ اکسل FY{fy} خوانده نشد ({codal.excel_err if codal is not None else "اکسل از تی‌اس‌ای‌سی/دیسک در دسترس نبود"})")
        save()
    if args.docs: collect_docs(st, cand, args, codal, log, save, tse)
    if args.docs and merged_now: collect_docs(st, cand, args, codal, log, save, tse, retry=True, source="both")
    if args.stage == "docs-tse": save(); return st
    st["done"] = True; st["complete_sig"] = sig; save(); return st

def build(out_dir, args):
    rows = {}; ev_rows = []; mem_rows = []; hold = []; BT = Tse()
    for fn in sorted(os.listdir(os.path.join(out_dir, "firms"))):
        if not fn.endswith(".json"): continue
        st = load_state(os.path.join(out_dir, "firms", fn))
        if st is None: continue
        sym, fid = st["symbol"], st["firm_id"]
        L = st.get("letters", []); tse = st.get("tse", {})
        # پایان سال مالی شرکت (ماه/روز غالب)
        mds = collections.Counter()
        for x in L:
            p = parse_title(x["title"])
            if p["annual"] and p["audited"] and p["fye"]: mds[tuple(int(v) for v in p["fye"].split("/")[1:])] += 1
        fye_md = mds.most_common(1)[0][0] if mds else (12, 29)
        for fy in range(args.fy_from, args.fy_to + 1): rows.setdefault((fid, fy), {"firm_id": fid, "symbol": sym, "company": st.get("company"), "fiscal_year": fy, "fye_md": "%02d/%02d" % fye_md})
        for k in ("sector", "market", "board", "shares", "industry_index"): 
            for fy in range(args.fy_from, args.fy_to + 1): rows[(fid, fy)]["tse_" + k] = tse.get(k)
        # رویدادها از فهرست نامه‌ها
        cnt = collections.defaultdict(collections.Counter)
        for x in L:
            fy = fiscal_year_of(x["pub"], fye_md); cat = classify(x["code"], x["title"])
            if fy: cnt[fy][cat] += 1
            ev_rows.append({"firm_id": fid, "symbol": sym, "no": x["no"], "code": lcode(x["code"]), "cat": cat, "pub": norm(x["pub"]), "fiscal_year": fy, "title": norm(x["title"])[:140]})
        for fy, c in cnt.items():
            if (fid, fy) in rows:
                for cat, n in c.items(): rows[(fid, fy)]["ev_n_" + cat] = n
                rows[(fid, fy)]["ev_n_letters"] = sum(c.values())
        # تأخیر انتشار و تجدید ارائه (از فهرست نامه‌ها)
        lag = collections.defaultdict(dict)
        for x in L:
            p = parse_title(x["title"]); jd = jdate(x["pub"])
            if lcode(x["code"]) != "ن-10" or not (p["annual"] and p["fiscal_year"] and p["fye"] and jd) or p["other_company"]: continue
            fy_ = p["fiscal_year"]; fy_t = tuple(int(v) for v in p["fye"].split("/")); gp, ge = j2g(*jd), j2g(*fy_t)
            days = (pd.Timestamp(*gp) - pd.Timestamp(*ge)).days; d_ = lag[fy_]
            if p["amendment"]: d_["amend_n"] = d_.get("amend_n", 0) + 1
            else:
                k = "lag_audited" if p["audited"] else "lag_unaudited"
                if k not in d_ or days < d_[k]: d_[k] = days
        for fy_, d_ in lag.items():
            if (fid, fy_) in rows:
                rows[(fid, fy_)].update(fs_report_lag_audited=d_.get("lag_audited"), fs_report_lag_unaudited=d_.get("lag_unaudited"), fs_amend_n=d_.get("amend_n", 0), fs_amend_any=int(d_.get("amend_n", 0) > 0))
        # اکسل
        for fy, e in st.get("excel", {}).items():
            if (fid, int(fy)) in rows and ("f" in e or e.get("downloaded")): rows[(fid, int(fy))]["cov_excel"] = 1
            if (fid, int(fy)) in rows and "f" in e: rows[(fid, int(fy))].update(e["f"])
            for m in e.get("members", []): mem_rows.append({"firm_id": fid, "symbol": sym, "fiscal_year": int(fy), **m})
        for fy, dd_ in st.get("docs", {}).items():
            if (fid, int(fy)) in rows:
                for part in dd_.values(): rows[(fid, int(fy))].update(part)
        # بازار
        daily = st.get("_daily")
        if daily:
            dd = [dict(zip(["dEven", "pClosing", "priceYesterday", "priceMin", "priceMax", "zTotTran", "qTotTran5J", "qTotCap"], r)) for r in daily]
            mk = pd.Series(dtype=float)
            try:
                mkt_idx = BT.index_hist(TEDPIX); ind_idx = BT.index_hist(st["_ind_code"]) if st.get("_ind_code") else None
            except Exception: mkt_idx = ind_idx = None
            for fy in range(args.fy_from, args.fy_to + 1):
                ps = j2g(fy - 1, fye_md[0], fye_md[1]) if True else None
                s0 = ps[0] * 10000 + ps[1] * 100 + ps[2] + 1; e = j2g(fy, fye_md[0], min(fye_md[1], 30)); e0 = e[0] * 10000 + e[1] * 100 + e[2]
                rows[(fid, fy)].update(market_vars(dd, s0, e0, mkt_idx, ind_idx, tse.get("shares")))
        cl = pd.DataFrame(st.get("_client") or [])
        if len(cl) and "recDate" in cl:
            cl = cl.apply(pd.to_numeric, errors="coerce")
            for fy in range(args.fy_from, args.fy_to + 1):
                ps = j2g(fy - 1, fye_md[0], fye_md[1]); e = j2g(fy, fye_md[0], min(fye_md[1], 30))
                w = cl[(cl["recDate"] > ps[0] * 10000 + ps[1] * 100 + ps[2]) & (cl["recDate"] <= e[0] * 10000 + e[1] * 100 + e[2])]
                if len(w) < 10: continue
                bi, bn, si, sn = (w[c].sum() for c in ("buy_I_Volume", "buy_N_Volume", "sell_I_Volume", "sell_N_Volume"))
                rows[(fid, fy)].update(ct_ind_buy_share=bi / (bi + bn) if bi + bn else np.nan, ct_ind_sell_share=si / (si + sn) if si + sn else np.nan,
                                       ct_ind_net_vol=bi - si, ct_ind_net_ratio=(bi - si) / (bi + bn) if bi + bn else np.nan, ct_ind_buyers_avg=w["buy_CountI"].mean(), ct_leg_buyers_avg=w["buy_CountN"].mean())
        sc = st.get("_share_change") or []
        for fy in range(args.fy_from, args.fy_to + 1):
            ps = j2g(fy - 1, fye_md[0], fye_md[1]); e = j2g(fy, fye_md[0], min(fye_md[1], 30)); lo, hi = ps[0] * 10000 + ps[1] * 100 + ps[2], e[0] * 10000 + e[1] * 100 + e[2]
            n = [x for x in sc if lo < int(x.get("dEven") or 0) <= hi]
            if (fid, fy) in rows: rows[(fid, fy)]["cap_change_n"] = len(n)
        raw = {**(tse.get("info_raw") or {}), **{"id_" + k: v for k, v in (tse.get("identity_raw") or {}).items()}}
        for k, v in raw.items():
            if isinstance(v, (str, int, float)) or v is None:
                for fy in range(args.fy_from, args.fy_to + 1): rows[(fid, fy)]["tseinfo_" + str(k)] = v
        for h in tse.get("holders_snapshot", []): hold.append({"firm_id": fid, "symbol": sym, **h})
    df = pd.DataFrame(list(rows.values())).sort_values(["firm_id", "fiscal_year"])
    # مشتقات: عدم تغییر مدیرعامل، تغییر تعداد کارکنان، خطای پیش‌بینی فروش
    for c in ("ceo_name", "fc_sales_est", "fc_sales_last_actual"):
        if c not in df: df[c] = np.nan
    df["ceo_nochange"] = (df.groupby("firm_id")["ceo_name"].shift(1) == df["ceo_name"]).astype("float").where(df["ceo_name"].notna() & df.groupby("firm_id")["ceo_name"].shift(1).notna())
    if "audit_firm" in df:
        g = df.groupby("firm_id")["audit_firm"]; prev = g.shift(1)
        df["audit_firm_change"] = (df["audit_firm"].notna() & prev.notna() & (df["audit_firm"] != prev)).astype(float).where(df["audit_firm"].notna() & prev.notna())
        blk = df["audit_firm_change"].fillna(0).groupby(df["firm_id"]).cumsum(); ok = df["audit_firm"].notna()
        df["audit_tenure"] = np.nan; df.loc[ok, "audit_tenure"] = df[ok].groupby(["firm_id", blk[ok]]).cumcount() + 1
    if "fc_sales_est" in df:
        df["fc_sales_error"] = (df["fc_sales_last_actual"] - df.groupby("firm_id")["fc_sales_est"].shift(1)) / df.groupby("firm_id")["fc_sales_est"].shift(1).abs()
    if "export_total_row" in df: df["export_flag"] = df["export_total_row"].map(lambda s: int(isinstance(s, str) and any(abs(v) > 0 for v in json.loads(s))) if isinstance(s, str) else np.nan)
    ok = lambda c: df[c].isin(list(OKSTAT)).astype(int) if c in df else 0
    cov = pd.DataFrame({"fiscal_year": df["fiscal_year"], "firm_id": df["firm_id"], "symbol": df["symbol"],
                        "excel": df["cov_excel"].fillna(0).astype(int) if "cov_excel" in df else 0, "audit_pdf": ok("audit_status"), "board_report": ok("br_status"), "internal_control": ok("ic_status")})
    cov.to_csv(os.path.join(out_dir, "coverage_by_firm_year.csv"), index=False, encoding="utf-8-sig")
    print("پوشش (تعداد شرکت-سال با فایل) به تفکیک سال:\n", cov.groupby("fiscal_year")[["excel", "audit_pdf", "board_report", "internal_control"]].sum().to_string())
    df.to_csv(os.path.join(out_dir, "features_firm_year.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame(ev_rows).to_csv(os.path.join(out_dir, "letters_index.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame(mem_rows).to_csv(os.path.join(out_dir, "board_members.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame(hold).to_csv(os.path.join(out_dir, "shareholders_snapshot.csv"), index=False, encoding="utf-8-sig")
    try: df.to_excel(os.path.join(out_dir, "features_firm_year.xlsx"), index=False)
    except Exception as e: print("اکسل نوشته نشد:", e)
    print("ساخته شد:", df.shape, "→", os.path.join(out_dir, "features_firm_year.csv"))

def file_gaps(S, args):
    rows = []
    for i_, r_ in S.iterrows():
        sym = norm(r_["Symbol"]); fid = int(float(r_.get("firm_id", i_))); base = os.path.join(args.files_dir, "%s_%s" % (fid, re.sub(r'[\\/:*?"<>|]', "_", sym)))
        for fy in range(args.fy_from, args.fy_to + 1):
            d = os.path.join(base, str(fy)); fl = os.listdir(d) if os.path.isdir(d) else []
            has = lambda p: int(any(f.startswith(p) and not f.endswith("_manifest.json") for f in fl))
            rows.append({"firm_id": fid, "symbol": sym, "fiscal_year": fy, "folder": int(os.path.isdir(d)), "excel": has("FS_excel"), "audit_fs_pdf": has("audit_FS"), "board_report": has("board_report"), "internal_control": has("internal_control")})
    df = pd.DataFrame(rows); os.makedirs(args.out, exist_ok=True); df.to_csv(os.path.join(args.out, "file_gaps.csv"), index=False, encoding="utf-8-sig")
    print("تعداد شرکت-سال دارای فایل، به تفکیک سال (از %d شرکت):" % len(S)); print(df.groupby("fiscal_year")[["folder", "excel", "audit_fs_pdf", "board_report", "internal_control"]].sum().to_string())
    print("\nجزئیات:", os.path.join(args.out, "file_gaps.csv"), "(ستون‌های ۰/۱ برای هر شرکت-سال)")

def _parse_one(args, sym, company, fid):
    try: process_firm(sym, company, fid, args, None, None, args.out, lambda m: None); return sym, None
    except Exception as e: return sym, "%s %s" % (type(e).__name__, str(e)[:100])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--symbols", default="my_symbols.csv"); ap.add_argument("--out", default="out_codal"); ap.add_argument("--seed-from", default="out", help="پوشهٔ داده‌های قبلی (بازار) که در --out کپی می‌شود"); ap.add_argument("--fy-from", type=int, default=1394); ap.add_argument("--fy-to", type=int, default=1404)
    ap.add_argument("--pilot", type=int, default=0, help="فقط N شرکت اول"); ap.add_argument("--min-interval", type=float, default=7.0, help="حداقل فاصله درخواست‌های کدال (ثانیه)")
    ap.add_argument("--max-requests", type=int, default=150, help="سقف درخواست کدال در هر دسته، سپس استراحت"); ap.add_argument("--build", action="store_true")
    ap.add_argument("--stage", choices=["tse", "docs-tse", "codal", "all"], default="all", help="tse = فقط بازار؛ docs-tse = اسناد (حسابرس/هیئت‌مدیره/کنترل داخلی) از تی‌اس‌ای‌سی بدون کپچا، فقط برای شرکت‌هایی که فهرست نامه‌هایشان قبلاً گرفته شده؛ codal = بازار+کدال")
    ap.add_argument("--part", default="1/1", help="برای تقسیم کدال به چند مرحله: k/n مثلاً 2/5 یعنی بخش دوم از پنج بخش")
    ap.add_argument("--workers", type=int, default=6, help="تعداد رشته‌های هم‌زمان برای مرحلهٔ tse")
    ap.add_argument("--no-client", action="store_true", default=True, help="حقیقی/حقوقی را نگیر (تا آدرس درست پیدا شود)")
    ap.add_argument("--docs", action="store_true", default=True, help="گزارش حسابرس/هیئت‌مدیره/کنترل داخلی را هم بگیر (PDF؛ درخواست زیاد)")
    ap.add_argument("--no-docs", dest="docs", action="store_false"); ap.add_argument("--docs-from", type=int, default=1394, help="اسناد از این سال مالی")
    ap.add_argument("--files-dir", default="codal_files", help="پوشهٔ فایل‌های خام کدال: <firm>/<سال>/...")
    ap.add_argument("--reparse", action="store_true", help="فقط از روی فایل‌های ذخیره‌شده دوباره بخوان (بدون هیچ درخواست به کدال)")
    ap.add_argument("--interactive", action="store_true", help="با کپچا/۴۲۹ بایست تا خودتان در مرورگر حل کنید و Enter بزنید")
    ap.add_argument("--cookie", default=None, help="رشتهٔ Cookie مرورگر شما (پس از حل کپچا) برای codal.ir")
    ap.add_argument("--user-agent", default=None, help="User-Agent همان مرورگر (اگر کوکی می‌دهید)")
    ap.add_argument("--no-save", action="store_true", help="فایل‌ها را روی دیسک ذخیره نکن؛ فقط در حافظه بخوان و برو بعدی")
    ap.add_argument("--retry-failed", action="store_true", help="موارد ناموفق قبلی (اکسل/سند) را هم دوباره امتحان کن (پیش‌فرض: یک بار فقط)")
    ap.add_argument("--force", action="store_true", help="شرکت‌های کامل‌شده را هم دوباره بررسی کن")
    ap.add_argument("--fast-list", action="store_true", help="فهرست نامه‌ها را فقط برای نوع‌های لازم بگیر (درخواست بسیار کمتر؛ ولی متغیرهای رویدادی ev_* ناقص می‌شوند)")
    ap.add_argument("--letter-types", default="6,90", help="شناسهٔ LetterType برای --fast-list: 6=صورت مالی، 90=کنترل داخلی؛ شناسهٔ گزارش هیئت‌مدیره را با کاما اضافه کنید")
    ap.add_argument("--search-interval", type=float, default=5.0, help="فاصلهٔ درخواست‌های جست‌وجوی فهرست نامه‌ها (ثانیه)؛ جدا از --min-interval که برای فایل‌هاست")
    ap.add_argument("--docs-source", choices=["tse", "codal", "both"], default="tse", help="منبع PDF/پیوست‌ها: tse = cdn.tsetmc.com (بدون کپچا، پیش‌فرض)، codal، یا both")
    ap.add_argument("--list-source", choices=["tse", "codal"], default="tse", help="منبع فهرست نامه‌ها: tse = یک درخواست از cdn.tsetmc.com (بدون کپچا، پیش‌فرض)؛ codal = جست‌وجوی صفحه‌به‌صفحهٔ کدال")
    ap.add_argument("--fill-codal", action="store_true", help="برای شرکت-سال‌هایی که از تی‌اس‌ای‌سی ناقص مانده، فهرست کامل کدال را بگیر و آنچه نبود را از کدال تکمیل کن")
    ap.add_argument("--extract", action="store_true", help="در مرحلهٔ docs-tse متن PDFها را هم هم‌زمان استخراج کن (پیش‌فرض: فقط دانلود؛ استخراج جدا و موازی با --reparse)")
    ap.add_argument("--procs", type=int, default=0, help="تعداد پردازش موازی برای --reparse (پیش‌فرض: تعداد هسته‌ها منهای یک)")
    ap.add_argument("--download-only", action="store_true", help="فقط دانلود و ذخیرهٔ فایل؛ هیچ استخراجی (اکسل/PDF) انجام نشود. استخراج بعداً با --reparse")
    ap.add_argument("--file-gaps", action="store_true", help="فقط پوشهٔ codal_files را اسکن کن و گزارش بده کدام شرکت-سال کدام فایل را ندارد (file_gaps.csv)")
    ap.add_argument("--wait-start", type=float, default=30, help="اولین استراحت پس از ۴۲۹/کپچا (دقیقه)"); ap.add_argument("--wait-max", type=float, default=180, help="سقف استراحت (دقیقه)")
    ap.add_argument("--burst-rest", type=float, default=20, help="استراحت پس از رسیدن به سقف درخواست (دقیقه)"); ap.add_argument("--max-hours", type=float, default=96, help="حداکثر زمان کل اجرا (ساعت)")
    args = ap.parse_args(); os.makedirs(os.path.join(args.out, "firms"), exist_ok=True)
    bad_ = repair_firms(args.out)
    if bad_: print(f"{len(bad_)} فایل وضعیت خراب کنار گذاشته شد (فایل‌های دانلودشده سر جایشان است)؛ دوباره ساخته می‌شوند:", bad_[:10])
    if args.seed_from and args.seed_from != args.out and os.path.isdir(os.path.join(args.seed_from, "firms")):
        import shutil
        for fn in os.listdir(os.path.join(args.seed_from, "firms")):
            dst = os.path.join(args.out, "firms", fn)
            if not os.path.exists(dst): shutil.copy2(os.path.join(args.seed_from, "firms", fn), dst)
    if args.build: return build(args.out, args)
    global NO_EXTRACT; NO_EXTRACT = bool(args.download_only and not args.reparse)
    S = pd.read_csv(args.symbols, dtype=str, encoding="utf-8-sig"); S = S.head(args.pilot) if args.pilot else S
    pk, pn = (int(x) for x in args.part.split("/")); sz = -(-len(S) // pn); S = S.iloc[(pk - 1) * sz: pk * sz]; print(f"بخش {pk}/{pn}: {len(S)} شرکت | مرحله: {args.stage}")
    codal, tse = (None if args.reparse else Codal(args.min_interval, args.max_requests, cookie=args.cookie, user_agent=args.user_agent, search_interval=args.search_interval)), Tse()
    t0 = time.time(); wait_min = args.wait_start
    if args.file_gaps: return file_gaps(S, args)
    if args.reparse:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        n = args.procs or max((os.cpu_count() or 2) - 1, 1); print(f"استخراج از روی فایل‌های ذخیره‌شده با {n} پردازش موازی…")
        jobs = [(norm(r_["Symbol"]), r_.get("company", ""), int(float(r_.get("firm_id", i_)))) for i_, r_ in S.iterrows()]; done = 0
        with ProcessPoolExecutor(n) as ex:
            futs = [ex.submit(_parse_one, args, *j) for j in jobs]
            for f_ in as_completed(futs):
                sym_, err = f_.result(); done += 1; print(f"[{done}/{len(jobs)}] {sym_}" + (f" ⚠ {err}" if err else " ✓"))
        print("زمان: %.0f دقیقه" % ((time.time() - t0) / 60)); return build(args.out, args)
    if args.stage not in ("tse", "docs-tse") and not args.reparse:
        sig = "%s-%s-%d-%s" % (args.fy_from, args.fy_to, int(args.docs), args.docs_from); done = 0
        for _, r_ in S.iterrows():
            p_ = os.path.join(args.out, "firms", f"{re.sub(r'[^0-9A-Za-z_]', '_', norm(r_['Symbol'])) or 'x'}_{int(float(r_.get('firm_id', 0)))}.json")
            try: done += int(json.load(open(p_, encoding="utf-8")).get("complete_sig") == sig)
            except Exception: pass
        print(f"از {len(S)} شرکت این بخش، {done} شرکت از قبل کامل است و بدون درخواست رد می‌شود.")
    if args.stage in ("tse", "docs-tse"):
        from concurrent.futures import ThreadPoolExecutor
        def work(item):
            i, r = item; sym = norm(r["Symbol"]); fid = int(float(r.get("firm_id", i))); T = Tse(min_interval=0.15)
            try: process_firm(sym, r.get("company", ""), fid, args, None, T, args.out, lambda m, sym=sym: print(f"[{sym}]{m}"))
            except Exception as ex: print(f"[{sym}] ⚠ خطا: {type(ex).__name__} {str(ex)[:100]}")
        with ThreadPoolExecutor(args.workers) as ex: list(ex.map(work, list(S.iterrows())))
        print("زمان: %.0f دقیقه" % ((time.time() - t0) / 60)); return build(args.out, args)
    try:
        for i, r in S.iterrows():
            sym = norm(r["Symbol"]); fid = int(float(r.get("firm_id", i)))
            print(f"[{i + 1}/{len(S)}] {sym} ({r.get('company', '')})")
            while True:
                try: process_firm(sym, r.get("company", ""), fid, args, codal, tse, args.out, print); wait_min = args.wait_start; break
                except Blocked as e:
                    if (time.time() - t0) / 3600 > args.max_hours: raise
                    if args.interactive and "سقف" not in str(e):
                        print(f"\a\n⏸ {e}\n  → کپچا را در مرورگر حل کنید و Enter بزنید (q+Enter = توقف). اگر تا {args.wait_start:.0f} دقیقه چیزی نزنید، خودکار دوباره امتحان می‌کند.")
                        ans = wait_enter(args.wait_start * 60)
                        if ans == "q": raise
                        codal.n = 0; continue
                    capped = "سقف" in str(e)
                    w = args.burst_rest if capped else wait_min
                    print(f"\n⏸ {e}  → استراحت {w:.0f} دقیقه و ادامهٔ خودکار ({time.strftime('%H:%M')})"); time.sleep(w * 60)
                    codal.n = 0
                    if not capped: wait_min = min(wait_min * 1.5, args.wait_max)
    except Blocked as e: print("\n⛔ پایان بر اثر سقف زمانی:", e)
    except KeyboardInterrupt: print("\nقطع شد توسط کاربر؛ پیشرفت ذخیره است.")
    print("زمان: %.0f دقیقه" % ((time.time() - t0) / 60)); build(args.out, args)

if __name__ == "__main__": main()
