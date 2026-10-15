#!/usr/bin/env python3
"""
جمع‌آوری داده‌های کدال و TSETMC برای دو مقاله (DIV و بندهای پیمان).

هشدار: این کد در محیط توسعه من آزمون نشد، چون codal.ir و tsetmc.com از آنجا
در دسترس نبودند. نام endpointها و فیلدها بر پایه ساختار شناخته‌شده سایت‌هاست
اما ممکن است تغییر کرده باشد. در مرورگر (F12 > Network) درخواست‌ها را ببینید
و در صورت اختلاف، فقط بخش CONFIG را اصلاح کنید.
اجرا باید از شبکه ایران (یا VPN مجاز) انجام شود.

نصب:  pip install requests pandas openpyxl beautifulsoup4 lxml
اجرا: python codal_collector.py list   --from 1393/01/01 --to 1402/12/29
      python codal_collector.py fetch  --limit 50      # دانلود صفحه صورت مالی
      python codal_collector.py parse                  # استخراج اقلام به CSV
"""
import argparse, json, re, sys, time, pathlib
import requests, pandas as pd

CONFIG = {
    "search_url": "https://search.codal.ir/api/search/v2/q",
    "base": "https://codal.ir",
    # LetterType=6 معمولاً «اطلاعات و صورت‌های مالی سالانه» است؛ در سایت بررسی کنید
    "params": {"Audited": "true", "AuditorRef": "-1", "Category": "1", "Childs": "true",
               "CompanyState": "0", "CompanyType": "1", "Consolidatable": "true",
               "IsNotAudited": "false", "Length": "-1", "LetterType": "6",
               "Mains": "true", "NotAudited": "false", "NotConsolidatable": "true",
               "Publisher": "false", "TracingNo": "-1", "search": "true"},
    "sleep": 1.5,           # مکث مؤدبانه بین درخواست‌ها
    "out": pathlib.Path("data_out"),
}
HEADERS = {"User-Agent": "Mozilla/5.0 (research; academic use)", "Accept": "application/json, text/html"}
CONFIG["out"].mkdir(exist_ok=True)

def get(url, **kw):
    for i in range(4):
        try:
            r = requests.get(url, headers=HEADERS, timeout=40, **kw)
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
        p = dict(CONFIG["params"], PageNumber=page, FromDate=a.from_, ToDate=a.to)
        r = get(CONFIG["search_url"], params=p)
        if r is None: break
        j = r.json()
        letters = j.get("Letters", [])
        if not letters: break
        rows += letters
        print(f"صفحه {page}: {len(letters)} نامه، جمع {len(rows)} از {j.get('Total')}")
        if page >= int(j.get("Page", page)): break
        page += 1; time.sleep(CONFIG["sleep"])
    df = pd.DataFrame(rows)
    df.to_csv(CONFIG["out"] / "letters.csv", index=False, encoding="utf-8-sig")
    print("ذخیره شد:", CONFIG["out"] / "letters.csv", len(df))

def cmd_fetch(a):
    df = pd.read_csv(CONFIG["out"] / "letters.csv")
    d = CONFIG["out"] / "html"; d.mkdir(exist_ok=True)
    n = 0
    for _, r in df.iterrows():
        f = d / f"{r['TracingNo']}.html"
        if f.exists(): continue
        url = r["Url"] if str(r["Url"]).startswith("http") else CONFIG["base"] + str(r["Url"])
        resp = get(url)
        if resp is not None:
            f.write_text(resp.text, encoding="utf-8")
        n += 1; time.sleep(CONFIG["sleep"])
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
    d = CONFIG["out"] / "html"; res = []
    for f in sorted(d.glob("*.html")):
        html = f.read_text(encoding="utf-8")
        ds = extract_datasource(html)
        if not ds:
            print("datasource یافت نشد:", f.name); continue
        cells = cells_from_datasource(ds)
        if cells.empty: continue
        cells["TracingNo"] = f.stem
        cells.to_csv(CONFIG["out"] / f"cells_{f.stem}.csv", index=False, encoding="utf-8-sig")
        # حسابرس: جست‌وجوی متنی در صفحه (باید دستی بررسی شود)
        m = re.search(r"(سازمان حسابرسی|مؤسسه حسابرسی\s+[^\s<]+(?:\s+[^\s<]+){0,2})", html)
        res.append({"TracingNo": f.stem, "auditor_guess": m.group(1) if m else None, "n_cells": len(cells)})
    pd.DataFrame(res).to_csv(CONFIG["out"] / "parsed_index.csv", index=False, encoding="utf-8-sig")
    print("پایان. سپس با ITEMS ردیف‌ها را به متغیر تبدیل و در استتا ادغام کنید.")

def tsetmc_shareholders(inscode):
    """سهامداران عمده؛ endpoint را در مرورگر تأیید کنید."""
    r = get(f"https://cdn.tsetmc.com/api/Shareholder/GetInstrumentShareHolderLast/{inscode}")
    return r.json() if r is not None else None

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="c", required=True)
    l = sp.add_parser("list"); l.add_argument("--from", dest="from_", default="1393/01/01"); l.add_argument("--to", default="1402/12/29")
    f = sp.add_parser("fetch"); f.add_argument("--limit", type=int, default=0)
    sp.add_parser("parse")
    a = ap.parse_args()
    {"list": cmd_list, "fetch": cmd_fetch, "parse": cmd_parse}[a.c](a)
