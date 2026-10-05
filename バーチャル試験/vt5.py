# VT5 ソール（UHMWPE）の傷と摩耗：1日1kmコース×30本＝30km
import numpy as np
from scipy.stats import spearmanr
def run(n,seed):
    r=np.random.default_rng(seed)
    W=800*r.uniform(1.0,2.5,n)          # 体重80kg、ターン時の荷重倍率1〜2.5
    A=1.6*0.07*r.uniform(1,2,n)         # 片足〜両足で荷重（m²）
    R=r.uniform(0.3e-3,0.75e-3,n)       # 方解石丸粒の半径
    frac=np.exp(r.uniform(np.log(0.003),np.log(0.3),n))  # 荷重を受ける表面粒の割合
    F=W/(A*frac/(2*R)**2)               # 1粒あたりの荷重 N
    H=r.uniform(38e6,60e6,n)            # UHMWPEの押込み硬さ（ISO 2039-1で約40N/mm²）
    E=r.uniform(0.6e9,1.0e9,n)/(1-0.46**2)
    # 弾性限界荷重（p0=1.1H/… 簡略：平均圧がHを超えると塑性）
    a_el=(3*F*R/(4*E))**(1/3); pm=F/(np.pi*a_el**2)
    plastic=pm>H
    a_pl=np.sqrt(F/(np.pi*H))
    dep=np.where(plastic, a_pl**2/(2*R)*r.uniform(0.5,0.8,n), 0)   # 残留溝の深さ（弾性回復で50〜80%が残る）
    wid=np.where(plastic,2*a_pl,0)
    k=np.exp(r.uniform(np.log(1e-7),np.log(1e-4),n))     # 比摩耗量 mm³/Nm（未測定、最大の不確かさ）
    p=W/A/1e6                                             # 公称面圧 N/mm²
    wear_um=k*p*30000*1e3                                 # 30km/日の一様摩耗 µm/日
    return dict(dep=dep*1e6,wid=wid*1e6,plastic=plastic,wear=wear_um,k=k,frac=frac,F=F,H=H)
print("収束確認：試行回数ごとの傷の深さ（µm）と摩耗（µm/日）のパーセンタイル")
for n in [10**4,10**5,10**6,10**7]:
    d=run(n,1)
    print(f"  N={n:>9,}: 塑性(傷)になる接点 {d['plastic'].mean()*100:5.1f}%  溝深さ 中央{np.median(d['dep'][d['plastic']]):.2f} 95%{np.percentile(d['dep'][d['plastic']],95):.2f} 99.9%{np.percentile(d['dep'][d['plastic']],99.9):.2f}  摩耗 中央{np.median(d['wear']):.3f} 95%{np.percentile(d['wear'],95):.2f}")
d=run(10**7,2)
print("\n感度（溝深さ）:",{k:round(spearmanr(d[k][:300000],d['dep'][:300000])[0],2) for k in ['frac','F','H']})
print("感度（摩耗）:",{k:round(spearmanr(d[k][:300000],d['wear'][:300000])[0],2) for k in ['k','frac']})
# 季節累計と許容
print("\n摩耗の累計（中央 / 95%値）:")
for days,lab in [(1,"1日（30km）"),(10,"個人10日"),(100,"レンタル板100日")]:
    print(f"  {lab:<12}: {np.median(d['wear'])*days:7.1f} / {np.percentile(d['wear'],95)*days:7.1f} µm")
for lim,lab in [(100,"ストーンでの再研磨1回分（約100µm）"),(500,"ソール厚1.2mmのうち使ってよい0.5mm")]:
    for days in [10,100]:
        kmax=lim/(np.median(800*1.75/(1.6*0.07*1.5)/1e6)*30000*1e3*days)
        print(f"  {lab}を{days}日で超えない比摩耗量の上限 k ≦ {kmax:.1e} mm³/Nm")
# エッジ（鋼525HV）と粒：丸い粒の接触圧
print("\nエッジ（焼入れ鋼 硬さ約5.1GPa、塑性開始の接触圧≈2.7GPa）:")
for F in [0.3,1.0,3.0]:
    for nm,Eg,nug in [("方解石",72e9,0.31),("石英",95e9,0.08)]:
        Es=1/((1-nug**2)/Eg+(1-0.3**2)/210e9); p0=(6*F*Es**2/(np.pi**3*(0.5e-3)**2))**(1/3)
        print(f"  荷重{F}N {nm}丸粒: 最大接触圧{p0/1e9:.2f}GPa → {'エッジに傷' if p0>2.7e9 else '弾性（傷なし）'}{'・方解石側が先に砕ける(圧縮強度数百MPa)' if nm=='方解石' and p0>0.5e9 else ''}")
