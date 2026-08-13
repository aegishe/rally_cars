import json, numpy as np

d = json.load(open('pikes-peak/charts/regression_results.json', encoding='utf-8'))
cars = d['cars']
protos = d['protos']
truck = d.get('truck_ref', [])

all_cars = cars + protos + truck

# Constants
g = 9.81          # m/s2
sin_theta = 0.072 # 7.2% grade
track_m = 19990   # meters
hp_per_watt = 1/745.7

print(f"{'车型':<30} {'账面hp':>6} {'重量kg':>7} {'圈速s':>7} {'均速km/h':>8} {'爬坡hp':>7} {'净hp':>6} {'账面PW':>7} {'净PW':>7} {'净/账':>6}")
print("-" * 95)

for c in all_cars:
    hp_book = c['hp']
    kg = c['weight']
    lap_s = c['lap_s']
    name = c['name']

    # Average speed
    v_avg = track_m / lap_s  # m/s
    v_kmh = v_avg * 3.6

    # Climb power at average speed
    p_climb = kg * g * sin_theta * v_avg * hp_per_watt

    # Net power (book - climb). Note: this doesn't account for altitude attenuation
    hp_net = max(hp_book - p_climb, 10)  # floor at 10hp

    pw_book = hp_book / kg
    pw_net = hp_net / kg
    ratio = pw_net / pw_book

    print(f"{name:<30} {hp_book:>6.0f} {kg:>7.0f} {lap_s:>7.1f} {v_kmh:>8.1f} {p_climb:>7.0f} {hp_net:>6.0f} {pw_book:>7.3f} {pw_net:>7.3f} {ratio:>6.1%}")

# T-test: book PW vs net PW correlation with lap time
print(f"\n--- 回归对比 ---")
from sklearn.linear_model import LinearRegression

hp_all = np.array([c['hp'] for c in cars])
kg_all = np.array([c['weight'] for c in cars])
lap_all = np.array([c['lap_s'] for c in cars])

# compute net hp for each
v_all = track_m / lap_all
p_climb_all = kg_all * g * sin_theta * v_all * hp_per_watt
hp_net_all = np.clip(hp_all - p_climb_all, 10, None)

pw_book_all = hp_all / kg_all
pw_net_all = hp_net_all / kg_all

m_book = LinearRegression().fit(np.log(pw_book_all).reshape(-1,1), np.log(lap_all))
m_net = LinearRegression().fit(np.log(pw_net_all).reshape(-1,1), np.log(lap_all))

k_book = -m_book.coef_[0]; r2_book = m_book.score(np.log(pw_book_all).reshape(-1,1), np.log(lap_all))
k_net = -m_net.coef_[0]; r2_net = m_net.score(np.log(pw_net_all).reshape(-1,1), np.log(lap_all))

print(f"账面功重比弹性 k_book = {k_book:.4f}, R2 = {r2_book:.4f}")
print(f"净功重比弹性   k_net  = {k_net:.4f}, R2 = {r2_net:.4f}")
print(f"净功重比改善 = {(k_net/k_book - 1)*100:+.1f}% 弹性, R2变化 = {r2_net - r2_book:+.4f}")

# Key examples
print(f"\n--- 关键对比 ---")
for a, b in [("Tesla Model 3 Performance", "Bentley Bentayga W12"),
             ("Hyundai Ioniq 5 N", "Lamborghini Urus Perf"),
             ("Porsche 911 Turbo S", "Hyundai Ioniq 5 N")]:
    ca = next(c for c in cars if c['name'] == a)
    cb = next(c for c in cars if c['name'] == b)
    print(f"\n{a} vs {b}:")
    for label, c in [(a, ca), (b, cb)]:
        v = track_m / c['lap_s']
        pc = c['weight'] * g * sin_theta * v * hp_per_watt
        net = max(c['hp'] - pc, 10)
        print(f"  {label:<30}: 账面 {c['hp']}hp → 爬坡 -{pc:.0f}hp = 净 {net:.0f}hp, PW {c['hp']/c['weight']:.3f}→{net/c['weight']:.3f}")
