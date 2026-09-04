import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests

vid = "Wercpk28guY"
proxies = {'http': 'http://127.0.0.1:2081', 'https': 'http://127.0.0.1:2081'}
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36'}

base = "https://inv.nadeko.net"
r = requests.get(f"{base}/api/v1/videos/{vid}", proxies=proxies, headers=headers, timeout=30)
print("STATUS", r.status_code, "LEN", len(r.text))
if r.status_code == 200:
    data = r.json()
    print("TITLE:", data.get("title"))
    print("AUTHOR:", data.get("author"))
    print("LENGTH:", data.get("lengthSeconds"))
    print("DESC:", (data.get("description") or "")[:600])
    caps = data.get("captions", [])
    print("CAPTIONS:")
    for c in caps:
        print("  ", json.dumps(c, ensure_ascii=False)[:300])
