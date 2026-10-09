from pathlib import Path
import sys,csv,json,math
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D.parents[1]/'.deps'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle,Circle,FancyArrowPatch
font=Path('C:/Windows/Fonts/meiryo.ttc')
if font.exists():plt.rcParams['font.family']=FontProperties(fname=str(font)).get_name()
plt.rcParams.update({'font.size':11,'axes.unicode_minus':False})
from reproduce import capillary
def rd(n):return list(csv.DictReader((D/n).open(encoding='utf-8')))
s=rd('snow_source_subset.csv');h=rd('interparticle_bridge.csv')
fig,axs=plt.subplots(1,3,figsize=(17,5.8))
xs=np.arange(6)
axs[0].bar(xs,[float(r['mean_k_m2']) for r in s],color='#367b82')
axs[0].axhline(3e-12,c='#a54e37',ls='--',label='第74巡の仮定 3×10⁻¹²')
axs[0].set_yscale('log');axs[0].set_ylim(1e-12,2e-8)
axs[0].set_xticks(xs,[r['sample']+'\n'+r['type'] for r in s])
axs[0].set(ylabel='平均の固有透過率 [m²]',title='A. 雪試料の構造と仮定値の差')
axs[0].text(.03,.96,'Calonne 2012 補足表2の6試料\n三次元画像からの計算値',transform=axs[0].transAxes,va='top',fontsize=10)
axs[0].legend(loc='lower right',fontsize=9)
ll=np.linspace(20,220,300)
for e,t,g,m,col,label in [(1e9,10e-6,40e-6,1,'#367b82','名目：E=1 GPa、t=10、g=40 µm'),(.2e9,8e-6,30e-6,2,'#a54e37','厳しい仮定：E=0.2 GPa、t=8、g=30、圧力2倍')]:
    lam=[capillary(e,t,l*1e-6,g,gamma=.072*m)['Lambda'] for l in ll]
    axs[1].plot(ll,lam,c=col,label=label)
axs[1].axhline(.25,c='black',ls='--',label='一様圧力近似の境界')
axs[1].axvline(50,c='#777',ls=':')
axs[1].set_yscale('log');axs[1].set(xlabel='支えのない長さ ℓ [µm]',ylabel='毛管力と曲げ剛性の比 Λ',title='B. 長さを半分にすると Λ は1/16',ylim=(1e-4,20))
axs[1].legend(loc='lower right',fontsize=8)
for k,col in [(.2,'#999999'),(1.6,'#367b82'),(10.,'#a54e37')]:
    r=[q for q in h if abs(float(q['root_k_N_m'])-k)<1e-9]
    axs[2].plot([float(q['fraction_of_100um_square'])*100 for q in r],[float(q['Lambda']) for q in r],'o-',c=col,label=f'根元 k={k:g} N/m')
axs[2].axhline(.25,c='black',ls='--')
axs[2].set_xscale('log');axs[2].set_yscale('log')
axs[2].set(xlabel='水を挟んで向き合う面積 [%]',ylabel='粒間の毛管力と根元剛性の比',title='C. 粒内が丈夫でも、粒同士は寄り合う')
axs[2].legend(fontsize=9,loc='upper left')
for ax in axs:ax.grid(alpha=.2)
fig.suptitle('第75巡｜原著との比較と、濡れ固着の反例',fontsize=16)
fig.text(.5,.018,'B・Cは仮定した理想形状の選別計算。境界を下回ることは、実物・寿命・雨後復旧の合格ではない。',ha='center',fontsize=10)
fig.tight_layout(rect=(0,.05,1,.94));fig.savefig(D/'figure1_evidence_and_limits.png',dpi=160);plt.close(fig)

fig,axs=plt.subplots(1,2,figsize=(14,7),gridspec_kw={'width_ratios':[1.2,1]})
ax=axs[0];ax.set_xlim(0,10);ax.set_ylim(0,11);ax.axis('off')
ax.text(.2,10.4,'H75-R：粒の中の短い支え＋柔らかな根元',fontsize=13,weight='bold')
# Free particle skeleton and two flexible arms; no common fixed mat.
for cx,cy in [(2.8,2.7),(7.3,2.4)]:
    for th in [0,2.1,4.2]:
        ax.plot([cx,cx+1.1*math.cos(th)],[cy,cy+.75*math.sin(th)],color='#377e72',lw=4)
    tt=np.linspace(0,1,80)
    x=cx+.18*np.sin(tt*3*np.pi);y=cy+.2+tt*1.4
    ax.plot(x,y,c='#377e72',lw=3)
    ax.add_patch(Circle((cx,y[-1]+.28),.38,facecolor='#a9c8c0',edgecolor='#377e72',lw=2))
    ax.plot(cx-.12,y[-1]+.61,'o',c='#8d5f9e',ms=8)
