import json, re

with open('pikes-peak/charts/pikes_peak_analysis.html', 'r', encoding='utf-8') as f:
    html = f.read()

# extract chart1 trace names
chart1 = html.split("Plotly.newPlot('chart1'")[1].split("Plotly.newPlot('chart2'")[0]
names = re.findall(r'"name":"([^"]+)"', chart1)
print("chart1 traces:", names)

# check which trace contains Rivian
blocks = chart1.split('"type":"scatter"')
for i, block in enumerate(blocks):
    if 'Rivian' in block:
        print(f"Rivian is in trace #{i}: {names[i] if i < len(names) else 'unknown'}")

# verify all body types present
for bt in ['超跑', '四门', 'SUV', '皮卡']:
    count = html.count(f'"name":"{bt}"')
    print(f"{bt}: {count} trace(s)")
