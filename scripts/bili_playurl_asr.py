# -*- coding: utf-8 -*-
"""B站匿名 playurl 直取 DASH 音频 + faster-whisper 转写。
绕开 yt-dlp 的 412 风控（yt_subs 技能文档描述但脚本未实现的路径）。
用法: python bili_playurl_asr.py <BV号> <输出目录>
复用 yt_subs.py 的 wbi 签名与 http 辅助函数。
"""
import sys
import os
import urllib.parse

BASE = r"C:\Users\AegisH\.agents\skills\yt-subs"
sys.path.insert(0, BASE)
import yt_subs as ys  # noqa: E402


def load_netscape_cookie_str(path: str) -> str:
    """读 Netscape cookies.txt，拼成 'k=v; k=v' 串（仅 bilibili 域）"""
    if not os.path.exists(path):
        raise RuntimeError(f"cookie 文件不存在: {path}")
    pairs = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 7:
                continue
            domain, _, _, _, _, name, value = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6]
            if "bilibili.com" in domain:
                pairs.append(f"{name}={value}")
    if not pairs:
        raise RuntimeError(f"cookie 文件中无 bilibili 域条目: {path}")
    return "; ".join(pairs)


def get_audio_url(bvid: str, cookie_str: str = ""):
    aid = ys.bv2av(bvid)
    p = ys._wbi_sign({"bvid": bvid}, cookie_str)
    qs = urllib.parse.urlencode(p)
    d = ys._http_get(f"https://api.bilibili.com/x/web-interface/wbi/view?{qs}",
                     cookie_str, as_json=True)
    if d.get("code") != 0:
        raise RuntimeError(f"view code={d.get('code')} {d.get('message')}")
    vd = d["data"]
    cid = vd["pages"][0]["cid"]
    title = vd.get("title", "")
    owner = vd.get("owner", {}).get("name", "")
    p2 = ys._wbi_sign({"avid": aid, "cid": cid, "qn": 64, "fnval": 16, "fourk": 0}, cookie_str)
    qs2 = urllib.parse.urlencode(p2)
    d2 = ys._http_get(
        f"https://api.bilibili.com/x/player/wbi/playurl?{qs2}", cookie_str, as_json=True,
        extra_headers={"Referer": f"https://www.bilibili.com/video/{bvid}"},
    )
    if d2.get("code") != 0:
        raise RuntimeError(f"playurl code={d2.get('code')} {d2.get('message')}")
    audios = d2["data"]["dash"]["audio"]
    audios.sort(key=lambda a: a.get("bandwidth", 0), reverse=True)
    best = audios[0]
    url = best.get("baseUrl") or (best.get("backupUrl") or [""])[0]
    return url, title, owner


def download(url: str, out_path: str, bvid: str, cookie_str: str = ""):
    headers = dict(ys.BILI_HEADERS)
    headers["Referer"] = f"https://www.bilibili.com/video/{bvid}"
    if cookie_str:
        headers["Cookie"] = cookie_str
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=90) as r, open(out_path, "wb") as f:
        while True:
            chunk = r.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)


def transcribe(audio: str, out_txt: str, title: str, owner: str, bvid: str) -> str:
    from faster_whisper import WhisperModel
    model = WhisperModel("small", device="cpu", compute_type="int8")
    print("[ASR] 加载模型完成，开始转写...")
    segments, info = model.transcribe(audio, language="zh", beam_size=5, vad_filter=True)
    lines = []
    for seg in segments:
        lines.append(seg.text.strip())
    text = "\n".join(x for x in lines if x)
    head = (
        f"标题：{title}\n发布者：{owner}\n"
        f"链接：https://www.bilibili.com/video/{bvid}\n"
        f"提取方式：Whisper ASR (small, playurl直取)\n\n{'-' * 56}\n\n"
    )
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(head + text)
    return text


if __name__ == "__main__":
    bvid = sys.argv[1]
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    cookie_file = os.environ.get("BILI_COOKIE_FILE", r"F:\Tools\www.bilibili.com_cookies.txt")
    cookie_str = ""
    try:
        cookie_str = load_netscape_cookie_str(cookie_file)
        print(f"[cookie] 已加载 {cookie_file}（登录态）")
    except Exception as e:
        print(f"[cookie] {e} —— 继续匿名尝试")
    try:
        url, title, owner = get_audio_url(bvid, cookie_str)
        print("标题:", title, "| 发布者:", owner)
        print("音频流已获取")
        audio = os.path.join(out_dir, f"{bvid}.m4a")
        download(url, audio, bvid, cookie_str)
        print(f"音频已下载: {os.path.getsize(audio) / 1024 / 1024:.1f} MB")
        out_txt = os.path.join(out_dir, f"{bvid}.txt")
        text = transcribe(audio, out_txt, title, owner, bvid)
        print(f"[OK] 转写完成 {len(text)} 字符 -> {out_txt}")
        print(text[:1500])
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
