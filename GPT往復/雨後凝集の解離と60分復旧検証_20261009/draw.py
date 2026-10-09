from pathlib import Path
import sys
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D.parents[1]/'.deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch
import reproduce as m
plt.rcParams.update({'font.family':'Meiryo','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
R=25e-6
v=np.logspace(-6,-2,120)
fig,axs=plt.subplots(1,3,figsize=(15,4.8),layout='constrained')
for model,label in [('2007','2007 近似'),('2024','2024 近似')]:
    vals=[m.bridge(R,float(x),50,model) for x in v]
    axs[0].semilogx(v,[x['force_contact_uN'] for x in vals],label=label)
    axs[1].loglog(v,[x['rupture_work_nJ'] for x in vals],label=label)
axs[0].set(xlabel='水橋体積 / 接点半径³',ylabel='接触時の力 [µN]',title='排水しても引離し力は残る')
axs[1].set(xlabel='水橋体積 / 接点半径³',ylabel='引離し仕事 [nJ]',title='体積が減ると仕事は小さくなる')
f=np.linspace(20,100,100);G=25
ref=m.bridge(R,1e-3);W=ref['rupture_work_nJ']*1e-9
for alpha in [.1,.5,1]:
    vr=alpha*G*9.81/(2*np.pi*f)
    axs[2].semilogy(f,m.P['particle_mass_kg']*vr**2/4/W,label=f'相対速度係数 α={alpha}')
axs[2].axhline(1,color='#a44',ls='--',lw=1)
axs[2].set(xlabel='振動数 [Hz]（駆動加速度は25gで共通）',ylabel='粒対の運動エネルギー / 1水橋の仕事',title='同じ加速度でも仕事の余裕は変わる')
for ax in axs:ax.grid(alpha=.2);ax.legend(fontsize=9)
fig.suptitle('50℃・同一球状接点の選別計算｜凝集解離の実験・振動装置の合否ではない',fontsize=13)
fig.savefig(D/'figure1_force_work.png',dpi=160);plt.close(fig)
fig=plt.figure(figsize=(14,7),layout='constrained');gs=fig.add_gridspec(2,2,height_ratios=[1.1,1])
ax=fig.add_subplot(gs[0,:]);ax.set(xlim=(0,10),ylim=(0,3));ax.axis('off')
items=[(.1,'① 水を逃がす','開いた排水路・回収\n水橋の残量は別途測定'),
       (2.65,'② 局所的にほぐす','粒の相対運動をつくる\n骨格へ荷重・枝損傷を測定'),
       (5.2,'③ 凝集・異物を判定','泥・破片は回収側へ\n同じ水をそのまま戻さない'),
       (7.75,'④ 再配置・圧密','滑走・支持・排水を確認\n水橋の再形成も再検査')]
for x,t,b in items:
    ax.add_patch(FancyBboxPatch((x,.8),2.1,1.65,boxstyle='round,pad=.12',fc='#e7f0f5',ec='#23536b'))
    ax.text(x+1.05,2.07,t,ha='center',va='center',weight='bold')
    ax.text(x+1.05,1.38,b,ha='center',va='center',fontsize=10)
    if x<7:ax.annotate('',(x+2.47,1.6),(x+2.2,1.6),arrowprops={'arrowstyle':'->','lw':1.7})
ax.text(5,.3,'H76-D 工程候補：各工程の時間・損傷・再凝集は未測定。密閉箱や固定滑走マットを作る案ではない。',ha='center',fontsize=11)
a=fig.add_subplot(gs[1,0])
for area,c in [(2000,'#1b7f8c'),(20000,'#b15d39')]:
    x=np.array([.01,.1,1]);q=area*.45*x/2280*3600
    a.loglog(x*100,q,'o-',label=f'{area:,} m²',color=c)
a.set(xlabel='処理する面積割合 [%]（深さ450 mm）',ylabel='機内へ取り込む場合の量 [m³/h]',title='処理枠38分：全面処理も比較する');a.legend();a.grid(alpha=.2)
b=fig.add_subplot(gs[1,1])
loss=np.logspace(-5,-2,100)
for area,c in [(2000,'#1b7f8c'),(20000,'#b15d39')]:
    yen=area*.45*120*200*loss*500/1e4
    b.loglog(loss*100,yen,label=f'{area:,} m²',color=c)
b.axvline(.01,ls='--',color='#777');b.text(.011,1.2e4,'100 ppm/回\n年2%補充の目標線',fontsize=9)
b.set(xlabel='全床処理1回の材料損失 [%]',ylabel='年200回の補充原料費 [万円/年]',title='500円/kgの仮単価。加工・回収・設備費は別');b.legend();b.grid(alpha=.2)
fig.suptitle('復旧工程・処理量・維持費をつなぐ｜機械の能力保証・実見積りではない',fontsize=14)
fig.savefig(D/'figure2_process_cost.png',dpi=160)
