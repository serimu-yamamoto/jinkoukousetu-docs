# VT7 滑走で緩んだ後の状態（斜面セル・オートマトン）と雨の日
import numpy as np
from multiprocessing import Pool
W,Lg=40.,50.
def day(args):
    seed,cell,phir=args
    r=np.random.default_rng(seed)
    nx,ny=int(W/cell),int(Lg/cell)
    loose=np.zeros((ny,nx))      # 緩んだ粒の厚さ mm（y=0が上端）
    broken=np.zeros((ny,nx))     # 下地から削れた累計 mm
    out_bottom=0.
    runs=3000
    for k in range(runs):
        x=r.uniform(2,W-2); y=0.
        amp=r.uniform(1,6); wl=r.uniform(6,14); ph=r.uniform(0,2*np.pi)
        pskid=r.uniform(0.3,0.8)
        while y<Lg-1:
            y+=wl/2
            if y>=Lg: break
            xc=np.clip(x+amp*np.sin(2*np.pi*y/wl+ph),0.5,W-0.5)
            if r.random()<pskid:
                L=r.uniform(1,3); wd=0.3
                j0=int(max(y-L/2,0)/cell); j1=int(min(y+L/2,Lg-1e-6)/cell)+1
                i0=int(max(xc-wd/2,0)/cell); i1=int(min(xc+wd/2,W-1e-6)/cell)+1
                db=r.uniform(0.3,1.5)
                sl=(slice(j0,j1),slice(i0,i1))
                brk=np.maximum(db-0.5*loose[sl],0)      # 緩んだ層が厚いほど下地は削れにくい
                broken[sl]+=brk; loose[sl]+=brk*1.15     # かさ増し（締まった→緩い）
                push=r.uniform(0.5,2.0); f=r.uniform(0.3,0.7)
                moved=loose[sl]*f; loose[sl]-=moved
                dj=int(push/cell); jt0=j0+dj; jt1=j1+dj
                if jt1<=ny: loose[jt0:jt1,i0:i1]+=moved
                else:
                    keep=max(ny-jt0,0)
                    if keep>0: loose[jt0:ny,i0:i1]+=moved[:keep]
                    out_bottom+=moved[keep:].sum()
                # 横に飛ばす分（ターン外側へ1マス）
                side=1 if r.random()<0.5 else -1
                ii0=min(max(i0+side,0),nx-1); ii1=min(max(i1+side,1),nx)
                spill=loose[sl][:, :ii1-ii0]*0.1; loose[j0:j1,ii0:ii1]+=spill; loose[sl][:, :ii1-ii0]-=spill
        # 安息角より急なら、緩んだ粒は少しずつずり落ちる（滑走の振動が引き金）
        if phir<30 and k%10==0:
            rate=0.02*(np.tan(np.radians(30))-np.tan(np.radians(phir)))/np.tan(np.radians(30))*10
            mv=loose*rate; loose-=mv; out_bottom+=mv[-1].sum(); loose[1:]+=mv[:-1]
    a=cell*cell; rho_loose=1674/1.15/1000  # t/m3
    return dict(
        bare=np.mean(loose<0.5), l2=np.mean(loose>=2), l5=np.mean(loose>=5), l20=np.mean(loose>=20),
        p95=np.percentile(loose,95), pmax=loose.max(), mean=loose.mean(),
        vol_t=loose.sum()*a/1000*rho_loose, bottom_t=(loose[int(45/cell):].sum()*a/1000+out_bottom*a/1000)*rho_loose,
        brk_mean=broken.mean(), brk_max=broken.max())
if __name__=="__main__":
    jobs=[(s,c,p) for p in [33,28] for c in [0.5,0.25] for s in range(12)]
    with Pool(24) as pool: res=pool.map(day,jobs)
    print("[A] 1日（3,000本）滑走後 17時の状態  ※12通りの乱数の平均±幅、セル0.5m/0.25mで比較（収束確認）")
    for p in [33,28]:
        for c in [0.5,0.25]:
            R=[res[i] for i,(s,cc,pp) in enumerate(jobs) if pp==p and cc==c]
            m=lambda k:(np.mean([x[k] for x in R]),np.std([x[k] for x in R]))
            print(f" 安息角{p}°{'(斜面30°より急に止まれる)' if p>30 else '(斜面30°より緩い→ずり落ちる)'} セル{c}m:")
            print(f"   下地がむき出し(緩み<0.5mm) {m('bare')[0]*100:4.1f}%  緩み2mm以上 {m('l2')[0]*100:4.1f}%  5mm以上 {m('l5')[0]*100:4.1f}%  20mm以上 {m('l20')[0]*100:4.1f}%")
            print(f"   緩み厚 平均{m('mean')[0]:.2f}mm 95%値{m('p95')[0]:.1f}mm 最大{m('pmax')[0]:.0f}mm | 緩んだ粒の総量{m('vol_t')[0]:.2f}t、下端5mと場外に集まった量{m('bottom_t')[0]:.2f}t | 下地の削れ 平均{m('brk_mean')[0]:.2f}mm 最大{m('brk_max')[0]:.1f}mm")

    print("\n[B] 雨")
    Ks=[3e-4,1e-3,3e-3]
    for k in Ks: print(f"  床の透水係数{k:.0e}m/s ＝ 浸み込める雨 {k*3.6e6:.0f}mm/h → 豪雨100mm/hでも表面を流れない")
    for rain in [10,30,50,100]:
        q=rain/1000/3600*50
        for Kd,td in [(0.01,0.1),(0.1,0.2)]:
            cap=Kd*0.5*td+1e-3*0.5*0.45
            print(f"  雨{rain:>3}mm/h：斜面50mの浸透流 {q*1000:.2f}L/s/m vs 排水能力（砕石K{Kd}・厚{td}m＋床）{cap*1000:.1f}L/s/m → {'余裕' if cap>q*1.5 else '不足（下部から水が湧き出す）'}")
    th_s,th_r,lam=0.382,0.02,2.0; m_=3+2/lam
    for z,lab in [(0.005,'表層5mm'),(0.05,'深さ5cm'),(0.45,'床の底0.45m')]:
        for Ksv in [3e-4,1e-3]:
            Se=(0.06-th_r)/(th_s-th_r); t=z*(th_s-th_r)/(Ksv*m_*Se**(m_-1))
            print(f"  雨がやんでから{lab}が含水6%（ほぼ通常）に戻るまで：透水{Ksv:.0e}で {t/60:.0f}分")
    print("  方解石の橋が雨で溶ける量：雨30mm×2,000m²＝60m³ × 最大約50mg/L ≈ 3kg（毎晩の析出17kgの2割弱、1日分の雨で表層の締まりの1〜2割が失われる上限）")
    print("  酸性雨pH4.5でも H⁺≈1.9mol → CaCO3 約0.1kg（無視できる）")
