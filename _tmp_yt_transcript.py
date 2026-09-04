import sys, http.cookiejar
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig

vid = "Wercpk28guY"

# load Netscape cookies into requests session
s = requests.Session()
cj = http.cookiejar.MozillaCookieJar(r"F:\Tools\www.youtube.com_cookies.txt")
cj.load(ignore_discard=True, ignore_expires=True)
s.cookies.update(cj)
s.proxies.update({"http": "http://127.0.0.1:2081", "https": "http://127.0.0.1:2081"})

api = YouTubeTranscriptApi(http_client=s)

try:
    tracks = api.list(vid)
except Exception as e:
    print("LIST_ERR:", type(e).__name__, e)
    sys.exit(1)

for tr in tracks:
    print("TRACK:", tr.language_code, tr.language, "generated" if tr.is_generated else "manual")

def pick(tracks):
    for want in ("en", "en-orig", "zh", "zh-Hans", "zh-CN"):
        for tr in tracks:
            if tr.language_code == want:
                return tr
    return tracks[0] if tracks else None

tr = pick(tracks)
if not tr:
    print("NO_TRACK")
    sys.exit(1)

data = tr.fetch()
text = "\n".join(f"{d['start']:.1f}\t{d['text']}" for d in data)
print("===LANG===", tr.language_code, tr.language, "===")
print(text)
