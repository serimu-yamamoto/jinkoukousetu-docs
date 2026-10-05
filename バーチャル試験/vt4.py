# VT4 乾燥運用（散水なし）の状態シミュレーション
import numpy as np
rng=np.random.default_rng(4)
lat=np.radians(36); dec=np.radians(21); beta=np.radians(30); sig=5.67e-8
es=lambda T:0.6108*np.exp(17.27*T/(T+237.3))
def forcing(hr,asp):
    hra=np.radians(15*(hr-12)); se=np.sin(lat)*np.sin(dec)+np.cos(lat)*np.cos(dec)*np.cos(hra); e=np.arcsin(max(se,0))
    az=np.pi+np.arctan2(np.sin(hra),np.cos(hra)*np.sin(lat)-np.tan(dec)*np.cos(lat))
    S=0 if e<=0 else (lambda Gh,ci:0.8*Gh/np.sin(e)*max(ci,0)+0.2*Gh*(1+np.cos(beta))/2)(1000*np.sin(e)**1.15,np.sin(e)*np.cos(beta)+np.cos(e)*np.sin(beta)*np.cos(az-np.radians(asp)))
    Ta=26.5+4.5*np.sin(np.pi*(hr-8)/12); RH=np.clip(0.75-0.25*np.sin(np.pi*(hr-8)/12),0.4,0.9)
    return S,Ta,RH
# (a) 0.45m乾燥床の1次元熱伝導、晴天3日連続（3日目を報告）
print("[a] 乾燥床の温度（晴天3日目、反射率0.55、熱伝導0.3W/mK、熱容量1.4MJ/m3K）")
k=0.3; Cv=1674*840; nz=91; dz=0.45/(nz-1); al=k/Cv; dt=0.4*dz**2/al
for asp,lab in [(0,"北向き"),(180,"南向き")]:
    T=np.full(nz,25.); rec={}
    t=0.
    while t<3*86400:
        hr=(t/3600)%24; S,Ta,RH=forcing(hr,asp); h=5.7+3.8*2
        q=S*0.45+0.85*sig*(Ta+273.15)**4-0.95*sig*(T[0]+273.15)**4-h*(T[0]-Ta)
        Tn=T.copy(); Tn[1:-1]=T[1:-1]+al*dt/dz**2*(T[2:]-2*T[1:-1]+T[:-2])
        Tn[0]=T[0]+dt*(q+k*(T[1]-T[0])/dz)/(Cv*dz/2); Tn[-1]=T[-2]; T=Tn
        if t>=2*86400:
            for d in [0,5,20,100]:
                i=int(round(d/1000/dz)); rec.setdefault(d,[]).append((hr,T[i]))
        t+=dt
    s=f"  {lab}:"
    for d,v in rec.items():
        v=np.array(v); m=(v[:,0]>=9)&(v[:,0]<17)
        s+=f" 深さ{d}mm 営業中{v[m,1].min():.0f}〜{v[m,1].max():.0f}℃ /"
    print(s)
    S,Ta,RH=forcing(14,asp); Ts=rec[0][int(len(rec[0])*14/24)][1]
    print(f"    14時の表面近くの相対湿度 ≈ {RH*es(Ta)/es(Ts)*100:.0f}%（気温{Ta:.0f}℃・湿度{RH*100:.0f}%の空気が表面温度{Ts:.0f}℃に触れたとき）")
# (c) 乾いた摩擦：UHMWPEソール×PVA膜付き方解石丸粒（Hertz接触＋Briscoe-Tabor界面せん断 τ=τ0+αp）
print("\n[c] 乾いた摩擦 モンテカルロ100万回")
n=1_000_000; W=800.; A=2*1.6*0.07
R=rng.uniform(0.3e-3,0.75e-3,n)                       # 粒の半径
frac=np.exp(rng.uniform(np.log(0.003),np.log(0.3),n))  # 荷重を受ける表面粒の割合（粒高さのばらつき）
F=W/(A*frac/(2*R)**2)                                  # 1粒あたりの荷重
Es=rng.uniform(0.6e9,1.0e9,n)/(1-0.46**2)              # UHMWPE（方解石は剛体扱い）
a=(3*F*R/(4*Es))**(1/3); p=F/(np.pi*a**2)
tau0=np.exp(rng.uniform(np.log(0.5e6),np.log(5e6),n)); alpha=rng.uniform(0.05,0.12,n)  # 乾いた高分子界面（未測定）
yield_=rng.uniform(20e6,28e6,n); plast=p>yield_
mu_adh=(tau0+alpha*p)/p
# 掘り起こし（粒が塑性で食い込む場合のみ）
mu_pl=np.where(plast,0.1*np.sqrt(np.clip(a/R,0,1)),0)
mu=mu_adh+mu_pl
print(f"  μ 中央{np.median(mu):.3f}  5%{np.percentile(mu,5):.3f}〜95%{np.percentile(mu,95):.3f}   P(μ≦0.10)={np.mean(mu<=0.10):.2f}  ソールが塑性変形(傷)する割合={np.mean(plast):.2f}")
from scipy.stats import spearmanr
for nm,v in [("τ0",tau0),("α",alpha),("荷重粒割合",frac),("粒径",R)]:
    print(f"   Spearman(μ,{nm})={spearmanr(v[:200000],mu[:200000])[0]:+.2f}")
# (d) 摩擦の瞬間温度上昇（Archard、高ペクレ数、熱の大半は方解石側へ）
v=10.; kpe=0.4; kca=3.0; kap=1.7e-7
qf=mu*p*v; Pe=v*a/(2*kap)
dT=1.6*qf*a/(kpe*np.sqrt(np.pi*Pe))*kpe/(kpe+kca)
print(f"\n[d] 10m/sの接点の瞬間温度上昇 中央{np.median(dT):.1f}K 95%{np.percentile(dT,95):.1f}K（表面45℃に上乗せ。UHMWPEの軟化はおよそ80℃以上）")
# (e) 風による粒の飛散（Bagnold）
print("\n[e] 風で飛ぶ条件")
for d in [0.6e-3,1.0e-3,1.5e-3]:
    ut=0.1*np.sqrt((2710-1.2)/1.2*9.81*d); z0=d/30; U10=ut*np.log(10/z0)/0.4
    print(f"  非結合の粒 d={d*1e3:.1f}mm: 臨界摩擦速度{ut:.2f}m/s → 高さ10mの風速{U10:.0f}m/s以上で移動開始（斜面の地形で風が強まれば、それより低い風速で）")
print("  方解石の微粉（10µm）：u*t≈0.2m/s（Shaoの式ではより高い）→ 舞い上がりは粒の跳躍が引き金になる")
