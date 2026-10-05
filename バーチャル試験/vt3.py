# VT3 日中9-17営業：表層含水率と表面温度の動的計算（散水方式の比較）
import numpy as np
lat=np.radians(36); dec=np.radians(21); beta=np.radians(30); sig=5.67e-8
es=lambda T:0.6108*np.exp(17.27*T/(T+237.3))
dz=0.005; por=0.382; C=(1674*840)*dz            # 表層5mm（滑走で触れる層）の熱容量 J/m2K（乾燥）
k_below=0.8/0.05                                 # 下層5cmへの伝導 W/m2K（湿り砂0.8W/mK）
def forcing(hr,asp):
    hra=np.radians(15*(hr-12))
    se=np.sin(lat)*np.sin(dec)+np.cos(lat)*np.cos(dec)*np.cos(hra); e=np.arcsin(max(se,0))
    az=np.pi+np.arctan2(np.sin(hra),np.cos(hra)*np.sin(lat)-np.tan(dec)*np.cos(lat))
    if e<=0: S=0
    else:
        Gh=1000*np.sin(e)**1.15; ci=np.sin(e)*np.cos(beta)+np.cos(e)*np.sin(beta)*np.cos(az-np.radians(asp))
        S=0.8*Gh/np.sin(e)*max(ci,0)+0.2*Gh*(1+np.cos(beta))/2
    Ta=26.5+4.5*np.sin(np.pi*(hr-8)/12); RH=np.clip(0.75-0.25*np.sin(np.pi*(hr-8)/12),0.4,0.9)
    return S,Ta,RH
def sim(asp,mode,pulse_mm=0.0,interval_min=0):
    dt=10.; T=25.; Tb=25.; th=0.0; water=0; Ts=[];ths=[]
    t=6*3600.; nextp=8.5*3600
    while t<17*3600:
        hr=t/3600; S,Ta,RH=forcing(hr,asp); h=5.7+3.8*2
        if mode=="常時湿潤": th=0.30
        if mode=="間欠ミスト" and t>=nextp:
            th=min(th+pulse_mm*1e-3/dz,por); water+=pulse_mm; nextp+=interval_min*60
        if mode=="制御ミスト" and t>=nextp:
            add=max(pulse_mm/100-th,0)*dz*1000; th+=add/1000/dz; water+=add; nextp+=interval_min*60
        if th>0.06 and mode!="常時湿潤": th=0.06+(th-0.06)*np.exp(-dt/600)  # 圃場容水量6%超は約10分で排水
        # 蒸発：第1段階（表層に水がある間は需要どおり、含水2%未満で急減）
        dem=max(h/1005*0.622/101.3*(es(T)-RH*es(Ta)),0)
        f=np.clip((th-0.005)/0.02,0,1); E=dem*f
        alb=0.35 if th>0.02 else 0.55
        Q=S*(1-alb)+0.85*sig*(Ta+273.15)**4-0.95*sig*(T+273.15)**4-h*(T-Ta)-E*2.45e6-k_below*(T-Tb)
        Ceff=C+th*dz*4.18e6
        T+=Q*dt/Ceff; Tb+=k_below*(T-Tb)*dt/(1674*840*0.05)
        if mode!="常時湿潤": th=max(th-E*dt/1000/dz,0)
        else: water+=E*dt
        if hr>=9: Ts.append(T); ths.append(th)
        t+=dt
    Ts=np.array(Ts); ths=np.array(ths)
    w=water/1000*2000 if mode!="常時湿潤" else water/1000*2000  # t/日（mm=kg/m2）
    if mode=="常時湿潤": w=water*2000/1000/0.7
    else: w=water*2000/1000/0.7
    return Ts.max(),np.percentile(Ts,50),ths.max()*100,np.mean(ths>0.08)*100,w
print("方式, 斜面向き → 営業中の表面温度 最高/中央, 表層の体積含水率 最大(%), 含水8%超の時間割合(%), 散水量 t/日")
for asp,lab in [(0,"北向き"),(180,"南向き")]:
    for mode,p,iv in [("常時湿潤",0,0),("制御ミスト",3,2),("制御ミスト",3,5),("制御ミスト",5,5),("制御ミスト",3,15),("散水なし",0,0)]:
        a,b,c,d,w=sim(asp,mode,p,iv)
        tag=mode+(f" 目標{p}%/{iv}分毎" if iv else "")
        print(f"  {lab} {tag:<20}: {a:5.1f}/{b:5.1f}℃  含水最大{c:5.1f}%  8%超{d:5.1f}%  {w:5.1f}t")
