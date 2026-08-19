"""SU7 Ultra 原型车 vs 极限组对比"""
import numpy as np
from sklearn.linear_model import LinearRegression

proto = [
    (1160, 849, 319.5, '919 Hybrid Evo'),
    (680, 1100, 365.3, 'VW ID.R'),
    (800, 1350, 376.0, 'Ford GT Mk IV'),
    (2000, 1700, 384.0, 'Lotus Evija X'),
]
su7p = (1548, 1900, 406.9, 'SU7 Ultra 原型')

X = np.column_stack([np.log([d[0] for d in proto]), np.log([d[1] for d in proto])])
y = np.log([d[2] for d in proto])
m = LinearRegression().fit(X, y)
print(f"极限组回归 (N=4): beta_hp={m.coef_[0]:.4f}, beta_kg={m.coef_[1]:.4f}, R2={m.score(X,y):.4f}")

rows = proto + [su7p]
print(f"\n{'车':<18}{'hp':>6}{'kg':>6}{'hp/t':>7}{'圈速':>9}{'极限组预测':>10}{'残差':>8}")
for hp, kg, lap, name in rows:
    pred = float(np.exp(m.predict([[np.log(hp), np.log(kg)]])[0]))
    resid = (np.log(lap) - m.predict([[np.log(hp), np.log(kg)]])[0]) * 100
    print(f"{name:<18}{hp:>6}{kg:>6}{hp/kg*1000:>7.0f}{lap:>8.1f}s{pred:>9.0f}s{resid:>+7.1f}%")

print("\n圈速效率:")
for hp, kg, lap, name in rows:
    print(f"  {name:<18} 每吨圈速 {lap/(kg/1000):.1f} s/t   每hp圈速 {lap/hp:.3f} s/hp")

# Evija X 对照细拆
print("\nEvija X vs SU7 原型 (同为电动极限车):")
print(f"  Evija X: 2000hp/1700kg/384.0s -> 功重比 +29%, 轻 200kg, 快 {406.9-384.0:.1f}s")
print(f"  按极限组弹性: 马力差 {np.log(2000/1548)*100:.1f}% x {abs(m.coef_[0]):.4f} = {abs(m.coef_[0])*np.log(2000/1548)*100:.2f}% 圈速收益")
print(f"               重量差 {np.log(1900/1700)*100:.1f}% x {m.coef_[1]:.4f} = {m.coef_[1]*np.log(1900/1700)*100:.2f}% 圈速惩罚")
print(f"  弹性解释 {(abs(m.coef_[0])*np.log(2000/1548) - m.coef_[1]*np.log(1900/1700))*100:.2f}% vs 实际圈速差 {(406.9-384.0)/384.0*100:.1f}%")
