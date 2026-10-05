# VT9 滑走集中ゾーン（全体の60〜70%が通る）の削れ：1kmコース・14h・1万本
import numpy as np
from multiprocessing import Pool
W,Lg=40.,50.
def day(args):
    seed,zw,zf,sev,cell,init=args
    r=np.random.default_rng(seed)
    nx,ny=int(W/cell),int(Lg/cell)
    base=np.zeros((ny,nx)) if init is None else init.copy()   # 下地の削れ（累計mm）
    loose=np.zeros((ny,nx)); zc=W/2
    turn_y=np.arange(3,Lg,r.uniform(7,10))                       # 地形で決まるターン位置
    dbmax,pmax=(1.5,0.8) if sev=="通常" else (3.0,0.95)
    hourly=[]
    for k in range(10000):
        inz=r.random()<zf
        if inz:
            x=zc+r.uniform(-zw/2,zw/2)*0.6; amp=r.uniform(0.3,1.0)*zw/2
        else:
            x=r.uniform(2,W-2); amp=r.uniform(1,6)
        pskid=r.uniform(0.3,pmax)
        side=1 if r.random()<0.5 else -1
        for i_t,ty in enumerate(turn_y if inz else np.arange(r.uniform(0,7),Lg,r.uniform(6,14)/2)):
            y=ty+(r.normal(0,0.7) if inz else 0)
            if y<0 or y>=Lg: continue
            xc=np.clip(x+side*amp*(-1)**i_t,0.5,W-0.5)
            if r.random()<pskid:
                L=r.uniform(1,3); j0=int(max(y-L/2,0)/cell); j1=int(min(y+L/2,Lg-1e-6)/cell)+1
                i0=int(max(xc-0.15,0)/cell); i1=int(min(xc+0.15,W-1e-6)/cell)+1
                sl=(slice(j0,j1),slice(i0,i1)); db=r.uniform(0.3,dbmax)
                brk=np.maximum(db-0.5*loose[sl],0); base[sl]+=brk; loose[sl]+=brk*1.15
                push=r.uniform(0.5,2.0); f=r.uniform(0.3,0.7); mv=loose[sl]*f; loose[sl]-=mv
                jt=(np.arange(j0,j1)+int(push/cell))%ny
                # 外側へ半分、下へ半分（こぶの山が溝の外にできる）
                io=np.clip(np.arange(i0,i1)+side*int(0.5/cell),0,nx-1)
                np.add.at(loose,(jt[:,None],np.arange(i0,i1)[None,:]),mv*0.5)
                np.add.at(loose,(np.arange(j0,j1)[:,None],io[None,:]),mv*0.5)
        if (k+1)%(10000//14)==0:
            zone=slice(int((zc-zw/2)/cell),int((zc+zw/2)/cell))
            relief=(loose-base)[:,zone]
            hourly.append((round(8+14*(k+1)/10000),base.max(),np.percentile(base[:,zone],99),np.percentile(base[:,zone],50),relief.max()-relief.min()))
    return hourly,base
if __name__=="__main__":
    sc=[(zw,zf,sev) for zw in [4,8] for zf in [0.6,0.7] for sev in ["通常","厳しい"]]
    jobs=[(s,zw,zf,sev,0.25,None) for (zw,zf,sev) in sc for s in range(12)]
    with Pool(24) as p: res=p.map(day,jobs)
    print("[1日（8〜22時）] 集中ゾーンの下地の削れ（12通りの平均、[ ]は12通りの最大）")
    print(" ゾーン幅/通過率/強さ : 12時の最大 / 17時の最大 / 22時の最大 [最悪] / ゾーン内99%値 / ゾーン内中央 / 22時の凹凸（山の頂〜溝の底）")
    worst=0
    for (zw,zf,sev) in sc:
        R=[res[i][0] for i,j in enumerate(jobs) if j[1:4]==(zw,zf,sev)]
        g=lambda h,ix:np.mean([[x for x in run if x[0]==h][0][ix] for run in R])
        mx=max([[x for x in run if x[0]==22][0][1] for run in R]); worst=max(worst,mx)
        print(f"  {zw}m/{int(zf*100)}%/{sev}: {g(12,1):5.0f} / {g(17,1):5.0f} / {g(22,1):5.0f} [{mx:4.0f}] mm / {g(22,2):4.0f}mm / {g(22,3):4.0f}mm / {g(22,4):4.0f}mm")
    # 収束確認：マス0.125m
    j2=[(s,4,0.7,"厳しい",0.125,None) for s in range(12)]
    with Pool(12) as p: r2=p.map(day,j2)
    print(f"  収束確認（4m/70%/厳しい、マス0.125m）: 22時の最大 平均{np.mean([[x for x in run if x[0]==22][0][1] for run,_ in r2]):.0f}mm [最悪{max([[x for x in run if x[0]==22][0][1] for run,_ in r2]):.0f}]")
    # 複数日：夜の整地で埋め戻せる割合 eff
    print("\n[複数日] 夜の整地で削れの一部しか戻せない場合の累積（4m/70%/厳しい、7日連続）")
    for eff in [1.0,0.9,0.8,0.6]:
        init=None; mxs=[]
        for d in range(7):
            hr,base=day((100+d,4,0.7,"厳しい",0.25,init))
            mxs.append(base.max()); init=base*(1-eff)
        print(f"  埋め戻し{int(eff*100)}%: 各日の終わりの最大削れ "+" ".join(f"{m:.0f}" for m in mxs)+" mm")
    print(f"\n全シナリオ・全乱数での1日の最悪削れ {worst:.0f}mm")
