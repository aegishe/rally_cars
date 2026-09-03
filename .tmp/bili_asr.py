# -*- coding: utf-8 -*-
import sys, json, time
import requests

BVID = "BV1SDbZ6sEvV"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
HEADERS = {"User-Agent": UA, "Referer": "https://www.bilibili.com"}

def get_view():
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={BVID}"
    r = requests.get(url, headers=HEADERS, timeout=20)
    print("[view] status", r.status_code)
    j = r.json()
    print("[view] code", j.get("code"), j.get("message"))
    data = j.get("data") or {}
    print("[view] aid", data.get("aid"), "cid", data.get("cid"), "title", data.get("title"))
    return data

def get_playurl(aid, cid):
    url = f"https://api.bilibili.com/x/player/playurl?avid={aid}&cid={cid}&qn=64&fnval=16&fourk=0"
    r = requests.get(url, headers=HEADERS, timeout=20)
    print("[playurl] status", r.status_code)
    j = r.json()
    print("[playurl] code", j.get("code"), j.get("message"))
    return j

def main():
    view = get_view()
    if not view:
        print("NO VIEW DATA"); return 1
    aid = view.get("aid"); cid = view.get("cid")
    if not aid or not cid:
        print("MISSING aid/cid"); return 1
    j = get_playurl(aid, cid)
    dash = (j.get("data") or {}).get("dash") or {}
    audios = dash.get("audio") or []
    if not audios:
        print("NO AUDIO STREAMS, code=", j.get("code")); 
        print(json.dumps(j, ensure_ascii=False)[:2000])
        return 1
    # pick highest bandwidth
    audios.sort(key=lambda x: x.get("bandwidth", 0), reverse=True)
    best = audios[0]
    print("[audio] bandwidth", best.get("bandwidth"), "codecs", best.get("codecs"), "size~", best.get("bandwidth",0)*17.4*60/8/1024/1024, "MB")
    base = best.get("baseUrl") or best.get("base_url")
    if not base:
        print("NO baseUrl"); print(json.dumps(best, ensure_ascii=False)[:2000]); return 1
    print("[audio] downloading...")
    r = requests.get(base, headers={"User-Agent": UA, "Referer": "https://www.bilibili.com"}, timeout=120)
    print("[audio] dl status", r.status_code, "bytes", len(r.content))
    if r.status_code != 200:
        print(r.text[:500]); return 1
    out = r"D:\Project\dsh_rally_cars\.tmp\bili_audio.m4s"
    with open(out, "wb") as f:
        f.write(r.content)
    print("[audio] saved", out, len(r.content))
    return 0

if __name__ == "__main__":
    sys.exit(main())
