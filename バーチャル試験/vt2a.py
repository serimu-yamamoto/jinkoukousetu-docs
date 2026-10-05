# VT2-A 混合床（硬い方解石粒＋柔らかいゲル粒）の有効剛性：三角格子ばね網の数値実験
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spl
from multiprocessing import Pool
L=48
def build(L):
    xs=[];ys=[]
    for j in range(L):
        for i in range(L):
            xs.append(i+0.5*(j%2)); ys.append(j*np.sqrt(3)/2)
    X=np.c_[xs,ys]; idx=lambda i,j:j*L+i; B=[]
    for j in range(L):
        for i in range(L):
            if i+1<L: B.append((idx(i,j),idx(i+1,j)))
            if j+1<L:
                if j%2==0:
                    B.append((idx(i,j),idx(i,j+1)))
                    if i-1>=0: B.append((idx(i,j),idx(i-1,j+1)))
                else:
                    B.append((idx(i,j),idx(i,j+1)))
                    if i+1<L: B.append((idx(i,j),idx(i+1,j+1)))
    return X,np.array(B)
X,Bd=build(L); n=len(X)
d=X[Bd[:,1]]-X[Bd[:,0]]; d/=np.linalg.norm(d,axis=1)[:,None]
bot=np.where(X[:,1]<1e-9)[0]; top=np.where(X[:,1]>X[:,1].max()-1e-9)[0]
H=X[:,1].max()
def Eeff(args):
    f,ratio,seed=args
    r=np.random.default_rng(seed)
    soft=r.random(n)<f; ks=np.where(soft,1.0/ratio,1.0)
    k=2*ks[Bd[:,0]]*ks[Bd[:,1]]/(ks[Bd[:,0]]+ks[Bd[:,1]])
    rows=[];cols=[];vals=[]
    for a in range(2):
        for b in range(2):
            v=k*d[:,a]*d[:,b]
            for (p,q,s) in [(0,0,1),(1,1,1),(0,1,-1),(1,0,-1)]:
                rows.append(2*Bd[:,p]+a); cols.append(2*Bd[:,q]+b); vals.append(s*v)
    K=sp.csr_matrix((np.concatenate(vals),(np.concatenate(rows),np.concatenate(cols))),shape=(2*n,2*n))
    u=np.zeros(2*n); fixed=np.zeros(2*n,bool)
    fixed[2*bot+1]=True; fixed[2*top+1]=True; u[2*top+1]=-0.01*H
    fixed[2*bot[0]]=True  # 剛体並進を止める
    fr=~fixed
    rhs=-K[fr][:,fixed]@u[fixed]
    Kf=K[fr][:,fr]+sp.identity(fr.sum())*1e-12
    u[fr]=spl.spsolve(Kf.tocsc(),rhs)
    F=(K@u)[2*top+1].sum()
    return f,ratio,-F
if __name__=="__main__":
    fs=np.round(np.arange(0,1.0001,0.05),2); ratios=[1e2,1e3,1e4]; R=24
    jobs=[(f,ra,1000*i+int(f*100)+int(np.log10(ra))*7) for f in fs for ra in ratios for i in range(R)]
    with Pool(24) as p: res=p.map(Eeff,jobs)
    res=np.array(res); E0=res[(res[:,0]==0)][:,2].mean()
    print("f_soft  " + "  ".join(f"ratio{int(r):>6}" for r in ratios)+"   (E/E_calcite, 平均±標準偏差, 実現24回)")
    for f in fs:
        line=f"{f:5.2f}  "
        for ra in ratios:
            v=res[(res[:,0]==f)&(res[:,1]==ra)][:,2]/E0
            line+=f"  {v.mean():.2e}±{v.std()/max(v.mean(),1e-30)*100:4.0f}%"
        print(line)
    np.save("vt2a.npy",res)
