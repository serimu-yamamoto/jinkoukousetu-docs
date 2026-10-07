import os,sys,json
from pathlib import Path
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D.parents[1]/'.deps'));sys.dont_write_bytecode=True
os.environ['MPLCONFIGDIR']=str(D.parents[1]/'.scratch'/'mpl')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
R=json.loads((D/'results.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.family':['Meiryo','Yu Gothic','sans-serif'],'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(2,2,figsize=(16,11));fig.subplots_adjust(top=.88,hspace=.4,wspace=.6,bottom=.14)
fig.suptitle('曲がるクリップ：着脱の非線形計算と、保持力・材料量の限界\n対称な薄い部材と剛体円の比較模型。50℃実物・粒床・雪感の予測ではない。',fontsize=18)
colors={0:'#315970',.1:'#42a18a',.2:'#bd5b4c',.4:'#888888'}
for c in R['reference_curves']:
    if c['mu']==.1:continue
    a=c['assembly'];d=c['disassembly'];start=a[0]['y0'];color=colors[c['mu']]
    label='μ='+str(c['mu'])+('（干渉あり・除外）' if not c['valid_two_contact_branch'] else '')
    ax[0,0].plot([(start-r['y0'])*50 for r in a],[r['F']*.125 for r in a],color=color,label=label)
    ax[0,0].plot([(start-r['y0'])*50 for r in d],[r['F']*.125 for r in d],color=color,ls='--')
ax[0,0].axhline(0,color='#aaaaaa',lw=.8);ax[0,0].set(title='A　押込みと引抜き側のすべり限界',xlabel='中央の押込み量（µm）',ylabel='押込み向きを正とした力（mN）');ax[0,0].legend(fontsize=9);ax[0,0].text(.02,.03,'実線：挿入側　破線：引抜き側\n静止からすべる遷移・動的跳躍は未計算',transform=ax[0,0].transAxes,fontsize=9)
c=R['refined_reference'];alpha=c['alpha'];axs=ax[0,1];axs.add_patch(Circle((0,0),alpha,facecolor='#dae2e6',edgecolor='#9baab0',lw=1))
for i,sh in enumerate(c['shapes']):
    x=np.array(sh['x']);y=np.array(sh['y']);xs=np.r_[-x[::-1],x];ys=np.r_[y[::-1],y];axs.plot(xs,ys,label=['自由形','途中1','途中2','着座直前'][i],lw=2)
axs.set_aspect('equal');axs.set(title='B　部材の中心線（α=1.14, φ=2.1, μ=0.2）',xlabel='x / Rₛ',ylabel='y / Rₛ');axs.legend(fontsize=9,loc='lower left');axs.set_ylim(-1.3,2.7)
axs=ax[1,0];values={'snap':0,'stick':1,'eject':2,'inadmissible_or_incomplete':3};cl=['#389680','#d6a649','#a8bdca','#a7595a'];rows=R['grid_summaries']
for j,pair in enumerate([(a,p) for a in [1.05,1.14,1.3] for p in [1.9,2.1,2.3]]):
 for i,mu in enumerate([0,.1,.2,.4]):
    z=next(r for r in rows if r['alpha']==pair[0] and r['phi_rad']==pair[1] and r['mu']==mu);v=values[z['regime']];axs.scatter(i,j,c=cl[v],s=300,marker='s');axs.text(i,j,['S','H','E','×'][v],ha='center',va='center',color='white',fontweight='bold')
axs.set_xticks(range(4),['0','0.1','0.2','0.4']);axs.set_yticks(range(9),[str(a)+' / '+str(p) for a in [1.05,1.14,1.3] for p in [1.9,2.1,2.3]]);axs.set(xlabel='仮の粒間摩擦 μ（実測ではない）',ylabel='半径比α / 半角φ（rad）',title='C　二点接触模型の領域（格子割合は成功率ではない）');axs.text(.0,-.28,'S：引き込む　H：摩擦で保持　E：押し返す\n×：接触等の条件を外れる。材料失敗の断定ではない。',transform=axs.transAxes,fontsize=9)
axs=ax[1,1];C=R['contact_budget'];vals=[C['force_required_for_illustrative_10kPa_N']*1000,R['dimensional_examples'][2]['sliding_limit_pull_peak_N']*1000,C['optimistic_parallel_clip_force_N']*1000]
axs.barh([2,1,0],vals,color=['#315970','#ba6556','#65a193']);axs.set_xscale('log');axs.set_yticks([2,1,0],['仮の10kPa用\n接点力','クリップ1個','余剰材料を\n全て並列化']);axs.set(xlabel='力（mN、対数目盛）',title='D　薄い部材だけに保持を任せる案は不足');axs.set_xlim(.005,20)
for y,v in zip([2,1,0],vals):axs.text(v*1.1,y,f'{v:.3g}',va='center')
axs.text(0,-.26,'Rₛ=50µm, b=100µm, t=5µm, 仮E=300MPa\n10kPaは比較尺度。雪の合否基準・実床強度ではない。',transform=axs.transAxes,fontsize=9)
for aa in [ax[0,0],ax[0,1],ax[1,1]]:aa.grid(alpha=.15)
fig.savefig(D/'曲線接点の応答と限界.png',dpi=160)

# Render the saved STL itself, not an independently regenerated proxy.
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
verts=[]
for line in (D/'曲線接点_100倍形状確認用.stl').read_text(encoding='ascii').splitlines():
 if line.strip().startswith('vertex '):verts.append([float(q) for q in line.split()[1:]])
tri=np.array(verts).reshape(-1,3,3)
fig2=plt.figure(figsize=(10,7));aa=fig2.add_subplot(111,projection='3d')
mesh=Poly3DCollection(tri,facecolor='#72aebc',edgecolor='none',alpha=1)
aa.add_collection3d(mesh);aa.set_xlim(-6,6);aa.set_ylim(-4,6);aa.set_zlim(-6,6);aa.set_box_aspect((12,10,12));aa.view_init(elev=25,azim=-65)
aa.set(xlabel='x（mm）',ylabel='y（mm）',zlabel='幅方向（mm）')
fig2.suptitle('100倍の自由形状・確認用STL\n中心線半径5mm、厚さ0.5mm、幅10mm、全角240.6°',fontsize=17)
fig2.text(.5,.04,'接点部品の形状資料。相手部品・全粒・安全性・製造精度は未検証。',ha='center',fontsize=11)
fig2.savefig(D/'拡大自由形状.png',dpi=150)
