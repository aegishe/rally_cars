import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests

vid = "Wercpk28guY"
proxies = {'http': 'http://127.0.0.1:2081', 'https': 'http://127.0.0.1:2081'}
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36'}

instances = [
    "https://inv.nadeko.net",
    "https://invidious.nerdvpn.de",
    "https://inv.tux.pizza",
    "https://iv.ggtyler.dev",
    "https://invidious.f5.si",
]

for base in instances:
    try:
        r = requests.get(f"{base}/api/v1/captions/{vid}", proxies=proxies, headers=headers, timeout=20)
        if r.status_code != 200:
            print(f"{base}: LIST status {r.status_code}")
            continue
        caps = r.json().get("captions", [])
        if not caps:
            print(f"{base}: no captions")
            continue
        c = caps[0]
        url = c["url"]
        if url.startswith("/"):
            url = base + url
        # add lang param
        if "lang=" not in url:
            url += "&lang=en"
        rc = requests.get(url, proxies=proxies, headers=headers, timeout=30)
        print(f"{base}: label={c.get('label')} status={rc.status_code} len={len(rc.text)}")
        if rc.status_code == 200 and len(rc.text) > 50:
            with open(r"D:\Project\dsh_rally_cars\_tmp_captions.vtt", "w", encoding="utf-8") as f:
                f.write(rc.text)
            print("  SAVED. first 500:")
            print(rc.text[:500])
            break
    except Exception as e:
        print(f"{base}: ERR {type(e).__name__} {e}")
