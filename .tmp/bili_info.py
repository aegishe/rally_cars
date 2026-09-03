# -*- coding: utf-8 -*-
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
import requests
h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36", "Referer": "https://www.bilibili.com"}
j = requests.get("https://api.bilibili.com/x/web-interface/view?bvid=BV1SDbZ6sEvV", headers=h, timeout=20).json()
d = j["data"]
print("title:", d["title"])
print("owner_name:", d["owner"]["name"])
print("owner_mid:", d["owner"]["mid"])
print("pubdate:", d["pubdate"])
print("duration_s:", d["duration"])
print("desc:")
print(d["desc"])
print("--- stat ---")
print(json.dumps(d["stat"], ensure_ascii=False))
# 分P信息
print("pages:", json.dumps(d.get("pages"), ensure_ascii=False)[:500])
