# VT13-① 含水率100段階×荷重×速度の摩擦（仮想試験）。未測定の物性は範囲で振る
import numpy as np
from multiprocessing import Pool
th_s=0.38; th_r=0.02
def run(args):
    th,N,seed=args
    r=np.random.default_rng(seed)
    m=r.uniform(40,110,N); dyn=r.uniform(1,2.5,N); W=m*9.81*dyn/2      # 片足の荷重N
    v=r.uniform(2,10,N); Lc=r.uniform(1.0,1.4,N); w=0.07; A=Lc*w; p=W/A
    d=r.uniform(0.3e-3,0.6e-3,N); sig=r.uniform(0.05,0.3,N)*d             # 粒頂の高さのばらつき
    th_fc=r.uniform(0.06,0.12,N)                                          # 圃場容水量（0.3〜0.6mm砂）
    S=6*(1-th_s)/d                                                        # 粒の比表面積 m2/m3
    h_av=np.minimum(th,th_fc)/S + np.maximum(th-th_fc,0)/(th_s-th_fc)*d*0.5   # 接点に使える水膜の厚さ
    eta=r.uniform(0.7e-3,1.0e-3,N)
    h_hd=r.uniform(0.1,1.0,N)*np.sqrt(eta*v*Lc/p)                         # 流体潤滑で保てる膜厚
    h=np.minimum(h_hd,h_av); alpha=1-np.exp(-(h/sig)**1.5)                # 水膜が受け持つ荷重の割合
    mu_dry=np.exp(r.normal(np.log(0.16),0.3,N))                           # VT4の乾燥摩擦（中央0.16）
    beta=r.uniform(0.3,0.8,N); thw=r.uniform(0.005,0.03,N)
    mu_b=mu_dry*(1-beta*(1-np.exp(-th/thw)))                              # 水による境界潤滑
    hv=np.maximum(h,1e-7); mu_v=eta*v/hv*alpha*A/W                        # 水膜のせん断抵抗
    Sr=(th-th_r)/(th_s-th_r); Sr=np.clip(Sr,0,1)
    nb=np.clip((Sr-0.1)/0.6,0,1)/d**2; Fcap=nb*A*2*np.pi*0.2*d*0.072*r.uniform(0.4,0.9,N)
    t_loose=r.uniform(0,6e-3,N); Scrit=r.uniform(0.7,0.9,N)
    s=t_loose*np.clip((Sr-Scrit)/(1-Scrit),0,1)                           # 水で支えを失った緩い層への沈み
    mu_p=0.5*r.uniform(1800,2100,N)*v**2*w*s*r.uniform(1,2,N)/W           # ぬかるみの掘り起こし抵抗
    mu=(1-alpha)*mu_b*(W+Fcap)/W + mu_v + mu_p
    return th,np.percentile(mu,[5,50,95]),np.mean(mu<=0.10),np.percentile(s*1000,[50,95]),np.median(alpha),np.median(mu_v),np.median(mu_p)
if __name__=='__main__':
    levels=np.linspace(0,th_s,100)
    print('収束確認（含水率4つの代表値で、試行回数を増やす）')
    for th in [0.0,0.03,0.10,0.35]:
        out=[]
        for N in [10**4,10**5,10**6]:
            _,pc,pok,_,_,_,_=run((th,N,1)); out.append(f'N={N:>8,}: 中央{pc[1]:.4f} 95%{pc[2]:.4f} P(μ≦0.10)={pok:.3f}')
        print(f'  含水{th*100:4.1f}%: '+' | '.join(out))
    with Pool(24) as pool: res=pool.map(run,[(th,10**6,int(th*1e4)+7) for th in levels])
    print('\n含水率(体積%) | 飽和度 | μ 5%/中央/95% | P(μ≦0.10) | 沈み 中央/95%(mm) | 水膜の荷重割合 | 粘性分 | ぬかるみ分')
    for i,(th,pc,pok,sk,al,mv,mp) in enumerate(res):
        if i%3==0 or i in (99,):
            print(f'  {th*100:5.1f}% | {(th-th_r)/(th_s-th_r)*100 if th>th_r else 0:5.0f}% | {pc[0]:.3f}/{pc[1]:.3f}/{pc[2]:.3f} | {pok:.2f} | {sk[0]:.2f}/{sk[1]:.2f} | {al:.2f} | {mv:.4f} | {mp:.4f}')
    best=min(res,key=lambda x:x[1][1])
    ok=[x[0] for x in res if x[2]>=0.5]
    print(f'\n中央値で最も滑る含水率：{best[0]*100:.1f}%（μ中央{best[1][1]:.3f}）。P(μ≦0.10)≧0.5の範囲：'+(f'{min(ok)*100:.1f}〜{max(ok)*100:.1f}%' if ok else 'なし'))
    np.save('vt13_mu.npy',np.array([[x[0],*x[1],x[2],*x[3]] for x in res]))
