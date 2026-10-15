#!/usr/bin/env python3
"""TSETMC: صنعت، تعداد سهام، سهامداران عمده، قیمت پایانی (برای MTB و مالکیت).
ورودی: data_out/symbols.csv با ستون‌های Symbol,InsCode (کد ۱۶ رقمی TSETMC را از سایت بردارید).
endpointها آزمون نشده‌اند؛ config.TSE_ENDPOINTS را در F12 تأیید کنید.
"""
import sys, time, json, requests, pandas as pd
import config as C
H = {"User-Agent": "Mozilla/5.0 (research; academic use)"}

def get(url):
    for i in range(4):
        try:
            r = requests.get(url, headers=H, timeout=40)
            if r.status_code == 200: return r.json()
            print("HTTP", r.status_code, url, file=sys.stderr)
        except Exception as e:
            print("خطا", e, file=sys.stderr)
        time.sleep(2 ** (i + 1))

def main():
    sy = pd.read_csv(C.OUT / "symbols.csv", dtype=str)
    inst, hold, px = [], [], []
    for _, r in sy.iterrows():
        ins = r["InsCode"]
        j = get(C.TSE_ENDPOINTS["instrument"].format(ins=ins))
        if j:
            i = j.get("instrumentInfo", j)
            inst.append({"Symbol": r["Symbol"], "InsCode": ins,
                         "sector": (i.get("sector") or {}).get("lSecVal"),
                         "shares": i.get("zTitad")})
        time.sleep(C.SLEEP)
        j = get(C.TSE_ENDPOINTS["shareholders"].format(ins=ins))
        for s in (j or {}).get("shareShareholder", []):
            hold.append({"Symbol": r["Symbol"], "date": s.get("dEven"), "holder": s.get("shareHolderName"),
                         "pct": s.get("perOfShares"), "shares": s.get("numberOfShares")})
        time.sleep(C.SLEEP)
        j = get(C.TSE_ENDPOINTS["prices"].format(ins=ins))
        for p in (j or {}).get("closingPriceDaily", []):
            px.append({"Symbol": r["Symbol"], "date": p.get("dEven"), "close": p.get("pClosing")})
        time.sleep(C.SLEEP)
    for name, rows in (("instruments", inst), ("holders", hold), ("prices", px)):
        pd.DataFrame(rows).to_csv(C.OUT / f"tse_{name}.csv", index=False, encoding="utf-8-sig")
    print("پایان")
if __name__ == "__main__": main()
