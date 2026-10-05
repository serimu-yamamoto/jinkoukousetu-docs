# VT6 「サラサラなのに圧雪で締まる」結合機構の比較
import numpy as np
rng=np.random.default_rng(6); n=2_000_000
por=0.382; kap=6
def rumpf(F,d): return (1-por)/por*kap*F/(np.pi*d**2)   # 粒間の結合力→引張強さ（Rumpf）
print("[1] 水だけ（毛管力）の粘着力 c≈σt")
for d in [0.2e-3,0.5e-3,1.0e-3]:
    F=2*np.pi*(d/2)*0.072*0.8
    print(f"  粒径{d*1e3:.1f}mm: {rumpf(F,d)/1e3:.2f}kPa（目標10〜100kPaに届かない）")
print("\n[2] PVA接点：細霧で再び水を吸って軟らかくなるまでの時間（膜5µm、拡散係数1e-13〜1e-11m²/s）")
for D in [1e-13,1e-12,1e-11]:
    print(f"  D={D:.0e}: {(5e-6)**2/D:.0f}秒")
print("  → 細霧（2〜5分ごと）の下では、PVAの結合は数秒〜数分で水を吸って軟化する。現地で結合し直せる性質（水で可塑化する）と、水に強い性質は同じ仕組みの表裏で、PVAでは両立できない")

print("\n[3] 石灰水焼結：夜の整地時に石灰水を噴霧→空気中のCO2で炭酸カルシウム(方解石)の橋が接点にできる")
R=rng.uniform(0.3e-3,0.75e-3,n); d=2*R
w=np.exp(rng.uniform(np.log(0.0002),np.log(0.01),n))   # 析出するCaCO3の質量割合（対粒）
eta=rng.uniform(0.1,0.5,n)                               # 析出のうち接点の橋になる割合
sc=np.exp(rng.uniform(np.log(1e6),np.log(10e6),n))       # 析出方解石の引張強さ 1〜10MPa（未測定）
mg=4/3*np.pi*R**3*2710
Vb=w*mg/2710/(kap/2)*eta
rb=(Vb*2*R/np.pi)**0.25
F=sc*np.pi*rb**2
c=rumpf(F,d)/1e3
ok=(c>=10)&(c<=100)
for lo,hi in [(0.0002,0.0005),(0.0005,0.001),(0.001,0.002),(0.002,0.005),(0.005,0.01)]:
    s=(w>=lo)&(w<hi)
    print(f"  CaCO3 {lo*100:.2f}〜{hi*100:.2f}%: c 中央{np.median(c[s]):6.0f}kPa（5%{np.percentile(c[s],5):5.0f}〜95%{np.percentile(c[s],95):6.0f}）  目標帯に入る確率 {ok[s].mean():.2f}")
from scipy.stats import spearmanr
print("  感度:",{k:round(spearmanr(v[:300000],c[:300000])[0],2) for k,v in [('析出量w',w),('橋の割合η',eta),('引張強さ',sc),('粒径',R)]})
# 毎晩の必要量：表層5mmを再結合
for wv in [0.0005,0.001,0.002]:
    caco3=2000*0.005*1674*wv; caoh=caco3*74.09/100.09; co2=caco3*44.01/100.09
    lw=caoh/1.6  # m3（飽和石灰水1.6g/L）
    print(f"  w={wv*100:.2f}%: 毎晩CaCO3 {caco3:5.1f}kg ← 消石灰{caoh:5.1f}kg（石灰水なら{lw:5.1f}m³）・CO2 {co2:4.1f}kg")
print("\n[4] 夜のうちに炭酸化が終わるか（空気からのCO2供給、表層5mm）")
need=2000*0.005*1674*0.001*44.01/100.09*1000/2000      # g/m2（w=0.1%）
Ca=0.75                                                 # 空気中CO2 g/m3
for hm in [0.003,0.01]:
    for Deff in [1e-6,3e-6]:
        flux=1/(1/(hm*Ca)+0.0025/(Deff*Ca))             # 大気側＋床内拡散の直列
        print(f"  物質移動係数{hm} m/s・床内拡散{Deff:.0e}: 供給{flux*3600:.2f}g/m²/h → 必要{need:.2f}g/m² は {need/flux/3600:.1f}時間で完了")
print("\n[5] 雪への影響と水への強さ")
print("  消石灰の飽和溶液の凝固点降下 ≈ %.3fK（塩類と違い、雪はほぼ溶かさない）" % (1.86*1.6/74.09*3))
print("  方解石の橋が水に溶ける量：細霧15t/日×最大約50mg/L ≈ 0.75kg/日 ≪ 毎晩の析出17kg → 細霧では弱まらない")
print("  シーズン累計の析出 %.1ft ＝ 床の %.2f%%（目詰まりの心配は小さい。砕けた橋は微粉として回収池へ）" % (17*100/1000, 17*100/1506600*100))
print("  費用：消石灰12kg/晩×100日×30〜60円/kg ≈ %.0f〜%.0f万円/シーズン" % (12*100*30/1e4, 12*100*60/1e4))
