# VT11 カービングの深い溝＋滑走集中ゾーン＋4〜5時間ごとの保守
import numpy as np
from multiprocessing import Pool
Wd,Lg,cell=12.,50.,0.05      # 集中ゾーンを中心に幅12mを細かく計算
Nc=46.1
def carve_depth(r,c):
    F=800*r.uniform(1,4); L=r.uniform(1.0,1.4); th=np.radians(r.uniform(45,70)); i=r.uniform(0.1,1.0)
    q=c*1e3*Nc*i; B=F/(q*L); return B*np.sin(th)*1000, B   # 溝の深さmm, 接触幅m
def day(args):
    seed,zw,zf,sev,interval,eff,ndays=args
    r=np.random.default_rng(seed)
    nx,ny=int(Wd/cell),int(Lg/cell); zc=Wd/2
    base=np.zeros((ny,nx)); loose=np.zeros((ny,nx))
    turn_y=np.arange(3,Lg,r.uniform(7,10))
    dbmax,pmax=(1.5,0.8) if sev=="通常" else (3.0,0.95)
    period_max=[]; carve_d=[]
    hours_op=14; runs=10000
    bounds=list(np.arange(interval,hours_op,interval)) if interval else []
    for d in range(ndays):
        nextm=0
        for k in range(runs):
            h=hours_op*k/runs
            if nextm<len(bounds) and h>=bounds[nextm]:
                period_max.append(base.max()); base*=(1-eff); loose[:]=0; nextm+=1
            inz=r.random()<zf
            if not inz and r.random()>Wd/40: continue   # ゾーン外の人は幅40m中12mの範囲に来る確率で
            c=np.exp(r.uniform(np.log(3),np.log(30)))
            adv=r.random()<r.uniform(0.3,0.5)
            if inz: x=zc+r.uniform(-zw/2,zw/2)*0.6; amp=r.uniform(0.3,1.0)*zw/2; ys=turn_y+r.normal(0,0.7,len(turn_y))
            else: x=r.uniform(0,Wd); amp=r.uniform(1,6); ys=np.arange(r.uniform(0,7),Lg,r.uniform(3,7))
            side=1 if r.random()<0.5 else -1
            for i_t,y in enumerate(ys):
                if y<0 or y>=Lg: continue
                xc=x+side*amp*(-1)**i_t
                if xc<0 or xc>=Wd: continue
                if adv:   # カービング：細く長い溝
                    dd,B=carve_depth(r,c); carve_d.append(dd)
                    L=r.uniform(3,6); wdt=max(B,0.03)
                    db=dd; push_f=0.8
                elif r.random()<r.uniform(0.3,pmax):
                    L=r.uniform(1,3); wdt=0.3; db=r.uniform(0.3,dbmax); push_f=r.uniform(0.3,0.7)
                else: continue
                j0=int(max(y-L/2,0)/cell); j1=int(min(y+L/2,Lg-1e-6)/cell)+1
                i0=int(max(xc-wdt/2,0)/cell); i1=int(min(xc+wdt/2,Wd-1e-6)/cell)+1
                sl=(slice(j0,j1),slice(i0,i1))
                brk=np.maximum(db-0.5*loose[sl],0); base[sl]+=brk; loose[sl]+=brk*1.15
                mv=loose[sl]*push_f; loose[sl]-=mv
                io=np.clip(np.arange(i0,i1)+side*max(int(0.3/cell),1),0,nx-1)
                np.add.at(loose,(np.arange(j0,j1)[:,None],io[None,:]),mv)   # 溝の外へ押し出す
        period_max.append(base.max()); base*=(1-eff); loose[:]=0
    return period_max,np.array(carve_d)
if __name__=="__main__":
    sc=[(4,0.7,"厳しい")]
    iv=[(None,"保守なし(14時間)"),(5,"5時間ごと"),(4,"4時間ごと")]
    jobs=[(s,zw,zf,sev,i,0.8,3) for (zw,zf,sev) in sc for (i,_) in iv for s in range(12)]
    with Pool(24) as p: res=p.map(day,jobs)
    cd=np.concatenate([c for _,c in res])
    print(f"[カービング1回の溝の深さ] 中央{np.median(cd):.1f}mm 95%{np.percentile(cd,95):.1f}mm 99.9%{np.percentile(cd,99.9):.1f}mm 最大{cd.max():.0f}mm（粘着力10〜100kPa、荷重1〜3倍、エッジ角45〜70°）")
    print("\n[保守の間隔ごとの、集中ゾーンの最大の削れ]（埋め戻し80%で3日連続。12通りの平均と[最悪]）")
    for (zw,zf,sev) in sc:
        for (i,lab) in iv:
            R=[res[k][0] for k,j in enumerate(jobs) if j[1:5]==(zw,zf,sev,i)]
            per=np.array([max(pm) for pm in R])
            print(f"  {zw}m/{int(zf*100)}%/{sev}＋カービング {lab:<12}: 1区間の最大 平均{per.mean():4.0f}mm [最悪{per.max():4.0f}mm] → 必要な厚さ ≈ {(per.max()+150)/1000:.2f}m（底付き0.15mを加算）")
