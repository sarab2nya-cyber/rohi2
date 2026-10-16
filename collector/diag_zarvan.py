# بررسی سایت zarvanfund.ir/codal — خروجی را بفرستید (فیلترشکن را مطابق نیاز روشن/خاموش کنید تا سایت باز شود)
import re, requests, json, sys
H = {"User-Agent": "Mozilla/5.0 (research; academic use)", "Accept": "*/*"}
BASE = "https://zarvanfund.ir"
def get(u, **k):
    try: return requests.get(u, headers=H, timeout=(15, 60), **k)
    except Exception as e: print("خطا:", u, type(e).__name__, str(e)[:100]); return None
print("robots.txt:"); r = get(BASE + "/robots.txt"); print(r.status_code if r is not None else None, (r.text[:400] if r is not None else ""))
r = get(BASE + "/codal")
if r is not None:
    t = r.text; open("zarvan_codal.html", "w", encoding="utf-8").write(t)
    print("\nصفحه:", r.status_code, len(t), r.headers.get("Content-Type"), "| ذخیره شد: zarvan_codal.html")
    print("عنوان:", re.findall(r"<title>(.*?)</title>", t, re.S)[:1])
    print("اسکریپت‌ها:", re.findall(r'<script[^>]+src="([^"]+)"', t)[:15])
    links = re.findall(r'href="([^"]+)"', t); print("لینک‌ها (نمونه):", links[:25])
    print("لینک‌های pdf:", [l for l in links if "pdf" in l.lower() or "download" in l.lower() or "file" in l.lower()][:15])
    print("آدرس‌های api در متن:", sorted(set(re.findall(r'["\'](/api/[^"\']+|https?://[^"\']*api[^"\']*)["\']', t)))[:20])
    print("\n۸۰۰ نویسهٔ اول بدنه:", re.sub(r"\s+", " ", re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", t, flags=re.S))[:800])
