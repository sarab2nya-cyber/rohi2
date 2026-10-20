# تست دوم حقیقی/حقوقی با روزهای معاملاتی واقعی — خروجی را بفرستید
import sys
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
import requests
H = {"User-Agent": "Mozilla/5.0 (research; academic use)", "Accept": "*/*", "Connection": "close"}
ins = "18004480270695404"   # فمراد
cands = []
for d in ("20240331", "20240401", "20231220"):
    cands += ["ClientType/GetClientTypeHistory/%s/%s" % (ins, d), "ClientType/GetClientType/%s/%s/0" % (ins, d), "ClientType/GetClientType/%s/0/%s" % (ins, d), "ClientType/GetClientType/%s/1/%s" % (ins, d)]
cands += ["ClientType/GetClientTypeAll/%s" % ins, "ClientType/GetClientTypeHistoryAll/%s" % ins]
for u in cands:
    try:
        r = requests.get("https://cdn.tsetmc.com/api/" + u, headers=H, timeout=(20, 60))
        print("\n", u, "->", r.status_code, len(r.content), "\n   ", r.text[:300].replace("\n", " "))
    except Exception as e: print("\n", u, "-> خطا", type(e).__name__, str(e)[:100])
