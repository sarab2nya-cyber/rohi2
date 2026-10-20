# بررسی صفحهٔ پیوست کدال: python diag_attach.py > diag_attach.txt
# اگر کپچا آمد: ابتدا در مرورگر حل کنید، سپس با --cookie "..." --user-agent "..." اجرا کنید.
import sys
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
import argparse, re, sys, time, requests
URLS = ["https://codal.ir/Reports/Attachment.aspx?LetterSerial=XCZEfwG5j0GuFxnaKD6qfw%3d%3d",
        "https://codal.ir/Reports/Attachment.aspx?LetterSerial=GcPCDJO8M8OKWwMszH6s6Q%3d%3d"]
ap = argparse.ArgumentParser(); ap.add_argument("--cookie"); ap.add_argument("--user-agent"); ap.add_argument("urls", nargs="*")
a = ap.parse_args(); urls = a.urls or URLS
H = {"User-Agent": a.user_agent or "Mozilla/5.0 (research; academic use)", "Accept": "*/*"}
if a.cookie: H["Cookie"] = a.cookie
def get(u):
    try: return requests.get(u, headers=H, timeout=(15, 60))
    except Exception as e: print("   خطا:", type(e).__name__, str(e)[:100]); return None
for k, u in enumerate(urls, 1):
    print(f"\n=== {k}) {u}")
    r = get(u)
    if r is None: continue
    t = r.text; title = re.findall(r"<title>(.*?)</title>", t, re.S)
    print("وضعیت:", r.status_code, "| نوع:", r.headers.get("Content-Type"), "| حجم:", len(r.content), "| عنوان:", [re.sub(r'\s+', ' ', x).strip() for x in title][:1])
    open(f"attach_page_{k}.html", "w", encoding="utf-8").write(t)
    links = []
    for m in re.finditer(r"""(?:href|src|data-url|data-href|onclick)\s*=\s*["']([^"']+)["']""", t):
        x = m.group(1).replace("&amp;", "&")
        if re.search(r"DownloadFile|\.pdf|\.xls|\.doc|\.zip|\.rar|GetFile|Download|Attachment", x, re.I) and x not in links: links.append(x)
    print("لینک‌های فایل‌مانند:", links[:15])
    print("۴۰۰ نویسهٔ متن صفحه:", re.sub(r"\s+", " ", re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", t, flags=re.S))[:400])
    for j, x in enumerate(links[:4], 1):
        time.sleep(8); full = x if x.startswith("http") else "https://codal.ir/" + x.lstrip("/")
        rr = get(full)
        if rr is not None: print(f"   [{j}] {full[:110]} -> {rr.status_code} | {rr.headers.get('Content-Type')} | {len(rr.content)} بایت | شروع={rr.content[:8]!r} | {rr.headers.get('Content-Disposition')}")
    time.sleep(10)
print("\nفایل‌های attach_page_*.html ذخیره شد؛ همراه خروجی بفرستید.")
