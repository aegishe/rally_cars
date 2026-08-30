# -*- coding: utf-8 -*-
"""v2: playurl 端点矩阵 + yt_dlp(pip) fallback，然后 Whisper 转写"""
import sys, os, urllib.request, urllib.parse

sys.path.insert(0, r"C:\Users\AegisH\.agents\skills\yt-subs")
import yt_subs as ys  # noqa: E402

BVID = "BV1BUtA65ETM"
WORK = r"D:\Project\dsh_rally_cars\.tmp"
cookie = ys.random_cookies()

# 1) view
bvid, aid = ys._parse_bv_av(BVID)
params = ys._wbi_sign({"bvid": bvid}, cookie)
view = ys._http_get(f"https://api.bilibili.com/x/web-interface/wbi/view?{urllib.parse.urlencode(params)}",
                    cookie, as_json=True)
if view.get("code") != 0:
    raise SystemExit(f"view 失败: {view.get('code')}")
vdata = view["data"]
cid = vdata["pages"][0]["cid"]
title = vdata.get("title", "")
owner = vdata.get("owner", {}).get("name", "")
print(f"标题: {title} | 发布者: {owner} | aid={aid} cid={cid}")

# 2) playurl 端点矩阵
audio_url = None
variants = []
p_wbi = ys._wbi_sign({"avid": aid, "cid": cid, "qn": 64, "fnval": 16, "fourk": 0}, cookie)
p_plain = {"avid": aid, "cid": cid, "qn": 64, "fnval": 16, "fourk": 0}
p_bvid = {"bvid": bvid, "cid": cid, "qn": 64, "fnval": 16, "fourk": 0}
p_h5 = dict(p_plain, platform="html5")
variants = [
    ("x/player/wbi/playurl WBI", "https://api.bilibili.com/x/player/wbi/playurl?" + urllib.parse.urlencode(p_wbi)),
    ("x/player/playurl WBI", "https://api.bilibili.com/x/player/playurl?" + urllib.parse.urlencode(p_wbi)),
    ("x/player/playurl 匿名", "https://api.bilibili.com/x/player/playurl?" + urllib.parse.urlencode(p_plain)),
    ("x/player/playurl bvid", "https://api.bilibili.com/x/player/playurl?" + urllib.parse.urlencode(p_bvid)),
    ("x/player/playurl h5", "https://api.bilibili.com/x/player/playurl?" + urllib.parse.urlencode(p_h5)),
    ("x/player/wbi/playurl h5", "https://api.bilibili.com/x/player/wbi/playurl?" + urllib.parse.urlencode(p_h5)),
]
for name, url in variants:
    try:
        d = ys._http_get(url, cookie, as_json=True,
                         extra_headers={"Referer": f"https://www.bilibili.com/video/{bvid}"})
    except Exception as e:
        print(f"[{name}] 请求异常: {e}")
        continue
    if d.get("code") != 0:
        print(f"[{name}] code={d.get('code')} {d.get('message','')}")
        continue
    dash = d.get("data", {}).get("dash", {})
    audios = dash.get("audio", [])
    if audios:
        best = max(audios, key=lambda a: a.get("bandwidth", 0))
        audio_url = best.get("baseUrl") or best.get("base_url")
        print(f"[{name}] OK bandwidth={best.get('bandwidth')}")
        break
    durl = d.get("data", {}).get("durl", [])
    if durl:
        audio_url = durl[0].get("url")
        print(f"[{name}] OK (durl)")
        break

out = os.path.join(WORK, "audio.m4a")
if audio_url:
    print(f"URL: {audio_url[:100]}...")
    req = urllib.request.Request(audio_url, headers={
        "User-Agent": ys.BILI_HEADERS.get("User-Agent", ""),
        "Referer": f"https://www.bilibili.com/video/{bvid}",
    })
    with urllib.request.urlopen(req, timeout=120) as resp, open(out, "wb") as f:
        while True:
            chunk = resp.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)
    print(f"下载完成: {os.path.getsize(out)/1024/1024:.1f} MB")
else:
    print("playurl 全失败，fallback yt_dlp(pip)...")
    import yt_dlp
    out = os.path.join(WORK, "audio2.m4a")
    opts = {
        "format": "ba/0",
        "outtmpl": os.path.join(WORK, "audio2.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "http_headers": {"Referer": "https://www.bilibili.com"},
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"https://www.bilibili.com/video/{bvid}", download=True)
        if info:
            print(f"yt_dlp 下载完成: {info.get('title')}")
    cands = [p for p in os.listdir(WORK) if p.startswith("audio2")]
    if not cands:
        raise SystemExit("yt_dlp 也失败")
    out = os.path.join(WORK, cands[0])

# 3) Whisper
from faster_whisper import WhisperModel
model = WhisperModel("small", device="cpu", compute_type="int8")
print("开始语音识别...")
segments, info = model.transcribe(out, language="zh", beam_size=5, vad_filter=True)
print(f"语言: {info.language} ({info.language_probability:.2%})")
lines = []
for seg in segments:
    t = seg.text.strip()
    if t:
        lines.append(t)
text = "\n".join(lines)
print("=== 识别结果 ===")
print(text)

header = (f"标题：{title}\n发布者：{owner}\n链接：https://www.bilibili.com/video/{bvid}\n"
          f"提取方式：playurl API / yt_dlp(pip) + Whisper ASR (small)\n\n"
          f"────────────────────────────────────────\n\n")
with open(os.path.join(WORK, "subtitle.txt"), "w", encoding="utf-8") as f:
    f.write(header + text)
print(f"\n已保存: {os.path.join(WORK, 'subtitle.txt')}")
