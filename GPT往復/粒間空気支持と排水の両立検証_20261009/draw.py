from pathlib import Path
import sys,csv,json,math
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D.parents[1]/'.deps'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle, FancyArrowPatch
font=Path('C:/Windows/Fonts/meiryo.ttc')
if font.exists():plt.rcParams['font.family']=FontProperties(fname=str(font)).get_name()
plt.rcParams.update({'font.size':11,'axes.unicode_minus':False})
def read(n):return list(csv.DictReader((D/n).open(encoding='utf-8')))
v=read('velocity.csv');f=read('fusion_requirements.csv')
fig,axs=plt.subplots(1,2,figsize=(14,5.6))
for width,name,col in [('0.1','スキー2本：幅100 mm','#007a87'),('0.25','ボード1枚：幅250 mm','#a55229')]:
    r=[x for x in v if x['width']==width];xs=[float(x['V']) for x in r];ys=[float(x['mu_diagnostic']) for x in r]
    axs[0].plot(xs,ys,'-',color=col,label=name)
    for x,y,rr in zip(xs,ys,r):
        axs[0].plot(x,y,'o',color=col,markerfacecolor=col if rr['within_small_strain_and_pressure_screen']=='True' else 'white',markersize=7)
axs[0].axhline(.04,c='gray',ls='--',label='仮の比較線 0.04')
axs[0].set(xlabel='速度 [m/s]',ylabel='抵抗係数の診断値（実測ではない）',ylim=(0,.12),title='A. 空気の効果は速度・幅に依存')
axs[0].text(.02,.96,'中抜き点：小変形・小圧力の確認範囲外\nEd=20 kPa、k=3×10⁻¹² m²、乾燥',transform=axs[0].transAxes,va='top',fontsize=10)
axs[0].legend(loc='lower left',fontsize=9)
for ee,col in [('20000.0','#999999'),('25000.0','#b05d18'),('40000.0','#007a87')]:
    r=[x for x in f if x['Ed']==ee and x['rain_mm_h']=='100.0']
    r+= [x for x in f if x['Ed']==ee and x['rain_mm_h']=='200.0' and x['permeability_retention']=='0.5']
    xs=[float(x['clean_saturated_drain_mm_h']) for x in r];ys=[float(x['mu_solid_required_for_diagnostic_004']) for x in r]
    axs[1].plot(xs,ys,'-',color=col,label='Ed='+str(int(float(ee)/1000))+' kPa')
    for x,y,rr in zip(xs,ys,r):
        axs[1].plot(x,y,'o',color=col,markerfacecolor=col if rr['within_small_strain_and_pressure_screen']=='True' else 'white',markersize=7)
axs[1].set(xlabel='清浄時の飽和排水容量 [mm/h]',ylabel='診断値0.04に必要な接触面の μ 上限',title='B. 排水余裕を増すと低摩擦面の要求が厳しくなる',ylim=(.025,.09))
axs[1].text(.02,.96,'10 m/s、幅100 mm、横漏れあり\n同一 k を乾燥空気と水に仮定',transform=axs[1].transAxes,va='top',fontsize=10)
axs[1].legend(loc='lower left',fontsize=9)
for ax in axs:ax.grid(alpha=.22)
fig.suptitle('第74巡｜側壁のない粒床：仮定したモデルの計算',fontsize=16)
fig.text(.5,.02,'空気支持率・計算点の合格割合は成功確率ではない。濡れた滑走、エッジ、実材料の性能は未検証。',ha='center',fontsize=10)
fig.tight_layout(rect=(0,.06,1,.93));fig.savefig(D/'figure1_tradeoff.png',dpi=160);plt.close(fig)

