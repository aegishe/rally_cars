import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, re, json, html

url = "https://www.youtube.com/watch?v=Wercpk28guY"
proxies = {'http': 'http://127.0.0.1:2081', 'https': 'http://127.0.0.1:2081'}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}
r = requests.get(url, proxies=proxies, headers=headers, timeout=30)
t = r.text

def grab(pattern):
    m = re.search(pattern, t)
    return m.group(1) if m else None

print("TITLE:", grab(r'"videoPrimaryInfoRenderer":\{"title":\{"runs":\[\{"text":"(.*?)"\}'))
print("CHANNEL:", grab(r'"ownerChannelName":"(.*?)"') or grab(r'"author":"(.*?)"'))
print("CHANNEL_URL:", grab(r'"channelId":"(.*?)"'))
print("DATE_TEXT:", grab(r'"dateText":\{"simpleText":"(.*?)"\}'))
print("VIEWS:", grab(r'"viewCount":\{"videoViewCountRenderer":\{"viewCount":\{"simpleText":"(.*?)"\}'))

m = re.search(r'"attributedDescription":\{"content":"(.*?)","commandRuns"', t)
if m:
    desc = html.unescape(m.group(1))
    desc = re.sub(r'<[^>]+>', '', desc)
    desc = desc.replace('\\n', '\n').replace('\\"', '"').replace('\\u0026', '&')
    print("DESC:\n" + desc[:2500])
else:
    print("DESC: N/A")

# also try to find keywords/category via meta
print("KEYWORDS:", grab(r'"keywords":\[(.*?)\]')[:300])
