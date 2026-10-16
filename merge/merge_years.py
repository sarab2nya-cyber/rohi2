#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ادغام صورت‌های مالی ۱۴۰۳ و ۱۴۰۴ (رهاورد نوین؛ XML اکسل) با اکسل اصلی ۱۳۸۰–۱۴۰۲ در همان چیدمان ستون‌های اکسل اصلی.

اجرا:
  python merge_years.py --main Main_1380_1402.xlsx --raw raw --out panel_1380_1404.xlsx
ساختار raw:  raw/1403/{balance,income,cashflow,ratios,ret12,ret16}.xml   raw/1404/{balance,income,cashflow,ratios,ret_annual}.xml

قواعد:
 - ردیف‌ها: اجتماع شرکت‌های ترازنامه/سود و زیان/جریان نقد/نسبت‌ها (کلید: نام شرکت نرمال‌شده).
 - صنایعی که در اکسل اصلی نیستند (بانک، بیمه، سرمایه‌گذاری، واسطه‌گری مالی، برق، سلامت) حذف می‌شوند (--keep-all برای نگه‌داشتن).
 - بلوک‌های بازده: مجموعه اول = ۱۲ ماهه، مجموعه دوم = ۱۶ ماهه (۱۴۰۴: فقط سالانه؛ مجموعه دوم خالی).
 - شناسه شرکت (ستون «شرکت») از اکسل اصلی؛ شرکت‌های جدید شناسه جدید می‌گیرند.
