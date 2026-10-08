from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parent
D=P.parents[1]/'.deps'
if D.is_dir():sys.path.insert(0,str(D))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
font='Meiryo' if any(f.name=='Meiryo' for f in font_manager.fontManager.ttflist) else 'DejaVu Sans'
plt.rcParams.update({'font.family':font,'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'cycle54','axes.unicode_minus':False})
R=json.loads((P/'results.json').read_text(encoding='utf-8'))
def save(fig,stem):
    fig.savefig(P/(stem+'.png'),dpi=160,bbox_inches='tight')
    fig.savefig(P/(stem+'.svg'),bbox_inches='tight',metadata={'Date':None})
    q=P/(stem+'.svg');q.write_text('\n'.join(x.rstrip() for x in q.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    plt.close(fig)
beta=list(range(56));cs=[0 if x==0 else .5-math.sin(2*math.radians(x))/(4*math.radians(x)) for x in beta]
fig,ax=plt.subplots(figsize=(9,4.8));ax.plot(beta,cs,color='#126e82',lw=2.5,label='中心点の簡略解析（一定荷重・摩擦）');ax.plot(beta,[0]*len(beta),'--',color='#bb604a',label='粒の回転を無視した診断')
ax.scatter([30],[.086],s=70,marker='x',color='black',label='S2掲載の中心点 0.086')
ax.set(xlabel='粒自身の連続回転振幅 ±度',ylabel='横方向の摩擦仕事割合 CS',title='直進しても、接触面が回転すると横向き仕事が生じる')
ax.annotate('解析 0.086503\n掲載との差 0.000503',(30,R['central_CS_30']),xytext=(5,.19),arrowprops={'arrowstyle':'->','color':'#444'})
ax.set_ylim(-.01,.28);ax.legend(loc='lower right',fontsize=9);ax.grid(alpha=.18)
fig.text(.1,-.02,'運動の診断。摩耗量・摩擦係数・雪らしさ・成功確率の予測ではない。',fontsize=10)
save(fig,'figure1_rotation')
fig,axs=plt.subplots(1,2,figsize=(10,4.6),gridspec_kw={'width_ratios':[1,1.25]})
# Ideal periodic projection. No specimen image or inferred measured topography.
import numpy as np
x=np.linspace(0,100,200,endpoint=False);xx,yy=np.meshgrid(x,x)
z=np.where((xx%50<5)|(yy%50<5),-1.5,0)
a=axs[0];a.imshow(z,extent=[0,100,0,100],origin='lower',cmap='Blues_r',vmin=-1.5,vmax=0);a.set(xlabel='µm',ylabel='µm',title='計算用の直交開放溝')
a.text(0,-29,'ピッチ50 / 幅5 / 深さ1.5µm\n縁の丸み・実際の加工誤差は未モデル化',fontsize=9)
a=axs[1];loss=[0,.25,.5,1,1.5];sa=[2*.19*.81*max(1.5-h,0) for h in loss];a.plot(loss,sa,'o-',color='#126e82',lw=2)
a.set(xlabel='上面だけの摩耗量 µm（仮定）',ylabel='フィルタなしの面Sa µm',title='微細な形状も消耗する');a.set_ylim(0,.55);a.grid(alpha=.18)
a.annotate('0.5µm摩耗で\nSa 0.3078µm',(.5,.3078),xytext=(.72,.43),arrowprops={'arrowstyle':'->'})
fig.suptitle('浅い凹凸を比較するH54：粗さだけで滑りを保証しない',y=1.02)
fig.text(.08,-.08,'面SaはS1の断面Raと別量。残る溝断面積は排水流量ではない。',fontsize=10)
fig.subplots_adjust(wspace=.4)
save(fig,'figure2_texture')
fig,ax=plt.subplots(figsize=(9,4.7));lives=[x['assumed_life_multiplier'] for x in R['life_sensitivity']];vals=[x['annual_whole_batch_replacement_yen']/1e8 for x in R['life_sensitivity']]
ax.bar([str(x) for x in lives],vals,color=['#ba5747','#d59c60','#428d9f','#9bc6ce']);ax.axhline(R['body_only_material_yen']/1e8,ls='--',c='#555',label='本体のみ・仮寿命1年の材料年額')
for n,v in enumerate(vals):ax.text(n,v+.06,f'{v:.3f}',ha='center')
ax.set(xlabel='機能寿命の仮倍率（計算の感度入力）',ylabel='全量交換の材料年額 億円',title='安価な接触材でも、機能寿命が短いと高くなる')
ax.set_ylim(0,max(vals)*1.15);ax.legend(fontsize=9)
fig.text(.1,-.025,'2,000m²・厚さ0.45m。本体140.025t、仮1,000円/kg。製造・工事・保守等は別。',fontsize=9)
save(fig,'figure3_cost')
print('3 figures written as PNG + SVG')
