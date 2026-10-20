# بررسی old.tsetmc.com برای اطلاعیه‌ها: python diag_oldtse.py > diag_oldtse.txt   (فیلترشکن را طوری بگذارید که سایت باز شود)
import re, requests, time
H = {"User-Agent": "Mozilla/5.0 (research; academic use)", "Accept": "*/*"}
INS = "68488673556087148"
def get(u):
    try: return requests.get(u, headers=H, timeout=(20, 90))
    except Exception as e: print("خطا:", u, type(e).__name__, str(e)[:100]); return None
main = "https://old.tsetmc.com/Loader.aspx?ParTree=151311&i=" + INS
r = get(main)
if r is not None:
    t = r.text; open("oldtse_main.html", "w", encoding="utf-8").write(t)
    print("صفحه:", r.status_code, len(t), "| عنوان:", re.findall(r"<title>(.*?)</title>", t, re.S)[:1])
    links = sorted(set(re.findall(r"""(?:href|src)=["']([^"']+)["']""", t)))
    print("لینک‌های codal:", [l for l in links if "codal" in l.lower()][:15])
    print("لینک‌های Loader/تب:", [l for l in links if "Loader" in l or "tsev2" in l.lower()][:30])
    print("عبارت‌های «اطلاعیه/کدال» در متن:", [m for m in re.findall(r"[^<>]{0,40}(?:اطلاعیه|کدال)[^<>]{0,40}", t)][:15])
    cand = [l for l in links if re.search(r"Loader\.aspx\?Partree=15131", l, re.I) and l != main][:6]
    for l in cand:
        time.sleep(3); u = l if l.startswith("http") else "https://old.tsetmc.com/" + l.lstrip("/")
        rr = get(u)
        if rr is not None: print("\n--", u[:120], "->", rr.status_code, len(rr.text), re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", rr.text))[:300])
