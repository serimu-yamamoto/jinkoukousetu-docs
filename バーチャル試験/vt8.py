# VT8 1kmコース・14時間・1万本：昼の整地の有無、必要な厚さ、層構成
import numpy as np
from multiprocessing import Pool
W,Lg,cell=40.,50.,0.25
def day(args):
    seed,midday=args
    r=np.random.default_rng(seed)
    nx,ny=int(W/cell),int(Lg/cell)
    loose=np.zeros((ny,nx)); broken=np.zeros((ny,nx)); flux=0.
    runs=10000; snaps=[]
    for k in range(runs):
        hour=8+14*k/runs
        if midday and abs(hour-12.0)<14/runs/2*1.0001 and not any(s[0]=='groom' for s in snaps):
            # 昼の整地（石灰水なし）：5m四方で粒をならし、削れた穴を埋め、山を崩す
            b=int(5/cell)
            for j in range(0,ny,b):
                for i in range(0,nx,b):
                    loose[j:j+b,i:i+b]=loose[j:j+b,i:i+b].mean()
            snaps.append(('groom',hour))
        x=r.uniform(2,W-2); y=r.uniform(-14,0)
        amp=r.uniform(1,6); wl=r.uniform(6,14); ph=r.uniform(0,2*np.pi); pskid=r.uniform(0.3,0.8)
        while True:
            y+=wl/2
            if y>=Lg: break
            if y<0: continue
            xc=np.clip(x+amp*np.sin(2*np.pi*y/wl+ph),0.5,W-0.5)
            if r.random()<pskid:
                L=r.uniform(1,3); j0=int(max(y-L/2,0)/cell); j1=int(min(y+L/2,Lg-1e-6)/cell)+1
                i0=int(max(xc-0.15,0)/cell); i1=int(min(xc+0.15,W-1e-6)/cell)+1
                sl=(slice(j0,j1),slice(i0,i1)); db=r.uniform(0.3,1.5)
                brk=np.maximum(db-0.5*loose[sl],0); broken[sl]+=brk; loose[sl]+=brk*1.15
                push=r.uniform(0.5,2.0); f=r.uniform(0.3,0.7); moved=loose[sl]*f; loose[sl]-=moved
                dj=int(push/cell); jt=(np.arange(j0,j1)+dj)
                wrap=jt>=ny; flux+=moved[wrap].sum(); jt=jt%ny    # 周期境界（コース中間区間）
                np.add.at(loose,(jt[:,None],np.arange(i0,i1)[None,:]),moved)
        if (k+1)%(runs//14)==0:
            snaps.append(('h',round(hour),np.mean(loose<0.5),loose.mean(),np.percentile(loose,95),loose.max(),np.percentile(broken,99.9),broken.max()))
    return snaps,flux*cell*cell/1000*1674/1.15/1000/W   # t/日/m幅 の下向き輸送
if __name__=="__main__":
    jobs=[(s,m) for m in [False,True] for s in range(12)]
    with Pool(24) as p: res=p.map(day,jobs)
    for m in [False,True]:
        R=[res[i] for i,(s,mm) in enumerate(jobs) if mm==m]
        print(f"\n[{'昼12時に整地(ならしのみ)あり' if m else '整地なし'}] 時刻: 下地むき出し / 緩み平均 / 95%値 / 最大の山 / 削れ深さ99.9%値 / 最大  （12通り平均）")
        H=[[s for s in run if s[0]=='h'] for run,_ in R]
        for t in range(len(H[0])):
            v=np.mean([[h[t][2],h[t][3],h[t][4],h[t][5],h[t][6],h[t][7]] for h in H],axis=0)
            print(f"  {H[0][t][1]:>2}時: {v[0]*100:4.1f}% / {v[1]:5.1f}mm / {v[2]:5.1f}mm / {v[3]:5.0f}mm / {v[4]:5.0f}mm / {v[5]:4.0f}mm")
        fl=np.mean([f for _,f in R])
        print(f"  コース全体の下向き輸送 ≈ {fl:.3f} t/日/m幅 → 40m幅で{fl*40:.1f}t/日が下へ移る（夜に上へ戻す量）")
    print("\n[必要な厚さ]（床材の総量は1km×40m＝4万m²、乾燥かさ密度1,674kg/m³）")
    for th in [0.3,0.45,0.6,1.0,1.5]:
        t=40000*th*1674/1000
        print(f"  厚さ{th:.2f}m: {t:8.0f}t  （仮定単価3〜15円/kgで{t*1000*3/1e8:5.1f}〜{t*1000*15/1e8:5.1f}億円）")
    print("\n[層の構成の判定]")
    d15,d85=0.6,1.4   # 床材(mm)
    print(f"  フィルター条件（Terzaghi）：下の層のD15は {4*d15:.1f}mm以上（排水）かつ {5*d85:.1f}mm以下（粒が落ち込まない）")
    print("  → 1mm粒の直下に20〜40mmの砕石を置くと、粒が隙間に落ち込む。間に5〜7mm程度の細かい層（D15≈3〜7mm）が要る")
    for nm,phi in [("丸い玉砂利",33),("角ばった砕石（細）",42),("角ばった砕石（粗）",45)]:
        fsd=np.tan(np.radians(phi))/np.tan(np.radians(30)); fss=fsd*(1-9.81/20.5)
        print(f"  {nm} φ{phi}°：30°斜面での層の安全率 乾燥{fsd:.2f}／層内が水で満ちた場合{fss:.2f} → {'不可（滑り面になる）' if fss<1.0 or fsd<1.3 else '可'}")
