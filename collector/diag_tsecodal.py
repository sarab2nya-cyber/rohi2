# ساختار پاسخ GetPreparedDataByInsCode را بررسی می‌کند: python diag_tsecodal.py > diag_tsecodal.txt
import sys
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
import json, requests, sys
H = {"User-Agent": "Mozilla/5.0 (research; academic use)", "Accept": "*/*", "Connection": "close"}
INS = "68488673556087148"
def show(name, u):
    try: r = requests.get(u, headers=H, timeout=(20, 120))
    except Exception as e: print("\n", name, "-> خطا", type(e).__name__, str(e)[:100]); return None
    print("\n==", name, u, "->", r.status_code, len(r.content), r.headers.get("Content-Type"))
    try: j = r.json()
    except Exception: print("   غیر JSON:", r.text[:300].replace("\n", " ")); return None
    open(name + ".json", "w", encoding="utf-8").write(json.dumps(j, ensure_ascii=False)[:5_000_000])
    def struct(o, d=0):
        if isinstance(o, dict): return {k: (struct(v, d + 1) if d < 2 else type(v).__name__) for k, v in list(o.items())[:25]}
        if isinstance(o, list): return [f"list[{len(o)}]", struct(o[0], d + 1) if o and d < 2 else None]
        return type(o).__name__
    print("   ساختار:", json.dumps(struct(j), ensure_ascii=False)[:1500])
    L = j if isinstance(j, list) else next((v for v in j.values() if isinstance(v, list)), []) if isinstance(j, dict) else []
    print("   تعداد ردیف:", len(L))
    for x in L[:3]: print("   نمونه:", json.dumps(x, ensure_ascii=False)[:700])
    if L: print("   آخرین ردیف:", json.dumps(L[-1], ensure_ascii=False)[:500])
    return j
show("prepared_99999", f"https://cdn.tsetmc.com/api/Codal/GetPreparedDataByInsCode/99999/{INS}")
show("prepared_0", f"https://cdn.tsetmc.com/api/Codal/GetPreparedDataByInsCode/0/{INS}")
show("prepared_20", f"https://cdn.tsetmc.com/api/Codal/GetPreparedDataByInsCode/20/{INS}")
print("\nفایل‌های prepared_*.json ذخیره شد؛ همراه خروجی بفرستید.")