ax.text(.4,1.1,'粗い骨格：深く切れる・動く・再整地する機能',fontsize=10)
ax.text(.4,.45,'独立した自由粒。図の二粒を連続シートで結ばない。',fontsize=10)
ax.text(.3,5.25,'丸く不連続な接点で、粒間の広い対向面を減らす',fontsize=10)
# magnification box, short lamella segments. Not a fabrication drawing.
ax.add_patch(Rectangle((.5,6.15),8.9,3.4,fill=False,edgecolor='#777',ls='--'))
ax.text(.7,9.15,'局所拡大：内部の支え。溝は側方にも開口させる',fontsize=10)
for y in [6.8,7.7]:
    ax.add_patch(Rectangle((1.05,y),7.2,.16,facecolor='#a9c8c0',edgecolor='#377e72'))
for x in [1.05,3.2,5.35,7.5]:
    ax.add_patch(Rectangle((x,6.8),.18,1.05,facecolor='#377e72'))
ax.annotate('',(3.2,8.45),(1.23,8.45),arrowprops=dict(arrowstyle='<->'))
ax.text(2.2,8.55,'ℓの目安 50 µm',ha='center',fontsize=10)
ax.annotate('',(8.7,7.7),(8.7,6.96),arrowprops=dict(arrowstyle='<->'))
ax.text(8.55,7.23,'g',fontsize=11,ha='right')
ax.text(1.0,6.3,'t≈10 µm、g≈40 µm：材料係数・形状は仮定',fontsize=9)
ax.annotate('',(4.2,6.12),(3.0,4.75),arrowprops=dict(arrowstyle='->',color='#777'))
ax.text(.5,5.7,'局所の支持と、粒全体の変形を分ける',fontsize=10,color='#377e72')
ax=axs[1];c=rd('rib_cost.csv');pitches=[50,100,200];xx=np.arange(3)
low=[];high=[]
for p in pitches:
    rr=[r for r in c if abs(float(r['pitch_um'])-p)<1e-6 and abs(float(r['rib_height_um'])-40)<1e-6]
    low.append(min(float(r['raw_only_JPY_ex_tax']) for r in rr)/1e6)
    high.append(max(float(r['raw_only_JPY_ex_tax']) for r in rr)/1e6)
ax.bar(xx-.16,low,.3,color='#91b6a8',label='仮単価500円/kg')
ax.bar(xx+.16,high,.3,color='#3b7280',label='仮単価2,000円/kg')
for i,(a,b) in enumerate(zip(low,high)):
    ax.text(i-.16,a+.25,f'{a:.2f}',ha='center',fontsize=10)
    ax.text(i+.16,b+.25,f'{b:.2f}',ha='center',fontsize=10)
ax.set_xticks(xx,[str(p)+' µm' for p in pitches]);ax.set(ylim=(0,19),ylabel='補強原料だけの追加費 [百万円・税別]',xlabel='直交する補強リブのピッチ',title='局所を細かく支えるための追加費')
ax.text(.02,.96,'全機能面 約33万m²、リブ幅10 µm\n高さ40 µm、密度1,200 kg/m³\n歩留まり80％。いずれも仮定。',transform=ax.transAxes,va='top',fontsize=10)
ax.legend(loc='upper right',bbox_to_anchor=(1,.79),fontsize=9);ax.grid(axis='y',alpha=.2)
fig.suptitle('設計案と費用｜濡れた粒群・雪の滑走感は未実証',fontsize=16)
fig.text(.5,.02,'図は縮尺不同。50 µmピッチの原料費約357〜1,428万円。成形・根元・接点・検査・維持費、設備2億円は別。',ha='center',fontsize=10)
fig.tight_layout(rect=(0,.06,1,.94));fig.savefig(D/'figure2_structure_cost.png',dpi=160);plt.close(fig)
print('Saved 2 figures.')
