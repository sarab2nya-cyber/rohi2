# آیا اکسل نامه‌های کدال از تی‌اس‌ای‌سی هم گرفتنی است؟ python diag_tse_excel.py > diag_tse_excel.txt
import sys
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
import requests
H = {"User-Agent": "Mozilla/5.0 (research; academic use)", "Accept": "*/*", "Connection": "close"}
NOS = {"صورت مالی سالانه حسابرسی‌شده (فپنتا، دارای اکسل)": "1551248", "میان‌دوره‌ای حسابرسی‌شده (دارای اکسل)": "1611059"}
for name, no in NOS.items():
    print("\n#####", name, no)
    urls = [f"https://cdn.tsetmc.com/api/Codal/GetContentFileByTracingNo/{no}/{t}" for t in range(0, 8)] + \
           [f"https://cdn.tsetmc.com/api/Codal/GetAttachmentContentFileByTracingNoAndRowOrder/{no}/{r}" for r in (0, 1, 2)]
    for u in urls:
        try:
            r = requests.get(u, headers=H, timeout=(20, 120)); d = r.content
            print(u.split("/api/")[1], "->", r.status_code, len(d), r.headers.get("Content-Type"), "| شروع:", d[:60])
        except Exception as e: print(u.split("/api/")[1], "-> خطا", type(e).__name__, str(e)[:80])
