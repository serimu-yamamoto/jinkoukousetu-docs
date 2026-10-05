# 人工フィルン HBG-5 バーチャル試験 第1弾（独立再計算＋感度解析）
import numpy as np
rng=np.random.default_rng(20261005); N=10_000_000
g=9.81; rho_s=2710.; rho_d=1674.; phi_por=1-rho_d/rho_s
gd=rho_d*g/1e3; gsat=(rho_d+phi_por*1000)*g/1e3; gw=9.81
print(f"porosity={phi_por:.3f} gamma_d={gd:.2f} gamma_sat={gsat:.2f} kN/m3")

# --- VT1 非結合方解石粒床の剛性（Hertz-Mindlin有効媒質, Mavko式）
G=32e9; nu=0.32
def hm(P,C,slip=1.0):
    K=(C**2*(1-phi_por)**2*G**2*P/(18*np.pi**2*(1-nu)**2))**(1/3)
    Gh=(5-4*nu)/(5*(2-nu))*(3*C**2*(1-phi_por)**2*G**2*P/(2*np.pi**2*(1-nu)**2))**(1/3)
    Gh=Gh*slip  # slip=0で摩擦なし接点(Walton smooth相当の下限側)
    E=9*K*Gh/(3*K+Gh); return E
print("\n[VT1] 非結合床のヤング率E(MPa) vs 平均応力P")
for P in [0.1e3,1e3,10e3,100e3,300e3]:
    lo=hm(P,6,0.3)/1e6; hi=hm(P,9,1.0)/1e6
    print(f"  P={P/1e3:7.1f}kPa  E={lo:8.1f}〜{hi:8.1f} MPa")
print("  表層1cm自重のP≈%.2fkPa" % (gd*0.01))

# --- VT2 エッジ支持（帯状基礎の支持力, Vesic係数）
def bc_N(phi):
    t=np.tan(phi); Nq=np.exp(np.pi*t)*np.tan(np.pi/4+phi/2)**2
    return (Nq-1)/t, Nq, 2*(Nq+1)*t
print("\n[VT2] エッジ支持に必要な粘着力c (kPa)：エッジ幅b=5〜20mm, 圧100〜300kPa")
for ph in [30,35,40]:
    Nc,Nq,Ng=bc_N(np.radians(ph))
    for q in [100,300]:
        for b in [0.005,0.02]:
            c=(q-0.5*gd*b*Ng)/Nc
            print(f"  phi={ph} q={q} b={b*1e3:.0f}mm -> c_req={max(c,0):.2f}")

# --- VT3 30度斜面 安全率 モンテカルロ
beta=np.radians(30)
phi=np.radians(rng.uniform(30,42,N))      # 丸粒は角ばった砂より低めを含める
z=rng.uniform(0.02,0.45,N)                 # すべり面深さ
m=rng.uniform(0,1,N)                       # 浸潤率 0=乾燥 1=飽和平行浸透
c=np.exp(rng.uniform(np.log(0.1),np.log(400),N))  # 濡れ時の接点結合c: 未測定→対数一様0.1〜400kPa
gam=np.where(m>0, gd+(gsat-gd)*m, gd)
FS=(c+(gam-m*gw)*z*np.cos(beta)**2*np.tan(phi))/(gam*z*np.sin(beta)*np.cos(beta))
print("\n[VT3] 斜面 P(FS>=1.5)")
for lo,hi in [(0.1,1),(1,3),(3,10),(10,40),(40,400)]:
    s=(c>=lo)&(c<hi); print(f"  c {lo:>5}〜{hi:<4}kPa: 全条件 {np.mean(FS[s]>=1.5):.3f} / 飽和(m>0.9) {np.mean(FS[s&(m>0.9)]>=1.5):.3f}")
# 必要c（最悪: 飽和, z=0.45）
for ph in [30,35,40]:
    t=np.tan(np.radians(ph)); cr=1.5*gsat*0.45*np.sin(beta)*np.cos(beta)-(gsat-gw)*0.45*np.cos(beta)**2*t
    print(f"  飽和・z0.45m・phi{ph}: c_req={cr:.2f}kPa")

# 感度（順位相関）
from scipy.stats import spearmanr
idx=rng.choice(N,200000,replace=False)
for name,v in [("phi",phi),("z",z),("m",m),("log c",np.log(c))]:
    print(f"  Spearman(FS,{name})={spearmanr(v[idx],FS[idx])[0]:+.3f}")

# --- VT4 夏の湿潤表面 熱収支（定常, ペンマン型）
n=2_000_000
S=rng.uniform(600,1000,n); alb=rng.uniform(0.25,0.55,n)  # 湿った方解石は暗くなる
Ta=30.; RH=rng.uniform(0.4,0.8,n); U=rng.uniform(0.5,4,n)
sig=5.67e-8; eps=0.95; Ld=eps*sig*(Ta+273.15)**4*rng.uniform(0.80,0.95,n)
h=5.7+3.8*U; L=2.45e6; cp=1005.; rhoa=1.16
def esat(T): return 0.6108*np.exp(17.27*T/(T+237.3))  # kPa
def resid(T,wet):
    LE=wet*h/cp*L*0.622/101.3*(esat(T)-RH*esat(Ta)) if True else 0
    return S*(1-alb)+Ld-eps*sig*(T+273.15)**4-h*(T-Ta)-LE
for wet,lab in [(1.0,"完全湿潤"),(0.0,"乾燥")]:
    lo=np.full(n,0.);hi=np.full(n,90.)
    for _ in range(60):
        mid=(lo+hi)/2; r=resid(mid,wet); lo=np.where(r>0,mid,lo); hi=np.where(r>0,hi,mid)
    T=(lo+hi)/2
    print(f"\n[VT4] {lab}: 表面温度 中央{np.median(T):.1f}℃ 5%{np.percentile(T,5):.1f} 95%{np.percentile(T,95):.1f}")
    if wet:
        E=h/cp*0.622/101.3*(esat(T)-RH*esat(Ta))  # kg/m2/s
        day=E*3600*8*2000/1000  # t/日 (8h,2000m2)
        print(f"  蒸発 {np.median(E*3600):.2f}kg/m2/h → 2,000m2・8h で中央{np.median(day):.0f}t/日 (5%{np.percentile(day,5):.0f}〜95%{np.percentile(day,95):.0f})")
        Tw=T  # 表面を30℃以下にできる割合
        print(f"  湿潤でも30℃以下になる割合 {np.mean(T<=30):.3f}")

# --- VT5 経済 Pmax モンテカルロ
n=5_000_000
vis=rng.uniform(50,150,n); price=rng.uniform(3000,4000,n); days=100
B=(price-1000)*vis*days-6e6
I=rng.uniform(1.5e7,3.0e7,n); O=rng.uniform(2e6,6e6,n); lam=rng.uniform(0.05,0.3,n)
Af=6.710081; M=1_506_600
P=((B-O)*Af-I)/(M*(1+lam*Af))
cost=rng.uniform(5,27.6,n)
print(f"\n[VT5] Pmax 中央{np.median(P):.1f}円/kg 5%{np.percentile(P,5):.1f} 95%{np.percentile(P,95):.1f}; P(Pmax>材料費)={np.mean(P>cost):.3f}; P(Pmax<0)={np.mean(P<0):.3f}")
for name,v in [("客数",vis),("料金",price),("O",O),("I",I),("λ",lam),("材料費",cost)]:
    print(f"  Spearman(Pmax-cost,{name})={spearmanr(v[:200000],(P-cost)[:200000])[0]:+.3f}")
