# VT13-② 雨の浸透と回復：1次元Richards式を線の方法＋BDF（剛性ODE）で解く
import numpy as np, itertools, collections, time
from scipy.integrate import solve_ivp
from scipy.sparse import diags
from multiprocessing import Pool
ts,tr=0.38,0.02
def mk(a,n,Ks):
    m=1-1/n
    def Se(h): return np.where(h<0,(1+(a*np.abs(h))**n)**(-m),1.0)
    def th(h): return tr+(ts-tr)*Se(h)
    def K(h): s=Se(h); return Ks*np.sqrt(s)*(1-(1-s**(1/m))**m)**2
    def C(h):
        ha=np.abs(np.minimum(h,0)); return np.where(h<0,(ts-tr)*a*m*n*(a*ha)**(n-1)*(1+(a*ha)**n)**(-m-1),0)+1e-4
    return th,K,C
def sim(P):
    a,n,Ks,rain,dur,qcap,E,dz=P
    th,K,C=mk(a,n,Ks); N=int(round(0.45/dz)); ntop=max(1,int(round(0.005/dz)))
    qc=None if qcap is None else qcap/1000/3600
    def F(fin):
        def f(t,h):
            Kc=K(h); q=np.empty(N+1)
            q[1:N]=-0.5*(Kc[:-1]+Kc[1:])*((h[1:]-h[:-1])/dz+1)
            q[0]=-(Kc[0] if qc is None else min(Kc[0],qc))
            if fin>0: q[N]=-min(fin,max(Kc[-1]*((0-h[-1])/(dz/2)+1),0))
            else: q[N]=min(-fin,max(Kc[-1]*((h[-1]+50)/(dz/2)-1),0))
            return (q[:-1]-q[1:])/dz/C(h)
        return f
    sp=diags([1,1,1],[-1,0,1],shape=(N,N))
    run=lambda fin,T,h,te=None: solve_ivp(F(fin),(0,T),h,method='BDF',jac_sparsity=sp,rtol=1e-5,atol=1e-7,t_eval=te)
    top=lambda y:np.array([th(y[-ntop:,k]).mean() for k in range(y.shape[1])])
    h=run(-0.3/1000/3600,6*3600,np.full(N,-0.4)).y[:,-1]
    s=run(rain/1000/3600,dur*3600,h,np.linspace(0,dur*3600,int(dur*60)+1)); tp=top(s.y)
    o={'max':tp.max(),'slush_h':np.sum((tp-tr)/(ts-tr)>=0.85)/60}
    s=run(-E/1000/3600,72*3600,s.y[:,-1],np.linspace(0,72*3600,72*30+1)); tp=top(s.y)
    o['slush_h']+=np.sum((tp-tr)/(ts-tr)>=0.85)*2/60; o['max']=max(o['max'],tp.max())
    for key,lim in [('t10',0.10),('t06',0.06)]:
        i=np.where(tp<=lim)[0]; o[key]=None if len(i)==0 else s.t[i[0]]/3600
    return o
def job(args):
    seed,rain,dur,qcap,E,dz=args; r=np.random.default_rng(seed)
    P=(r.uniform(3,8),r.uniform(3,7),np.exp(r.uniform(np.log(5e-4),np.log(2e-3))),rain,dur,qcap,E,dz)
    try: return (rain,dur,qcap,E,sim(P))
    except Exception: return (rain,dur,qcap,E,None)
if __name__=='__main__':
    for dz in [0.00125,0.000625,0.0003125]:
        t0=time.time(); o=sim((5,5,1e-3,50,3,0,0.6,dz))
        print(f'格子確認 dz={dz*1000}mm 雨50mm/h×3h・排水なし・晴れ: 表層最大{o["max"]*100:.1f}% 春雪{o["slush_h"]:.1f}h 10%回復{o["t10"]} 6%回復{o["t06"]} ({time.time()-t0:.0f}s)',flush=True)
    rains=[2,5,10,20,30,50,80,100]; durs=[1,3,6,12]; qcaps=[None,10,0]; Es=[0.6,0.1]
    jobs=[(s*7919+int(rn*13+du*7+(0 if q is None else q+1)*3+E*10),rn,du,q,E,0.00125) for rn,du,q,E in itertools.product(rains,durs,qcaps,Es) for s in range(8)]
    with Pool(24) as p: res=p.map(job,jobs)
    G=collections.defaultdict(list); fail=sum(1 for *_,rc in res if rc is None)
    for rn,du,q,E,rc in res:
        if rc: G[(rn,du,q,E)].append(rc)
    print(f'計算 {len(res)}件（失敗{fail}件）')
    med=lambda L:(None if sum(v is None for v in L)>len(L)/2 else np.median([v for v in L if v is not None]))
    fmt=lambda v:'72h超' if v is None else f'{v:.1f}h'
    for q,lab in [(None,'排水良好'),(10,'排水が詰まりかけ（底から10mm/hまで）'),(0,'排水不良（底から抜けない）')]:
        print(f'\n[{lab}] 継続時間ごとに「表層含水の最大／春雪状態の時間／10%以下へ戻る時間 晴れ・曇り／6%以下 晴れ」')
        for rn in rains:
            row=[]
            for du in durs:
                S=G[(rn,du,q,0.6)]; Cc=G[(rn,du,q,0.1)]
                if not S: row.append(f'{du}h:失敗'); continue
                row.append(f'{du}h:{np.median([x["max"] for x in S])*100:4.1f}%/{np.median([x["slush_h"] for x in S]):4.1f}h/{fmt(med([x["t10"] for x in S]))}・{fmt(med([x["t10"] for x in Cc]))}/{fmt(med([x["t06"] for x in S]))}')
            print(f'  {rn:>3}mm/h '+' | '.join(row),flush=True)
