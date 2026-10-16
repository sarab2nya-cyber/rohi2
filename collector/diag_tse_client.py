# تست چند آدرس تی‌اس‌ای‌سی برای «حقیقی/حقوقی» — خروجی را کپی کنید و بفرستید
import requests, json
H = {"User-Agent": "Mozilla/5.0 (research; academic use)", "Accept": "*/*", "Connection": "close"}
ins = "18004480270695404"   # فمراد
for u in ("ClientType/GetClientTypeHistory/%s/0" % ins, "ClientType/GetClientTypeHistory/%s/20240320" % ins, "ClientType/GetClientType/%s/1/0" % ins,
          "ClientType/GetClientTypeAll", "Instrument/GetInstrumentShareChange/%s" % ins, "Shareholder/GetInstrumentShareHolderHistory/%s" % ins):
    try:
        r = requests.get("https://cdn.tsetmc.com/api/" + u, headers=H, timeout=(20, 90))
        print("\n", u, "->", r.status_code, len(r.content), "\n   ", r.text[:500].replace("\n", " "))
    except Exception as e: print("\n", u, "-> خطا", type(e).__name__, str(e)[:100])