fig,axs=plt.subplots(1,2,figsize=(14,6.4),gridspec_kw={'width_ratios':[1.22,1]})
ax=axs[0];ax.set_xlim(0,10);ax.set_ylim(0,10);ax.axis('off')
ax.text(.2,9.65,'H74-P：自由な開放粒に機能を分担',fontsize=14,weight='bold')
ax.add_patch(Rectangle((1.6,8.25),6.6,.35,color='#444b55'));ax.text(4.9,8.75,'板／実ソール　→ 滑走',ha='center')
for row,y in enumerate([7.2,5.4,3.6,1.8]):
    for j,x in enumerate([2,4.5,7]):
        x+=.32*(row%2)
        for t in np.arange(6)*math.pi/3+.15*(j+row):
            dx,dy=.68*math.cos(t),.68*math.sin(t)
            ax.plot([x,x+dx],[y,y+dy],c='#348272',lw=2.5)
            for q in[-1,1]:
                ux,uy=.28*math.cos(t+q*1.05),.28*math.sin(t+q*1.05)
                bx,by=x+.60*dx,y+.60*dy
                ax.plot([bx,bx+ux],[by,by+uy],c='#76a197',lw=1.5)
            ax.plot(x+dx,y+dy,'o',c='#8f4c9b',ms=3)
ax.annotate('',(.5,6.4),(2,6.4),arrowprops=dict(arrowstyle='->',color='#257aac',lw=2))
ax.annotate('',(9.3,6.4),(7.8,6.4),arrowprops=dict(arrowstyle='->',color='#257aac',lw=2))
ax.text(.25,5.3,'横へ\n空気が\n漏れる',fontsize=10,color='#257aac')
ax.annotate('',(8.5,.65),(8.5,5),arrowprops=dict(arrowstyle='->',color='#257aac',lw=2))
ax.text(8.6,2.1,'下へ\n排水',fontsize=10,color='#257aac')
ax.plot([1.2,8.1],[.65,.65],c='#888',lw=3)
ax.text(4.65,.15,'保持・排水下地は最大削れ深さ＋余裕の下',ha='center',fontsize=9)
ax.text(1.5,9.2,'緑：骨格・二次枝　紫：低摩擦候補の接点',fontsize=10)
ax.text(1.55,4.48,'450 mm 全深度に同じ機能を持つ粒',fontsize=10,bbox=dict(facecolor='white',alpha=.85,edgecolor='none'))
ax.text(1.55,2.66,'300 mm 削れ後も固定マットを露出させない',fontsize=10,bbox=dict(facecolor='white',alpha=.85,edgecolor='none'))
ax.text(1.4,.97,'模式図：形状・間隔・縮尺は未確定',fontsize=9,color='#555')
ax=axs[1]
cost=read('raw_cost.csv')
xs=np.arange(3);a=[float(x['raw_only_JPY_ex_tax'])/1e6 for x in cost if x['hypothetical_resin_JPY_per_kg']=='500.0'];b=[float(x['raw_only_JPY_ex_tax'])/1e6 for x in cost if x['hypothetical_resin_JPY_per_kg']=='2000.0']
ax.bar(xs-.16,a,width=.3,color='#91b6a8',label='仮原料単価 500円/kg')
ax.bar(xs+.16,b,width=.3,color='#426d80',label='仮原料単価 2,000円/kg')
ax.set_xticks(xs,['2%：2.16 t','5%：5.4 t','10%：10.8 t'])
ax.set(ylabel='追加原料費のみ [百万円・税別]',title='全床108 tへ二次枝材料を追加した場合',ylim=(0,34),xlabel='追加量／既存床質量（歩留まり80%を仮定）')
for i,(aa,bb) in enumerate(zip(a,b)):
    ax.text(i-.16,aa+.5,f'{aa:g}',ha='center',fontsize=10);ax.text(i+.16,bb+.5,f'{bb:g}',ha='center',fontsize=10)
ax.legend(loc='upper left',fontsize=10);ax.grid(axis='y',alpha=.2)
fig.suptitle('構造案と経済条件｜材料も加工も未見積り・未試作',fontsize=16)
fig.text(.5,.02,'固定繊維シートは採用しない。微細枝の脱落・濡れ固着・加工費・寿命費は未確定。設備2億円とは別枠。',ha='center',fontsize=10)
fig.tight_layout(rect=(0,.06,1,.94));fig.savefig(D/'figure2_design_cost.png',dpi=160);plt.close(fig)
print('Saved 2 concept/numerical figures.')
