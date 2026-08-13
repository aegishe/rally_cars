import json, numpy as np
from sklearn.linear_model import LinearRegression
from scipy import stats

d = json.load(open('pikes-peak/charts/regression_results.json', encoding='utf-8'))
cars = [c for c in d['cars'] if c['mod_level'] == '原厂']
N = len(cars)

hp = np.array([c['hp'] for c in cars])
kg = np.array([c['weight'] for c in cars])
lap = np.array([c['lap_s'] for c in cars])
is_ev = np.array([1 if c['powertrain']=='EV' else 0 for c in cars])
is_suv = np.array([1 if c['body']=='SUV' else 0 for c in cars])
is_sedan = np.array([1 if c['body']=='Sedan' else 0 for c in cars])

y = np.log(lap)
X = np.column_stack([np.log(hp), np.log(kg), is_ev, is_suv, is_sedan])
m = LinearRegression().fit(X, y)
r2 = m.score(X, y)
r2_adj = 1 - (1-r2)*(N-1)/(N-5-1)
yp = m.predict(X)
res = (y - yp)*100

mse = np.sum((y-yp)**2)/(N-5-1)
XtX_inv = np.linalg.inv(X.T @ X)
se = np.sqrt(np.maximum(mse*np.diag(XtX_inv), 1e-10))
t_vals = [m.coef_[i]/max(se[i],1e-10) for i in range(5)]
p_vals = [2*stats.t.sf(abs(t), N-5-1) for t in t_vals]

labels = ['ln(hp)','ln(kg)','EV','SUV','Sedan']
for i, lb in enumerate(labels):
    sig = '***' if p_vals[i]<0.001 else '**' if p_vals[i]<0.01 else '*' if p_vals[i]<0.05 else '.' if p_vals[i]<0.1 else 'ns'
    print(f'{lb:8s} {m.coef_[i]:+.4f}  p={p_vals[i]:.4f} {sig:>4}')

wpr = abs(m.coef_[1]/m.coef_[0]) if abs(m.coef_[0])>1e-6 else 999
pw_k_m = LinearRegression().fit(np.log(hp/kg).reshape(-1,1), y)
k = -pw_k_m.coef_[0]
k_r2 = pw_k_m.score(np.log(hp/kg).reshape(-1,1), y)

print(f'\n原厂组 N={N}, R2={r2:.4f}, R2_adj={r2_adj:.4f}')
print(f'重量惩罚比 = {wpr:.2f}, 功重比弹性 k = {k:.4f} (R2={k_r2:.4f})')
print(f'\n--- 对比全量 ---')
old_reg = d['regression']
print(f'全量组 N=13, WPR={old_reg["weight_penalty_ratio"]:.2f}, k={old_reg["pw_elasticity_k"]:.4f}')
print()

print('残差排序:')
sorted_idx = np.argsort(res)
for idx in sorted_idx:
    print(f'  {cars[idx]["name"]:<30} {res[idx]:+.1f}%  {cars[idx]["powertrain"]} {cars[idx]["body"]}')

print(f'\n纯电 (N={np.sum(is_ev)}): avg残差={np.mean(res[is_ev==1]):+.1f}%')
for i in range(N):
    if is_ev[i]:
        print(f'  {cars[i]["name"]:<30} {res[i]:+.1f}%')

print(f'纯油 (N={np.sum(is_ev==0)}): avg残差={np.mean(res[is_ev==0]):+.1f}%')
for i in range(N):
    if not is_ev[i]:
        print(f'  {cars[i]["name"]:<30} {res[i]:+.1f}%')