"""
import argparse, re, sys, pathlib
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import ssml

def N(s):
    return re.sub(r"\s+", " ", str(s).replace("ي", "ی").replace("ك", "ک").replace("‌", " ").replace("‏", "")).strip()

def table(path):
    rows = list(ssml.read(path).values())[0]
    hdr = [str(h) if h is not None else f"_c{i}" for i, h in enumerate(rows[0])]
    w = len(hdr)
    return pd.DataFrame([(r + [None] * w)[:w] for r in rows[1:]], columns=hdr)

FIN_NAME = re.compile(r"^بانک|بانک |بیمه|لیزینگ|^سر\.|سرمایه گذاری|مالی|ارزش آفرینان|سپرده گذاری|تامین آتیه|تعاونی|اعتباری|کارگزاری|صندوق|تامین سرمایه|بورس|هلدینگ مالی|پتروشیمی.*سرمایه")
FIN_COLS = ["مطالبات از بانک مرکزی", "مطالبات از بیمه\u200cگذاران و نمایندگان", "سهم بیمه\u200cگران اتکایی از ذخائر فنی",
            "مطالبات از سایر بانکها و موسسات اعتباری", "مطالبات از دولت"]
# بلوک‌های اکسل اصلی (موقعیت ستون‌ها) و جدول منبع هر بلوک
BLOCKS = {"bal": (0, 155, "balance"), "inc": (156, 287, "income"), "cf": (289, 363, "cashflow"),
          "rat": (365, 404, "ratios"), "ret1": (406, 415, "ret_a"), "ret2": (416, 425, "ret_b")}

def run(a):
    m = pd.read_excel(a.main); cols = list(m.columns); sc = [str(c) for c in cols]
    base = lambda c: re.sub(r"\.\d+$", "", str(c))
    num_cols = {c for c in cols if m[c].dtype.kind in "fi"}
    m["_n"] = m["Symbol"].map(N); m["_t"] = m["نماد"].map(N)
    name2id = m.drop_duplicates("_n").set_index("_n")["شرکت"].to_dict()
    name2sym = m.drop_duplicates("_n", keep="last").set_index("_n")["Symbol"].to_dict()
    tick2n = m.sort_values("Year").drop_duplicates("_t", keep="last").set_index("_t")["_n"].to_dict()
    ind_ok = set(m["صنعت"].dropna().map(N))
    ind_codes = m.dropna(subset=["صنعت"]).assign(_i=lambda d: d["صنعت"].map(N)).drop_duplicates("_i").set_index("_i")[["کد صنعت جزئی", "کدصنعت کلی"]]
    ind_cls = m.dropna(subset=["صنعت"]).assign(_i=lambda d: d["صنعت"].map(N)).drop_duplicates("_i").set_index("_i")["طبقه"].to_dict()
    next_id = int(pd.to_numeric(m["شرکت"], errors="coerce").max()) + 1
    out, rep = [], []
    plan = {1403: {"balance": "balance", "income": "income", "cashflow": "cashflow", "ratios": "ratios", "ret_a": "ret12", "ret_b": "ret16"},
            1404: {"balance": "balance", "income": "income", "cashflow": "cashflow", "ratios": "ratios", "ret_a": "ret_annual", "ret_b": None}}
    for y, files in plan.items():
        T = {}
        for k, f in files.items():
            if f is None: T[k] = None; continue
            df = table(str(pathlib.Path(a.raw) / str(y) / f"{f}.xml"))
            df = df.rename(columns={"نام شرکت": "شرکت"})
            df["_n"] = df["شرکت"].map(N); df["_t"] = df["نماد"].map(N) if "نماد" in df else None
            T[k] = df.drop_duplicates("_n").set_index("_n")
        names = set()
        for k in ("balance", "income", "cashflow", "ratios"): names |= set(T[k].index)
        # صنعت: از جدول بازده (نام، سپس نماد)
        ret = T["ret_a"]; rt = ret.reset_index().drop_duplicates("_t").set_index("_t")
        def industry(n):
            if n in ret.index: return N(ret.loc[n, "صنعت"])
            for k in ("balance", "income", "cashflow"):
                if n in T[k].index and T[k].loc[n, "_t"] in rt.index: return N(rt.loc[T[k].loc[n, "_t"], "صنعت"])
            return None
        rows = []
        for n in sorted(names):
            ind = industry(n)
            if ind is None and n in name2sym:                          # از سال‌های قبل در اکسل اصلی
                ind = N(m.loc[m["_n"] == n, "صنعت"].dropna().iloc[-1]) if m.loc[m["_n"] == n, "صنعت"].notna().any() else None
            if ind is None and not a.keep_all:      # صنعت نامشخص: تشخیص مالی بودن از نام یا ستون‌های ویژه بانک/بیمه
                bsrc = T["balance"].loc[n] if n in T["balance"].index else None
                fin_cols = [c for c in FIN_COLS if bsrc is not None and c in bsrc.index and pd.to_numeric(bsrc[c], errors="coerce") not in (0, np.nan) and pd.notna(pd.to_numeric(bsrc[c], errors="coerce"))]
                if FIN_NAME.search(n) or fin_cols:
                    rep.append({"year": y, "company": n, "industry": None, "action": "excluded_financial_by_name_or_columns"}); continue
            keep_ind = (ind in ind_ok) or a.keep_all or ind is None
            if not keep_ind:
                rep.append({"year": y, "company": n, "industry": ind, "action": "excluded_industry"}); continue
            r = {}
            tick = next((T[k].loc[n, "_t"] for k in ("balance", "income", "cashflow") if n in T[k].index and T[k].loc[n, "_t"]), None)
            nn = n
            if n not in name2id and tick in tick2n: nn = tick2n[tick]; rep.append({"year": y, "company": n, "industry": ind, "action": f"matched_by_ticker→{nn}"})
            cid = name2id.get(nn)
            if cid is None: cid = next_id; name2id[nn] = cid; next_id += 1; rep.append({"year": y, "company": n, "industry": ind, "action": "new_company"})
            first = next((T[k].loc[n] for k in ("balance", "income", "cashflow", "ratios") if n in T[k].index), None)
            r["Symbol"] = name2sym.get(nn, first["شرکت"]); r["شرکت"] = cid; r["Year"] = y
            if ind in ind_codes.index: r["کد صنعت جزئی"], r["کدصنعت کلی"] = ind_codes.loc[ind]
            r["صنعت"] = ind; r["طبقه"] = ret.loc[n, "طبقه"] if n in ret.index else ind_cls.get(ind)
            if ind is None: rep.append({"year": y, "company": n, "industry": None, "action": "industry_missing"})
            # ردیف بازده بر اساس نام یا نماد
            def retrow(tab):
                if tab is None: return None
                if n in tab.index: return tab.loc[n]
                t2 = tab.reset_index().drop_duplicates("_t").set_index("_t")
                return t2.loc[tick] if tick in t2.index else None
            srcs = {"balance": T["balance"].loc[n] if n in T["balance"].index else None, "income": T["income"].loc[n] if n in T["income"].index else None,
                    "cashflow": T["cashflow"].loc[n] if n in T["cashflow"].index else None, "ratios": T["ratios"].loc[n] if n in T["ratios"].index else None,
                    "ret_a": retrow(T["ret_a"]), "ret_b": retrow(T["ret_b"])}
            for blk, (lo, hi, sk) in BLOCKS.items():
                s = srcs[sk]
                if s is None: continue
                for c in cols[lo:hi + 1]:
                    if c in r and blk == "bal" and c in ("Symbol", "شرکت", "Year", "کد صنعت جزئی", "کدصنعت کلی", "صنعت", "طبقه"): continue
                    b = base(c)
                    if b in ("سال مالی", "سال") or b not in s.index: continue
                    v = s[b]
                    if c in num_cols: v = pd.to_numeric(v, errors="coerce")
                    r[c] = v
            rows.append(r)
        out.append(pd.DataFrame(rows))
    new = pd.concat(out, ignore_index=True)
    new = new.reindex(columns=cols + ["data_source", "new_company", "industry_missing"])
    for c in num_cols: new[c] = pd.to_numeric(new[c], errors="coerce")
    new["data_source"] = "new_" + new["Year"].astype(int).astype(str)
    flags = pd.DataFrame(rep)
    new["data_source"] = "new_" + new["Year"].astype(int).astype(str)
    new["new_company"] = 0; new["industry_missing"] = 0
    if len(flags):
        key = new["Symbol"].map(N) + "|" + new["Year"].astype(int).astype(str)
        for act, col in (("new_company", "new_company"), ("industry_missing", "industry_missing")):
            ks = set(flags.loc[flags.action == act, "company"].map(N) + "|" + flags.loc[flags.action == act, "year"].astype(str))
            new[col] = key.isin(ks).astype(int)
    m["data_source"] = "main"; m["new_company"] = 0; m["industry_missing"] = 0
    final = pd.concat([m.drop(columns=["_n", "_t"]), new], ignore_index=True).sort_values(["شرکت", "Year"]).reset_index(drop=True)
    assert not final.duplicated(["Symbol", "Year"]).any(), "کلید تکراری"
    final.to_excel(a.out, index=False)
    pd.DataFrame(rep).to_csv(str(a.out) + ".report.csv", index=False, encoding="utf-8-sig")
    print("نهایی:", final.shape, "ردیف جدید:", len(new), "سال‌ها:", new.groupby("Year").size().to_dict())
    print(pd.DataFrame(rep).groupby(["year", "action"]).size() if rep else "")
    return final, new, cols, num_cols

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--main", required=True); ap.add_argument("--raw", default="raw")
    ap.add_argument("--out", default="panel_1380_1404.xlsx"); ap.add_argument("--keep-all", action="store_true")
    run(ap.parse_args())
