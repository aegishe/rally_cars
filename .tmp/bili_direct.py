# -*- coding: utf-8 -*-
"""绕过 yt-dlp.exe（PyInstaller 解压在沙箱下失败），直接走 B站匿名 playurl API 下载 DASH 音频 + faster-whisper 转写"""
import sys, os, json, urllib.request, urllib.parse

sys.path.insert(0, r"C:\Users\AegisH\.agents\skills\yt-subs")
import yt_subs as ys  # noqa: E402

BVID = "BV1BUtA65ETM"
WORK = r"D:\Project\dsh_rally_cars\.tmp"
cookie = ys.random_cookies()

# 1) view API -> aid/cid/title/owner
bvid, aid = ys._parse_bv_av(BVID)
params = ys._wbi_sign({"bvid": bvid}, cookie)
qs = urllib.parse.urlencode(params)
view = ys._http_get(f"https://api.bilibili.com/x/web-interface/wbi/view?{qs}", cookie, as_json=True)
if view.get("code") != 0:
    raise SystemExit(f"view 失败: {view.get('code')} {view.get('message','')}")
vdata = view["data"]
cid = vdata["pages"][0]["cid"]
title = vdata.get("title", "")
owner = vdata.get("owner", {}).get("name", "")
print(f"标题: {title}")
print(f"发布者: {owner}")
print(f"aid={aid} cid={cid}")

# 2) playurl DASH 音频（先 WBI 签名，失败再退匿名）
def get_playurl(use_wbi: bool):
    if use_wbi:
        p = ys._wbi_sign({"avid": aid, "cid": cid, "qn": 64, "fnval": 16, "fourk": 0}, cookie)
    else:
        p = {"avid": aid, "cid": cid, "qn": 64, "fnval": 16, "fourk": 0}
    url = f"https://api.bilibili.com/x/player/playurl?{urllib.parse.urlencode(p)}"
    return ys._http_get(url, cookie, as_json=True,
                        extra_headers={"Referer": f"https://www.bilibili.com/video/{bvid}"})

data = get_playurl(True)
if data.get("code") != 0:
    print(f"playurl(WBI) code={data.get('code')} {data.get('message','')}，退匿名...")
    data = get_playurl(False)
if data.get("code") != 0:
    raise SystemExit(f"playurl 失败: {data.get('code')} {data.get('message','')}")
dash = data["data"].get("dash", {})
audios = dash.get("audio", [])
if not audios:
    raise SystemExit("无 DASH 音频流")
best = max(audios, key=lambda a: a.get("bandwidth", 0))
base_url = best.get("baseUrl") or best.get("base_url")
print(f"音频: bandwidth={best.get('bandwidth')} 时长={dash.get('duration')}s")
print(f"URL: {base_url[:100]}...")

# 3) 下载
os.makedirs(WORK, exist_ok=True)
out = os.path.join(WORK, "audio.m4a")
req = urllib.request.Request(base_url, headers={
    "User-Agent": ys.BILI_HEADERS.get("User-Agent", ""),
    "Referer": f"https://www.bilibili.com/video/{bvid}",
})
with urllib.request.urlopen(req, timeout=120) as resp, open(out, "wb") as f:
    while True:
        chunk = resp.read(1 << 16)
        if not chunk:
            break
        f.write(chunk)
size = os.path.getsize(out)
print(f"下载完成: {out} ({size/1024/1024:.1f} MB)")

# 4) Whisper 转写
from faster_whisper import WhisperModel  # noqa: E402
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

# 5) 保存（带元信息头）
header = (f"标题：{title}\n发布者：{owner}\n链接：https://www.bilibili.com/video/{bvid}\n"
          f"提取方式：匿名 playurl + Whisper ASR (small)\n\n"
          f"────────────────────────────────────────\n\n")
with open(os.path.join(WORK, "subtitle.txt"), "w", encoding="utf-8") as f:
    f.write(header + text)
print(f"\n已保存: {os.path.join(WORK, 'subtitle.txt')}")
