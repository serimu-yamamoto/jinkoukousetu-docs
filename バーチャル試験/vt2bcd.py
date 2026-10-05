import numpy as np
rng=np.random.default_rng(7); g=9.81; beta=np.radians(30)
print("[VT2-B] 30°斜面・斜面長50m・静止から直滑降（体重80kg, CdA0.4〜0.7, 空気1.16kg/m3）")
m=80; rho=1.16
for mu in [0.02,0.04,0.06,0.08,0.10,0.15,0.20,0.30]:
    a=g*(np.sin(beta)-mu*np.cos(beta))
    out=[]
    for CdA in [0.4,0.7]:
        k=0.5*rho*CdA; vt2=m*a/k; v=np.sqrt(vt2*(1-np.exp(-2*k*50/m))); out.append(v)
    print(f"  μ={mu:.2f}: 初期加速度 {a:.2f}m/s²（μ0.05比 {a/(g*(0.5-0.05*np.cos(beta))):.2f}）  50m後の速度 {out[1]*3.6:.0f}〜{out[0]*3.6:.0f}km/h")
for ang in [12,20,30]:
    b=np.radians(ang); a0=np.sin(b)-0.05*np.cos(b)
    print(f"  斜度{ang}°: 加速度の差を雪(μ0.05)比10%以内に収めるμ上限 = {(np.sin(b)-0.9*a0)/np.cos(b):.3f}")
# エッジ荷重下の挙動：床の粘着力cと支持力
print("  エッジ圧300kPa（幅5mm）に対する支持力q_ult（φ35°）:")
Nc,Nq,Ng=46.1,33.3,48.0
for c in [1,3,10,20,50]:
    q=c*Nc+0.5*16.4*0.005*Ng
    print(f"    c={c:>2}kPa: q_ult={q:6.0f}kPa → {'エッジが沈み粒を跳ね上げる' if q<300 else '沈まない（雪の硬いバーン相当まで）'}")
# 平らな滑走時の掘り起こし抵抗
for E in [3e6,10e6,30e6]:
    for c in [10e3,50e3]:
        q=800/(1.6*0.07); dl=q*0.07*0.9/E; F=0.07*dl*3.84*c
        print(f"    E={E/1e6:>3.0f}MPa c={c/1e3:.0f}kPa: 沈み{dl*1e3:.3f}mm 掘り起こしμ={F/800:.5f}")

print("\n[VT2-C] 夏の晴天日 時間別熱収支（北緯36°・7月、気温22〜31℃、風2m/s、湿った面の反射率0.35）")
lat=np.radians(36); dec=np.radians(21)
def run(aspect_deg, hours_on, pre=1):
    tot=0; Tmax_on=-99; Tdry=[]
    for hr in np.arange(5,21,0.25):
        hra=np.radians(15*(hr-12))
        se=np.sin(lat)*np.sin(dec)+np.cos(lat)*np.cos(dec)*np.cos(hra); e=np.arcsin(max(se,0))
        az=np.arctan2(-np.sin(hra), np.tan(dec)*np.cos(lat)-np.sin(lat)*np.cos(hra))  # 北0,東+ ではなく南基準に変換
        az=np.pi+np.arctan2(np.sin(hra), np.cos(hra)*np.sin(lat)-np.tan(dec)*np.cos(lat))
        asp=np.radians(aspect_deg)
        if e<=0: Sdir=0; Sdif=0
        else:
            Gh=1000*np.sin(e)**1.15
            cosi=np.sin(e)*np.cos(beta)+np.cos(e)*np.sin(beta)*np.cos(az-asp)
            Sdir=0.8*Gh/np.sin(e)*max(cosi,0); Sdif=0.2*Gh*(1+np.cos(beta))/2
        S=Sdir+Sdif
        Ta=26.5+4.5*np.sin(np.pi*(hr-8)/12); RH=np.clip(0.75-0.25*np.sin(np.pi*(hr-8)/12),0.4,0.9)
        h=5.7+3.8*2; sig=5.67e-8
        es=lambda T:0.6108*np.exp(17.27*T/(T+237.3))
        Ld=0.85*sig*(Ta+273.15)**4
        on=any(a-pre<=hr<b for a,b in hours_on)
        def res(T,wet): return S*0.65+Ld-0.95*sig*(T+273.15)**4-h*(T-Ta)-wet*h/1005*2.45e6*0.622/101.3*(es(T)-RH*es(Ta))
        lo,hi=-10,95
        for _ in range(50):
            mid=(lo+hi)/2; lo,hi=(mid,hi) if res(mid,1 if on else 0)>0 else (lo,mid)
        T=(lo+hi)/2
        if on:
            E=h/1005*0.622/101.3*(es(T)-RH*es(Ta)); tot+=E*900*2000/1000/0.7  # 散水効率70%
            if any(a<=hr<b for a,b in hours_on): Tmax_on=max(Tmax_on,T)
        else: Tdry.append(T)
    return Tmax_on,tot,max(Tdry) if Tdry else np.nan
sched={"日中9-17時":[(9,17)],"朝夕7-11時+15-19時":[(7,11),(15,19)],"夕夜17-21時":[(17,21)]}
for asp,lab in [(0,"北向き"),(180,"南向き")]:
    for k,v in sched.items():
        Tm,w,Td=run(asp,v)
        print(f"  {lab} {k:<16}: 営業中の最高表面温度 {Tm:5.1f}℃  散水 {w:5.1f}t/日  非散水時の最高 {Td:5.1f}℃")

print("\n[VT2-D] 年間運用費 モンテカルロ（2,000m²、100営業日、10年8%で設備を年額化 Af=6.710081）")
n=1_000_000; Af=6.710081
water_t=rng.uniform(5,20,n)*100; wprice=rng.uniform(50,400,n)        # t/年, 円/t（雨水・井戸〜上水）
loss_um=np.exp(rng.uniform(np.log(0.1),np.log(10),n))                 # PVA膜の摩耗 µm/日（未測定U3）
pva_kg=loss_um*2000*1.27e-3*rng.uniform(2,4,n)*100                      # 露出粒表面の面積倍率2〜4
pva_price=rng.uniform(261,429,n)
groom_h=rng.uniform(0.5,1.5,n)*110; groom=groom_h*(20*170+rng.uniform(3000,8000,n))
labor=rng.uniform(2,4,n)*110*rng.uniform(2000,3000,n)
power=rng.uniform(1e5,3e5,n)
capex=(rng.uniform(3e6,10e6,n)+rng.uniform(2e6,6e6,n)+rng.uniform(3e6,15e6,n)+rng.uniform(0.5e6,2e6,n))/Af  # 縁散水・噴霧キット・回収池・センサー
items={"水":water_t*wprice,"PVA補充":pva_kg*pva_price,"整地(燃料・整備)":groom,"夜間作業人件費":labor,"電力":power,"設備の年額":capex}
tot=sum(items.values())
for k,v in items.items(): print(f"  {k:<14} 中央{np.median(v)/1e4:7.0f}万円  (5%{np.percentile(v,5)/1e4:5.0f}〜95%{np.percentile(v,95)/1e4:5.0f})  寄与率{np.median(v/tot)*100:4.0f}%")
print(f"  合計           中央{np.median(tot)/1e4:7.0f}万円  (5%{np.percentile(tot,5)/1e4:5.0f}〜95%{np.percentile(tot,95)/1e4:5.0f})  v36の仮置きO=400万円以下の確率 {np.mean(tot<=4e6):.2f}")
print(f"  客1人あたり（100人/日）中央{np.median(tot)/1e4:.0f}円")
from scipy.stats import spearmanr
for k,v in [("膜摩耗µm/日",loss_um),("水単価",wprice),("PVA単価",pva_price),("整地時間",groom_h)]:
    print(f"  Spearman(合計,{k})={spearmanr(v[:200000],tot[:200000])[0]:+.2f}")
